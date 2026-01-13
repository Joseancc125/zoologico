from fastapi import FastAPI, Request
import asyncio
import aiohttp
import json

app = FastAPI(title="Orchestrator")
MCP_URL = "http://mcp:9000/publish"
CLOUD_URL = "http://cloud_processor:5000/ingest"

@app.post("/alert")
async def alert(request: Request):
    body = await request.json()
    # Enriquecer con metadatos si hace falta
    body['received_at'] = asyncio.get_event_loop().time()

    # Publicar en MCP (simple HTTP POST al broker)
    async with aiohttp.ClientSession() as s:
        try:
            await s.post(MCP_URL, json=body, timeout=2)
        except Exception:
            pass

    # También enviar copia a procesador en la nube (no bloqueante)
    asyncio.create_task(_forward_to_cloud(body))

    return {"status": "ok"}

async def _forward_to_cloud(payload):
    async with aiohttp.ClientSession() as s:
        try:
            await s.post(CLOUD_URL, json=payload, timeout=5)
        except Exception:
            pass
