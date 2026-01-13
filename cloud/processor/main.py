from flask import Flask, request
import time
import os

app = Flask(__name__)

# MLflow is optional for local quick tests. If not installed, skip MLflow logging.
_has_mlflow = False
try:
    from mlflow import set_experiment, start_run, log_param, log_metric, log_artifact
    _has_mlflow = True
except Exception:
    _has_mlflow = False

if _has_mlflow:
    MLFLOW_URI = os.environ.get('MLFLOW_TRACKING_URI', 'http://mlflow:5001')
    try:
        set_experiment('zoologico-ingest')
    except Exception:
        pass


@app.route('/ingest', methods=['POST'])
def ingest():
    payload = request.get_json() or {}
    camera = payload.get('camera_id')
    ts = payload.get('timestamp')
    print('Ingested:', camera, ts)

    # Optional MLflow logging
    if _has_mlflow:
        try:
            with start_run('ingest-event') as run:
                log_param('camera_id', camera)
                log_metric('event_timestamp', float(ts or time.time()))
        except Exception:
            pass

    # Guardar en archivo de log local (simulación de almacenamiento / data lake)
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/ingest.log', 'a') as f:
            f.write(str(payload) + "\n")
    except Exception:
        pass

    return {'status':'ingested'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
