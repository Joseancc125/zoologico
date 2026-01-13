Jetson Orin Nano — Guía rápida de setup

Resumen
-------
Estas instrucciones preparan un Jetson Orin Nano (8 GB) para desarrollo de visión por computador y ML: recomendaciones para flasheo (JetPack), y un script de configuración de software de usuario (Python, PyTorch, YOLOv8, MLflow, utilidades).

IMPORTANTE: no puedo ejecutar o flashear la placa desde este contenedor. Debes ejecutar los pasos y el script directamente en tu Jetson o en el host (según se indique).

1) Flashear Jetson con JetPack (recomendado)
- Usa NVIDIA SDK Manager desde un PC Ubuntu compatible para flashear la SD/emmc con JetPack (incluye L4T, kernel, CUDA, cuDNN, TensorRT). URL: https://developer.nvidia.com/jetpack-sdk
- Si prefieres flasheo manual o imagen, sigue la documentación oficial de NVIDIA para tu versión de JetPack.

2) Verificar instalación básica en Jetson
- SSH/abre consola en la tarjeta y comprueba:
  - `uname -a`
  - `nvcc --version` (debería existir)
  - `dpkg -l | grep nvidia` y `dpkg -l | grep cuda`

3) Instalar paquetes de sistema (script recomendado)
- He incluido `scripts/jetson_setup.sh` que realiza instalación de paquetes de usuario, crea un `venv`, y ayuda a instalar PyTorch/Ultralytics. Ejecuta el script en la tarjeta Jetson.

4) PyTorch y ultralytics en Jetson
- PyTorch para Jetson suele instalarse mediante un wheel preparado para la versión de JetPack/L4T. NVIDIA publica wheels o instrucciones. El script permite pasar la URL del wheel a la variable `TORCH_WHEEL_URL` o instalar `torch` desde el índice provisto por NVIDIA si aplica.

5) TensorRT
- TensorRT viene normalmente con JetPack; las bindings Python se instalan vía apt (p. ej. `python3-libnvinfer`) o ya están disponibles. El script detecta si están presentes y avisará.

6) Docker en Jetson
- Para ejecutar contenedores con aceleración en Jetson, usa las imágenes `nvcr.io` o `jetson/` y la NVIDIA container runtime para ARM (en Jetson la integración es distinta a x86). Revisa `https://github.com/NVIDIA/jetson-containers`.

7) Post-setup y prueba
- Tras ejecutar el script, activa el `venv`, instala YOLOv8 (`pip install ultralytics`) y prueba `python -c "from ultralytics import YOLO; print('ok')"`.

Script y pasos de ejemplo
- Ejecuta en la Jetson:

```bash
# descargar el repositorio y el script
cd ~/proj && git clone <tu-repo> && cd zoologico
bash scripts/jetson_setup.sh
```

Si quieres, te guío en cada paso por SSH y reviso los logs mientras lo ejecutas.
