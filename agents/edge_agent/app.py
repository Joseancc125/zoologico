from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import requests
import time
import uuid
from . import detector

app = FastAPI(title="Edge Agent")
ORCHESTRATOR_URL = "http://orchestrator:8000/alert"

class Detection(BaseModel):
    camera_id: str
    timestamp: float
    label: str
    confidence: float
    bbox: list
    frame_id: str

@app.post("/frame")
async def receive_frame(file: UploadFile = File(...), camera_id: str = "cam-01"):
    # guardamos el frame localmente (simulación)
    frame_id = str(uuid.uuid4())
    path = f"/tmp/{frame_id}.jpg"
    with open(path, "wb") as f:
        f.write(await file.read())

    # Ejecutar detector (YOLOv8) si está disponible
    detections = detector.detect(path)
    # Seleccionar la detección con mayor confianza (si existe)
    if detections:
        best = max(detections, key=lambda d: d.get('confidence', 0))
        det = Detection(camera_id=camera_id, timestamp=time.time(), label=best.get('label','unknown'), confidence=best.get('confidence',0.0), bbox=best.get('bbox',[]), frame_id=frame_id)
    else:
        det = Detection(camera_id=camera_id, timestamp=time.time(), label="unknown", confidence=0.0, bbox=[], frame_id=frame_id)

    # Enviar alerta al orquestador
    try:
        requests.post(ORCHESTRATOR_URL, json=det.dict(), timeout=2)
    except Exception:
        pass

    return {"status": "received", "frame_id": frame_id}
