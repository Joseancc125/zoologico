#!/usr/bin/env python3
"""MCP lightweight broker: recibe POST /publish y guarda/reenruta a suscriptores.
Esta es una implementación mínima para pruebas locales.
"""
from aiohttp import web
import asyncio
import json

SUBSCRIBERS = []
import os
import json as _json
_PERSIST_FILE = os.path.join(os.getcwd(), 'mcp_subscribers.json')

def _load_subscribers():
    try:
        with open(_PERSIST_FILE, 'r') as f:
            data = _json.load(f)
            return data.get('subscribers', [])
    except Exception:
        return []

def _save_subscribers():
    try:
        with open(_PERSIST_FILE, 'w') as f:
            _json.dump({'subscribers': SUBSCRIBERS}, f)
    except Exception:
        pass

routes = web.RouteTableDef()

@routes.post('/publish')
async def publish(request):
    data = await request.json()
    # reenviar a todos los suscriptores (HTTP POST)
    for url in list(SUBSCRIBERS):
        asyncio.create_task(_post(url, data))
    return web.json_response({'status':'published'})

@routes.post('/subscribe')
async def subscribe(request):
    body = await request.json()
    url = body.get('callback_url')
    if url and url not in SUBSCRIBERS:
        SUBSCRIBERS.append(url)
        _save_subscribers()
    return web.json_response({'status':'subscribed','callback':url})


@routes.get('/subscribers')
async def list_subscribers(request):
    return web.json_response({'subscribers': SUBSCRIBERS})

async def _post(url, data):
    import aiohttp
    try:
        async with aiohttp.ClientSession() as s:
            await s.post(url, json=data, timeout=3)
    except Exception:
        pass

app = web.Application()
app.add_routes(routes)
if __name__ == '__main__':
    # cargar subscriptores previamente almacenados
    SUBSCRIBERS[:] = _load_subscribers()
    web.run_app(app, port=9000)
