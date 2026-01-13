import time
from mlflow import log_param, log_metric, log_artifact, set_experiment, start_run

set_experiment('zoologico-training')

with start_run('example-run') as run:
    log_param('model','yolov8n')
    for epoch in range(3):
        # simulación de entrenamiento
        loss = 1.0/(epoch+1)
        acc = epoch * 10 + 50
        log_metric('loss', loss, step=epoch)
        log_metric('acc', acc, step=epoch)
        time.sleep(0.5)
    # guardar artefacto simulado
    with open('dummy-model.txt','w') as f:
        f.write('modelo simulado')
    log_artifact('dummy-model.txt')
    print('Run finished:', run.info.run_id)
