#!/usr/bin/env bash
set -euo pipefail

echo "Jetson Orin Nano — setup script (usuario)")

if ! grep -q "nvidia" /proc/device-tree/compatible 2>/dev/null; then
  echo "ADVERTENCIA: no parece ejecutarse en un Jetson (no encontrado 'nvidia' en /proc/device-tree/compatible)." >&2
  echo "Continúo, pero revisa que estés en la tarjeta Orin Nano antes de ejecutar pasos que requieran hardware." >&2
fi

echo "1) Actualizar paquetes del sistema (necesario escritorios/paquetes de desarrollo)"
sudo apt-get update
sudo apt-get upgrade -y

echo "2) Instalar paquetes de sistema recomendados"
sudo apt-get install -y build-essential cmake git pkg-config libjpeg-dev libpng-dev python3-venv python3-dev python3-pip

echo "3) Crear y activar virtualenv en ~/zoologico-venv"
python3 -m venv ~/zoologico-venv
source ~/zoologico-venv/bin/activate
pip install --upgrade pip setuptools wheel

echo "4) Instalar dependencias Python ligeras"
pip install --no-cache-dir pillow requests numpy opencv-python-headless

echo "5) Instalar PyTorch (opcional: proporcionar TORCH_WHEEL_URL). Si no, intenta instalar desde índice NVIDIA si está disponible."
if [ -n "${TORCH_WHEEL_URL:-}" ]; then
  echo "Instalando PyTorch desde: $TORCH_WHEEL_URL"
  pip install --no-cache-dir "$TORCH_WHEEL_URL"
else
  echo "No se proporcionó TORCH_WHEEL_URL. Intentando instalar 'torch' desde pip (puede fallar en Jetson)."
  pip install --no-cache-dir torch torchvision || echo "Instalación de torch fallida: descarga manual del wheel recomendada."
fi

echo "6) Instalar Ultralytics (YOLOv8) y MLflow (opcional)"
pip install --no-cache-dir ultralytics mlflow || echo "Instalación parcial fallida; revisa compatibilidad de torch/tensorrt." 

echo "7) Comprobar TensorRT (bindings Python)"
if python -c "import sys
try:
    import tensorrt
    print('tensorrt_ok')
except Exception:
    sys.exit(1)" 2>/dev/null; then
  echo "TensorRT Python disponible"
else
  echo "TensorRT Python no disponible (esto puede ser normal si no se instaló JetPack completo). Si lo necesitas, instala JetPack via SDK Manager."
fi

echo "8) Crear estructura de datos local / data lake ligera"
mkdir -p ~/zoologico/data_lake

echo "9) Finalizado. Activa el venv con: source ~/zoologico-venv/bin/activate"
echo "Luego prueba: python -c \"from ultralytics import YOLO; print('YOLO import ok')\""

echo "NOTA: Para soporte completo (drivers, CUDA, cuDNN, TensorRT), usa NVIDIA SDK Manager/JetPack desde un host Ubuntu y flashea la tarjeta." 
