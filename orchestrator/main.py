from fastapi import FastAPI, Request, BackgroundTasks
import asyncio
import aiohttp
import os

app = FastAPI(title="Orchestrator")
MCP_URL = os.environ.get('MCP_URL', 'http://mcp:9000/publish')
CLOUD_URL = os.environ.get('CLOUD_URL', 'http://cloud_processor:5000/ingest')

# In-memory registry (simple) de cámaras
CAMERAS = {}


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
    return {"status":"received"}


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
    # Intentar suscribir al MCP para recibir publicaciones
    callback = os.environ.get('ORCHESTRATOR_CALLBACK', 'http://orchestrator:8000/mcp_callback')
    async with aiohttp.ClientSession() as s:
        try:
            await s.post('http://mcp:9000/subscribe', json={'callback_url': callback}, timeout=3)
        except Exception:
            pass
