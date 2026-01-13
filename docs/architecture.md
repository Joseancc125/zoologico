Arquitectura propuesta

- Cámaras -> agentes de borde (edge) en las oficinas del zoológico.
- Agentes de borde: realizan captura de frames, detección ligera con YOLO (opcional), envían alertas al Orquestador/MCP.
- Orquestador (API central): centraliza alertas, agrega metadatos (ubicación, hora, confianza) y publica en MCP.
- MCP (broker de contexto): enruta eventos a consumidores suscritos: sistema de alertas, almacenamiento, y la nube.
- Nube: procesado batch para análisis históricos y entrenamiento de modelos.

Decisiones
- Comunicación interna: HTTP/REST para eventos simples, gRPC o WebSocket para streams si se necesita baja latencia.
- Formato mensajes: JSON con campos `camera_id`, `timestamp`, `bbox`, `label`, `confidence`, `frame_url`.
- YOLO: integrar como dependencia opcional en los agentes; usar versión según disponibilidad de GPU.
