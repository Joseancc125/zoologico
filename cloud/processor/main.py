from flask import Flask, request
import time

app = Flask(__name__)

@app.route('/ingest', methods=['POST'])
def ingest():
    payload = request.get_json()
    # Aquí iría el procesamiento batch o almacenamiento en data lake
    print('Ingested:', payload.get('camera_id'), payload.get('timestamp'))
    return {'status':'ingested'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
