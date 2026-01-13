```` 

## Deployment

Se añadió un manifiesto `k8s/manifest.yaml` y un workflow de CI (`.github/workflows/build-and-deploy.yml`) que automatiza construcción y push de imágenes a GitHub Container Registry (GHCR) y despliegue a Kubernetes.

- Para desplegar vía GitHub Actions: añade un secret `KUBE_CONFIG` (base64 del `kubeconfig`) en Settings → Secrets. El workflow construye imágenes y aplica `k8s/manifest.yaml` con las imágenes generadas.

- Para desplegar manualmente, sustituye los placeholders en `k8s/manifest.yaml` y aplica:

```bash
sed -e "s#__ORCHESTRATOR_IMAGE__#ghcr.io/<owner>/zoologico-orchestrator:<tag>#g" \
	-e "s#__EDGE_IMAGE__#ghcr.io/<owner>/zoologico-edge:<tag>#g" \
	-e "s#__CLOUD_IMAGE__#ghcr.io/<owner>/zoologico-cloud:<tag>#g" \
	-e "s#__MCP_IMAGE__#ghcr.io/<owner>/zoologico-mcp:<tag>#g" \
	k8s/manifest.yaml > k8s/rendered.yaml
kubectl apply -f k8s/rendered.yaml
```

Si prefieres desplegar con `docker compose` en un host remoto, copia el `docker-compose.yml` al host y ejecuta `docker compose up -d --build`.
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
- `scripts/sdkmanager_auto.sh`: helper para descargar y flashear JetPack (CLI) con logging, GPG support y subida cifrada de logs.
- `data/`: generador y dataset sintético para preentrenamiento.

Archivos útiles
- `scripts/jetson_setup.sh`: script de preparación de entorno en Jetson Orin Nano.
- `scripts/sdkmanager_auto.sh`: descarga y flasheo automatizado con soporte de token GPG, logs y subida a S3/GCS.

Notas rápidas
- Para pruebas locales sin GPU, usa el flujo sin Docker o con `docker-compose` (ver `docs/run_local.md`).
- Para preparar una Jetson Orin Nano, sigue `docs/jetson_setup.md` y usa `scripts/sdkmanager_auto.sh` para automatizar descarga+flash.

Soporte de seguridad para SDK Manager
- El script `scripts/sdkmanager_auto.sh` soporta token en texto plano (`SDK_TOKEN_FILE`) o token GPG (`--gpg-file`/`SDK_GPG_FILE`). También cifra los summaries con GPG antes de subirlos a S3/GCS.

Contacto
- Si quieres que pruebe el flujo completo en este entorno (sin flasheo), dime y ejecuto las pruebas locales restantes.

Próximos pasos
- Revisar `docs/architecture.md`.
- Decidir versión de YOLO a integrar (YOLOv5/YOLOv8/TorchServe) para implementar el agente.
- ¿Deseas que integre YOLO localmente ahora? Indica preferencia de modelo y si usaremos GPU.

Contacto
- Pide: "Implementa YOLO" para que empiece la integración.

Token y permisos (resumen rápido)
- Nunca subas `~/.nvidia_token` ni `~/.encrypt_pass` a repositorios.
- Recomiendo usar token cifrado con GPG (`~/.nvidia_token.gpg`) y un archivo de passphrase con permisos `600` si automatizas.
- Permisos sugeridos:
	- `chmod 600 ~/.nvidia_token` (si existe en claro)
	- `chmod 600 ~/.encrypt_pass`
	- `chmod 600 ~/.nvidia_token.gpg`

Consulta `docs/token_readme.md` para ejemplos y comandos.

CI / pre-commit
- Este repositorio incluye un workflow de GitHub Actions `.github/workflows/ci-sdkmanager.yml` que verifica `scripts/sdkmanager_auto.sh` con `shellcheck` y `bash -n`.
- Para activar Actions: ve a la página del repositorio en GitHub → Settings → Actions, y habilita Actions si está deshabilitado.
- Para probar localmente y configurar hooks:

```bash
# instalar pre-commit y hooks
python3 -m pip install --user pre-commit
~/.local/bin/pre-commit install

# ejecutar lint localmente
make lint
```

Para probar un PR usando la CLI `gh` (GitHub):

```bash
# crea una rama, haz cambios y push
git checkout -b ci/test-sdk
git add scripts/sdkmanager_auto.sh
git commit -m "test: ci for sdkmanager script"
git push --set-upstream origin ci/test-sdk

# crear PR (requiere gh CLI autenticado)
gh pr create --fill --base main --head ci/test-sdk

# una vez creado, la Actions pipeline se ejecutará automáticamente.
```