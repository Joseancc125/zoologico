import mlflow
import os

MLFLOW_URI = os.environ.get('MLFLOW_TRACKING_URI', 'http://mlflow:5001')
mlflow.set_tracking_uri(MLFLOW_URI)

def start_run(name=None, tags=None):
    return mlflow.start_run(run_name=name, tags=tags)

def log_params(params: dict):
    for k,v in params.items():
        mlflow.log_param(k, v)

def log_metrics(metrics: dict, step=None):
    for k,v in metrics.items():
        mlflow.log_metric(k, v, step=step)

def log_artifact(path, artifact_path=None):
    mlflow.log_artifact(path, artifact_path=artifact_path)

def set_experiment(name):
    mlflow.set_experiment(name)
