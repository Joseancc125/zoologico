Ejecución local (rápida)

1) Instalar dependencias (recomendado en virtualenv)

```bash
pip install -r requirements.txt
```

2) Levantar servicios básicos con Docker Compose

```bash
docker-compose up --build
```

- `orchestrator` en http://localhost:8000
- `edge_agent` en http://localhost:8100
- `cloud_processor` en http://localhost:5000
- `mlflow` UI en http://localhost:5001

3) Enviar frame de prueba

```bash
python tools/send_test_frame.py
```

4) Ejecutar ejemplo de entrenamiento que registra en MLflow

```bash
python cloud/processor/train_example.py
```

5) Ejemplo de entrenamiento DDP (local, sintético)

```bash
# single-process demo
python cloud/training/ddp_train.py --rank 0 --world_size 1

# para multi-proceso en la misma máquina usar torchrun (instalar torch correctamente):
# torchrun --nproc_per_node=2 cloud/training/ddp_train.py --world_size 2
```
