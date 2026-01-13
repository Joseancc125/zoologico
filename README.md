# Zoológico — Sistema distribuido de detección de animales

Resumen
-------
Este repositorio contiene un esqueleto para un sistema distribuido que procesa video de cámaras de seguridad del zoológico.

Componentes clave
- Agentes de borde (edge): reciben frames y ejecutan detección ligera (hook para YOLO).
- Orquestador / MCP: recibe alertas, enriquece contexto y enruta eventos.
- Procesador en la nube: análisis batch y tendencias históricas.

Qué hay en este repositorio
- `agents/edge_agent/`: servicio de borde (API para enviar frames).
- `orchestrator/`: API central que recibe alertas.
- `mcp/`: servidor ligero de Model Context Protocol (broker de contexto).
- `cloud/processor/`: scripts para procesamiento batch.
- `docker-compose.yml`: desplegar servicios básicos localmente.
- `docs/architecture.md`: diagrama y decisiones de diseño.

Próximos pasos
- Revisar `docs/architecture.md`.
- Decidir versión de YOLO a integrar (YOLOv5/YOLOv8/TorchServe) para implementar el agente.
- ¿Deseas que integre YOLO localmente ahora? Indica preferencia de modelo y si usaremos GPU.

Contacto
- Pide: "Implementa YOLO" para que empiece la integración.