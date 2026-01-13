from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
import os


app = FastAPI(title="Zoologico Dashboard")

app.mount('/static', StaticFiles(directory='dashboard/static'), name='static')
app.mount('/uploads', StaticFiles(directory='uploads'), name='uploads')

ORCHESTRATOR_URL = os.environ.get('ORCHESTRATOR_URL', 'http://orchestrator:8000')


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    with open('dashboard/static/index.html', 'r') as f:
        return HTMLResponse(f.read())


@app.get('/visual', response_class=HTMLResponse)
async def visual(request: Request):
    with open('dashboard/static/visual.html', 'r') as f:
        return HTMLResponse(f.read())


@app.get('/visual/frames')
async def visual_frames(camera_id: str = None, hours: int = 24, limit: int = 200):
    """Proxy endpoint to fetch recent frames/alerts for visualization.
    Optional filter by `camera_id` and `hours` (lookback in hours).
    Returns JSON with `results` array like orchestrator `/alerts/history` but filtered.
    """
    import time
    cutoff = None
    try:
        now = time.time()
        cutoff = now - (int(hours) * 3600)
    except Exception:
        cutoff = None

    async with aiohttp.ClientSession() as s:
        try:
            url = f"{ORCHESTRATOR_URL}/alerts/history?page=1&per_page={limit}"
            async with s.get(url, timeout=5) as r:
                data = await r.json()
                results = data.get('results', []) if isinstance(data, dict) else []
                filtered = []
                for it in results:
                    try:
                        rcv = float(it.get('received_at') or 0)
                    except Exception:
                        rcv = 0
                    # some services may store monotonic timestamps (small values).
                    # if rcv looks like a monotonic timestamp (less than 1e6), skip cutoff filtering.
                    is_monotonic_like = (rcv > 0 and rcv < 1e6)
                    if cutoff and (not is_monotonic_like) and rcv < cutoff:
                        continue
                    if camera_id and str(it.get('camera_id')) != str(camera_id):
                        continue
                    filtered.append(it)
                return JSONResponse({'total': len(filtered), 'results': filtered})
        except Exception as e:
            return JSONResponse({'total': 0, 'results': [], 'error': str(e)})


@app.get('/alerts')
async def alerts(limit: int = 50):
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(f"{ORCHESTRATOR_URL}/alerts?limit={limit}", timeout=5) as r:
                data = await r.json()
                return JSONResponse(data)
        except Exception as e:
            return JSONResponse({'count': 0, 'alerts': [], 'error': str(e)})


@app.get('/history')
async def history(page: int = 1, per_page: int = 20, q: str = ''):
    async with aiohttp.ClientSession() as s:
        try:
            url = f"{ORCHESTRATOR_URL}/alerts/history?page={page}&per_page={per_page}"
            if q:
                url += f"&q={q}"
            async with s.get(url, timeout=5) as r:
                data = await r.json()
                return JSONResponse(data)
        except Exception as e:
            return JSONResponse({'total': 0, 'page': page, 'per_page': per_page, 'results': [], 'error': str(e)})
