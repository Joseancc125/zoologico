from fastapi import FastAPI, Request, BackgroundTasks
import asyncio
import aiohttp
import os
import sqlite3
import json
import uuid
import base64
from typing import Optional

app = FastAPI(title="Orchestrator")
MCP_URL = os.environ.get('MCP_URL', 'http://mcp:9000/publish')
CLOUD_URL = os.environ.get('CLOUD_URL', 'http://cloud_processor:5000/ingest')

# In-memory registry (simple) de cámaras
CAMERAS = {}
# In-memory recent alerts (simple PoC, not persistent)
ALERTS = []
ALERTS_MAX = int(os.environ.get('ALERTS_MAX', '200'))

# Persistence paths
DATA_DIR = os.environ.get('DATA_DIR', './data')
DB_PATH = os.path.join(DATA_DIR, 'alerts.db')
UPLOADS_DIR = os.environ.get('UPLOADS_DIR', './uploads')


def ensure_storage():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    # init sqlite
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id TEXT PRIMARY KEY,
        camera_id TEXT,
        received_at REAL,
        metadata TEXT,
        thumbnail_path TEXT
    )
    ''')
    conn.commit()
    conn.close()


def save_alert_to_db(payload: dict, thumbnail_path: Optional[str] = None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        aid = payload.get('id') or str(uuid.uuid4())
        cam = payload.get('camera_id')
        rcv = payload.get('received_at')
        meta = json.dumps(payload)
        cur.execute('INSERT OR REPLACE INTO alerts (id, camera_id, received_at, metadata, thumbnail_path) VALUES (?,?,?,?,?)',
                    (aid, cam, rcv, meta, thumbnail_path))
        conn.commit()
        conn.close()
        return aid
    except Exception:
        return None


def save_thumbnail_from_b64(b64str: str) -> Optional[str]:
    try:
        data = base64.b64decode(b64str)
        fname = f"{uuid.uuid4().hex}.jpg"
        path = os.path.join(UPLOADS_DIR, fname)
        with open(path, 'wb') as f:
            f.write(data)
        # return path relative to web root
        return f"/uploads/{fname}"
    except Exception:
        return None


@app.get('/health')
async def health():
    return {"status":"ok"}


@app.post('/register_camera')
async def register_camera(request: Request):
    body = await request.json()
    cam_id = body.get('camera_id')
    meta = body.get('meta', {})
    if not cam_id:
        return {"error":"camera_id required"}
    CAMERAS[cam_id] = {"meta": meta, "registered_at": asyncio.get_event_loop().time()}
    return {"status":"registered", "camera_id": cam_id}


@app.post('/alert')
async def alert(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    # Enriquecer con metadatos
    body['received_at'] = asyncio.get_event_loop().time()

    # Guardar alerta en memoria (últimas ALERTS_MAX)
    try:
        ALERTS.append(body)
        if len(ALERTS) > ALERTS_MAX:
            del ALERTS[0:len(ALERTS)-ALERTS_MAX]
    except Exception:
        pass

    # Persistir: si viene thumbnail/frame en base64, guardarlo
    thumbnail_path = None
    if isinstance(body.get('thumbnail_b64'), str):
        thumbnail_path = save_thumbnail_from_b64(body.get('thumbnail_b64'))
        if thumbnail_path:
            body['thumbnail_url'] = thumbnail_path
    elif isinstance(body.get('frame_b64'), str):
        thumbnail_path = save_thumbnail_from_b64(body.get('frame_b64'))
        if thumbnail_path:
            body['thumbnail_url'] = thumbnail_path

    # guardar en sqlite en background
    try:
        background_tasks.add_task(save_alert_to_db, body, thumbnail_path)
    except Exception:
        pass

    # Publicar en MCP
    background_tasks.add_task(_publish_to_mcp, body)
    # Reenviar a procesador en la nube (no bloqueante)
    background_tasks.add_task(_forward_to_cloud, body)

    return {"status": "ok"}


@app.post('/mcp_callback')
async def mcp_callback(request: Request):
    # MCP reenviará eventos aquí
    body = await request.json()
    # Por ahora solo loguear y reenviar a nube si necesario
    asyncio.create_task(_forward_to_cloud(body))
    # también guardamos el evento recibido desde MCP
    try:
        ALERTS.append(body)
        if len(ALERTS) > ALERTS_MAX:
            del ALERTS[0:len(ALERTS)-ALERTS_MAX]
    except Exception:
        pass
    return {"status":"received"}


@app.get('/alerts')
async def list_alerts(limit: int = 50):
    # devuelve las últimas `limit` alertas (más recientes últimas)
    try:
        return {'count': len(ALERTS), 'alerts': ALERTS[-limit:][::-1]}
    except Exception:
        return {'count': 0, 'alerts': []}


@app.get('/alerts/history')
async def alerts_history(page: int = 1, per_page: int = 20, q: Optional[str] = None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # count
        if q:
            like = f"%{q}%"
            cur.execute('SELECT COUNT(*) FROM alerts WHERE metadata LIKE ?', (like,))
        else:
            cur.execute('SELECT COUNT(*) FROM alerts')
        total = cur.fetchone()[0]
        offset = (page - 1) * per_page
        if q:
            cur.execute('SELECT id, camera_id, received_at, metadata, thumbnail_path FROM alerts WHERE metadata LIKE ? ORDER BY received_at DESC LIMIT ? OFFSET ?', (like, per_page, offset))
        else:
            cur.execute('SELECT id, camera_id, received_at, metadata, thumbnail_path FROM alerts ORDER BY received_at DESC LIMIT ? OFFSET ?', (per_page, offset))
        rows = cur.fetchall()
        results = []
        for rid, cam, rcv, meta, thumb in rows:
            try:
                metaobj = json.loads(meta) if meta else {}
            except Exception:
                metaobj = {}
            # ensure id/camera/received_at present
            metaobj.setdefault('id', rid)
            if cam:
                metaobj.setdefault('camera_id', cam)
            metaobj.setdefault('received_at', rcv)
            if thumb:
                metaobj.setdefault('thumbnail_url', thumb)
            results.append(metaobj)
        conn.close()
        return {'total': total, 'page': page, 'per_page': per_page, 'results': results}
    except Exception:
        return {'total': 0, 'page': page, 'per_page': per_page, 'results': []}


@app.post('/maintenance/purge')
async def maintenance_purge(request: Request):
    body = await request.json()
    retention_days = int(body.get('retention_days', 30))
    dry_run = bool(body.get('dry_run', True))
    cutoff = asyncio.get_event_loop().time() - (retention_days * 24 * 3600)
    deleted = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT id, thumbnail_path, received_at FROM alerts WHERE received_at < ?', (cutoff,))
        rows = cur.fetchall()
        to_delete_ids = [r[0] for r in rows]
        to_delete_files = [r[1] for r in rows if r[1]]
        if not dry_run:
            # delete files
            for p in to_delete_files:
                try:
                    # stored path like /uploads/<name>
                    fname = p.split('/')[-1]
                    fpath = os.path.join(UPLOADS_DIR, fname)
                    if os.path.exists(fpath):
                        os.remove(fpath)
                except Exception:
                    pass
            # delete db records
            cur.executemany('DELETE FROM alerts WHERE id = ?', [(i,) for i in to_delete_ids])
            conn.commit()
        conn.close()
        return {'dry_run': dry_run, 'matched': len(to_delete_ids), 'deleted': (0 if dry_run else len(to_delete_ids)), 'files': to_delete_files}
    except Exception as e:
        return {'error': str(e)}


@app.post('/maintenance/compact')
async def maintenance_compact():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('VACUUM')
        conn.close()
        return {'status': 'ok'}
    except Exception as e:
        return {'error': str(e)}


async def _publish_to_mcp(payload):
    async with aiohttp.ClientSession() as s:
        try:
            await s.post(MCP_URL, json=payload, timeout=3)
        except Exception:
            pass


async def _forward_to_cloud(payload):
    async with aiohttp.ClientSession() as s:
        try:
            await s.post(CLOUD_URL, json=payload, timeout=5)
        except Exception:
            pass


@app.on_event('startup')
async def startup_subscribe():
    ensure_storage()
    # Intentar suscribir al MCP para recibir publicaciones
    callback = os.environ.get('ORCHESTRATOR_CALLBACK', 'http://orchestrator:8000/mcp_callback')
    async with aiohttp.ClientSession() as s:
        try:
            await s.post('http://mcp:9000/subscribe', json={'callback_url': callback}, timeout=3)
        except Exception:
            pass
