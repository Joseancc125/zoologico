MLflow — integración

Este repositorio incluye soporte básico para MLflow.

Cómo usar (local con docker-compose):

1. Levanta servicios:

```bash
docker-compose up --build
```

2. Abre UI de MLflow en http://localhost:5001

3. Ejecuta ejemplo de entrenamiento:

```bash
pip install -r requirements.txt
python cloud/processor/train_example.py
```

Notas
- `mlflow/tracking.py` contiene helpers para registrar experimentos.
- El servicio `mlflow` en `docker-compose.yml` usa SQLite como backend (no recomendado para producción).
- Para producción se recomienda usar un backend SQL y un almacenamiento de artefactos (S3, GCS).
