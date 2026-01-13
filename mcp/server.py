#!/usr/bin/env python3
"""MCP lightweight broker: recibe POST /publish y guarda/reenruta a suscriptores.
Esta es una implementación mínima para pruebas locales.
"""
from aiohttp import web
import asyncio
import json

SUBSCRIBERS = []

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
    return web.json_response({'status':'subscribed','callback':url})

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
    web.run_app(app, port=9000)
