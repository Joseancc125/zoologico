Token y passphrase — recomendaciones y ejemplos

Archivos sensibles
- `~/.nvidia_token`: token o contraseña para SDK Manager (si usas CLI con `--password`).
- `~/.nvidia_token.gpg`: token cifrado con GPG (recomendado).
- `~/.encrypt_pass`: passphrase para cifrar summaries/logs con GPG (opcional).

Permisos recomendados
- Asegura que sólo tu usuario pueda leer estos ficheros:

```bash
# crear token en claro (no recomendado):
echo "<tu-token>" > ~/.nvidia_token
chmod 600 ~/.nvidia_token

# crear passphrase file (para cifrado automático):
echo "<passphrase>" > ~/.encrypt_pass
chmod 600 ~/.encrypt_pass

# cifrar token con GPG (recomendado):
# esto crea ~/.nvidia_token.gpg
echo "<tu-token>" | gpg --symmetric --cipher-algo AES256 -o ~/.nvidia_token.gpg
chmod 600 ~/.nvidia_token.gpg
```

Cómo usar con `scripts/sdkmanager_auto.sh`
- Usando token en texto plano:

```bash
SDK_EMAIL=you@example.com SDK_TOKEN_FILE=~/.nvidia_token \ \
  ./scripts/sdkmanager_auto.sh --version 5.1.2 --target "Jetson Orin Nano Developer Kit" --download-only
```

- Usando token GPG (recomendado):

```bash
SDK_EMAIL=you@example.com SDK_GPG_FILE=~/.nvidia_token.gpg \ \
  SDK_ENCRYPT_PASSPHRASE_FILE=~/.encrypt_pass \ \
  ./scripts/sdkmanager_auto.sh --version 5.1.2 --target "Jetson Orin Nano Developer Kit" --download-only
```

Ejemplo: subir resumen a S3 y notificar webhook

```bash
SDK_EMAIL=you@example.com SDK_GPG_FILE=~/.nvidia_token.gpg \ \
  SDK_ENCRYPT_PASSPHRASE_FILE=~/.encrypt_pass \ \
  SDK_S3_BUCKET=my-bucket \ \
  SDK_WEBHOOK_URL=https://hooks.example.com/sdk-notify \ \
  ./scripts/sdkmanager_auto.sh --version 5.1.2 --target "Jetson Orin Nano Developer Kit" --download-only --summary-to ops@example.com
```

Notas de seguridad
- Nunca subas `~/.nvidia_token` a repositorios.
- Usa GPG para cifrar tokens y passphrases cuando automatices.
- Protege `~/.encrypt_pass` con permisos `600` y considera usar `gpg-agent` o un KMS en producción.

*** End Patch