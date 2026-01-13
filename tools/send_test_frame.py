import requests
from PIL import Image, ImageDraw
import io

# Genera una imagen simple y la envía al agente de borde
img = Image.new('RGB', (128,128), color=(73,109,137))
d = ImageDraw.Draw(img)
d.rectangle([10,10,60,60], outline='red')
b = io.BytesIO()
img.save(b, format='JPEG')
b.seek(0)

files = {'file': ('frame.jpg', b, 'image/jpeg')}
resp = requests.post('http://localhost:8100/frame', files=files, params={'camera_id':'cam-test'})
print('response', resp.status_code, resp.text)
