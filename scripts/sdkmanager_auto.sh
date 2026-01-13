#!/usr/bin/env bash
set -euo pipefail

# sdkmanager_auto.sh
# Script helper: descarga paquetes de JetPack (modo --download) y luego realiza el flasheo (--flash)
# usando credenciales almacenadas en un archivo token seguro.
# Adaptado para JetPack 5.1.2 y Jetson Orin Nano Developer Kit.

# Usage:
#   chmod +x scripts/sdkmanager_auto.sh
#   export SDK_EMAIL="tu@email.com"
#   echo "<tu-token-o-contraseña>" > ~/.nvidia_token && chmod 600 ~/.nvidia_token
#   ./scripts/sdkmanager_auto.sh --version 5.1.2 --target "Jetson Orin Nano Developer Kit" --download-only
#   ./scripts/sdkmanager_auto.sh --version 5.1.2 --target "Jetson Orin Nano Developer Kit" --flash

EMAIL=${SDK_EMAIL:-}
TOKEN_FILE=${SDK_TOKEN_FILE:-$HOME/.nvidia_token}
GPG_FILE=${SDK_GPG_FILE:-}
SDK_SUMMARY_TO=${SDK_SUMMARY_TO:-}
SDK_LOG_DIR=${SDK_LOG_DIR:-$HOME/zoologico/sdkmanager_logs}
SDK_WEBHOOK_URL=${SDK_WEBHOOK_URL:-}
SDK_S3_BUCKET=${SDK_S3_BUCKET:-}
SDK_GCS_BUCKET=${SDK_GCS_BUCKET:-}
SDK_ENCRYPT_PASSPHRASE_FILE=${SDK_ENCRYPT_PASSPHRASE_FILE:-}
PRODUCT=${PRODUCT:-Jetson}
DOWNLOAD_ONLY=0
FLASH_ONLY=0
VERSION="5.1.2"
TARGET="Jetson Orin Nano Developer Kit"

print_usage(){
  cat <<EOF
Usage: $0 [--email <email>] [--token-file <path>] [--version <jetpack-version>] [--target <target-name>] [--download-only] [--flash-only]

Example:
  SDK_EMAIL=me@example.com SDK_TOKEN_FILE=~/.nvidia_token $0 --version 5.1.2 --target "Jetson Orin Nano Developer Kit"
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --email) EMAIL="$2"; shift 2;;
    --token-file) TOKEN_FILE="$2"; shift 2;;
    --version) VERSION="$2"; shift 2;;
    --target) TARGET="$2"; shift 2;;
    --download-only) DOWNLOAD_ONLY=1; shift;;
    --flash-only) FLASH_ONLY=1; shift;;
    --gpg-file) GPG_FILE="$2"; shift 2;;
    --summary-to) SDK_SUMMARY_TO="$2"; shift 2;;
      --webhook) SDK_WEBHOOK_URL="$2"; shift 2;;
      --s3-bucket) SDK_S3_BUCKET="$2"; shift 2;;
      --gcs-bucket) SDK_GCS_BUCKET="$2"; shift 2;;
      --encrypt-passfile) SDK_ENCRYPT_PASSPHRASE_FILE="$2"; shift 2;;
    -h|--help) print_usage; exit 0;;
    *) echo "Unknown arg: $1"; print_usage; exit 1;;
  esac
done

if [[ -z "$EMAIL" ]]; then
  echo "ERROR: Email required. Set SDK_EMAIL or pass --email." >&2
  print_usage
  exit 1
fi

if [[ ! -f "$TOKEN_FILE" ]]; then
  if [[ -z "$GPG_FILE" ]]; then
    echo "ERROR: token file not found: $TOKEN_FILE and no --gpg-file provided" >&2
    echo "Create it with: echo '<token-or-password>' > $TOKEN_FILE && chmod 600 $TOKEN_FILE" >&2
    exit 1
  fi
fi

# Obtain token: prefer GPG decryption if provided, otherwise read plain file
if [[ -n "$GPG_FILE" ]]; then
  if [[ ! -f "$GPG_FILE" ]]; then
    echo "ERROR: GPG file not found: $GPG_FILE" >&2
    exit 1
  fi
  # decrypt with gpg (expects user's gpg private key available)
  TOKEN=$(gpg --quiet --batch --decrypt "$GPG_FILE" 2>/dev/null) || {
    echo "ERROR: failed to decrypt GPG file: $GPG_FILE" >&2
    exit 1
  }
else
  TOKEN=$(<"$TOKEN_FILE")
fi

SDK_CMD="sdkmanager"
if ! command -v $SDK_CMD >/dev/null 2>&1; then
  echo "ERROR: sdkmanager not found in PATH. Instala SDK Manager en el host Ubuntu 22.04." >&2
  exit 1
fi

DOWNLOAD_CMD=("$SDK_CMD" --cli install --product "$PRODUCT" --target "$TARGET" --version "$VERSION" --download --accept-eula --email "$EMAIL" --password "$TOKEN" --logintype devzone)
FLASH_CMD=("$SDK_CMD" --cli install --product "$PRODUCT" --target "$TARGET" --version "$VERSION" --flash --accept-eula --email "$EMAIL" --password "$TOKEN" --logintype devzone)

echo "SDK Manager CLI helper"
echo "Product: $PRODUCT"
echo "Target: $TARGET"
echo "Version: $VERSION"

if [[ $FLASH_ONLY -eq 1 && $DOWNLOAD_ONLY -eq 1 ]]; then
  echo "ERROR: cannot specify both --download-only and --flash-only" >&2
  exit 1
fi

mkdir -p "$SDK_LOG_DIR"
timestamp=$(date +%Y%m%d_%H%M%S)
LOG_DOWNLOAD="$SDK_LOG_DIR/download_${timestamp}.log"
LOG_FLASH="$SDK_LOG_DIR/flash_${timestamp}.log"
SUMMARY_FILE="$SDK_LOG_DIR/summary_${timestamp}.txt"

run_cmd_to_log(){
  local -n cmd=$1
  local outfile=$2
  echo "Running: ${cmd[*]}" | tee -a "$outfile"
  ("${cmd[@]}") &>> "$outfile"
  return $?
}

encrypt_file(){
  local infile="$1"
  local outfile="$2"
  if [[ -n "${SDK_ENCRYPT_PASSPHRASE_FILE:-}" && -f "${SDK_ENCRYPT_PASSPHRASE_FILE}" ]]; then
    gpg --quiet --yes --batch --symmetric --cipher-algo AES256 --passphrase-file "${SDK_ENCRYPT_PASSPHRASE_FILE}" -o "$outfile" "$infile"
    return $?
  else
    # no passphrase file: symmetric with prompt (not suitable for automation)
    gpg --quiet --yes --batch --symmetric --cipher-algo AES256 -o "$outfile" "$infile" || return $?
  fi
}

upload_to_s3(){
  local file="$1"
  local bucket="$2"
  if command -v aws >/dev/null 2>&1; then
    aws s3 cp "$file" "s3://$bucket/$(basename "$file")"
    return $?
  else
    echo "aws CLI not found; skipping S3 upload for $file" >&2
    return 1
  fi
}

upload_to_gcs(){
  local file="$1"
  local bucket="$2"
  if command -v gsutil >/dev/null 2>&1; then
    gsutil cp "$file" "gs://$bucket/$(basename "$file")"
    return $?
  else
    echo "gsutil not found; skipping GCS upload for $file" >&2
    return 1
  fi
}

post_webhook(){
  local file="$1"
  local url="$2"
  if [[ -z "$url" ]]; then
    return 0
  fi
  if command -v curl >/dev/null 2>&1; then
    curl -s -X POST -H "Content-Type: text/plain" --data-binary @"$file" "$url" || echo "Webhook post failed" >&2
  else
    echo "curl not found; cannot POST webhook" >&2
  fi
}

if [[ $DOWNLOAD_ONLY -eq 1 ]]; then
  echo "Running download step (no flash)" | tee -a "$LOG_DOWNLOAD"
  run_cmd_to_log DOWNLOAD_CMD "$LOG_DOWNLOAD"
  rc=$?
  echo "Download exit code: $rc" | tee -a "$LOG_DOWNLOAD"
  echo "Download complete. Logs: $LOG_DOWNLOAD"
  echo "Download finished with rc=$rc" > "$SUMMARY_FILE"
  tail -n 200 "$LOG_DOWNLOAD" >> "$SUMMARY_FILE" 2>/dev/null || true
  # send or save summary
  if [[ -n "${SDK_SUMMARY_TO:-}" || -n "${SDK_SUMMARY_TO}" ]]; then
    if command -v mail >/dev/null 2>&1; then
      cat "$SUMMARY_FILE" | mail -s "SDKManager download summary $timestamp" "$SDK_SUMMARY_TO"
    elif command -v sendmail >/dev/null 2>&1; then
      (echo "Subject: SDKManager download summary $timestamp"; cat "$SUMMARY_FILE") | sendmail "$SDK_SUMMARY_TO"
    else
      echo "No mailer found; summary saved to $SUMMARY_FILE"
    fi
  else
    echo "Summary saved to $SUMMARY_FILE"
  fi
  # upload encrypted summary/logs if requested
  uploaded_urls=()
  if [[ -n "${SDK_S3_BUCKET:-}" ]]; then
    enc_summary="$SUMMARY_FILE.gpg"
    if encrypt_file "$SUMMARY_FILE" "$enc_summary"; then
      if upload_to_s3 "$enc_summary" "$SDK_S3_BUCKET"; then
        uploaded_urls+=("s3://$SDK_S3_BUCKET/$(basename "$enc_summary")")
      fi
    fi
  fi
  if [[ -n "${SDK_GCS_BUCKET:-}" ]]; then
    enc_summary_gcs="$SUMMARY_FILE.gpg"
    if encrypt_file "$SUMMARY_FILE" "$enc_summary_gcs"; then
      if upload_to_gcs "$enc_summary_gcs" "$SDK_GCS_BUCKET"; then
        uploaded_urls+=("gs://$SDK_GCS_BUCKET/$(basename "$enc_summary_gcs")")
      fi
    fi
  fi
  if [[ -n "${SDK_WEBHOOK_URL:-}" ]]; then
    # include uploaded urls in webhook payload
    tmp_payload="$SUMMARY_FILE.webhook"
    echo "Summary: $SUMMARY_FILE" > "$tmp_payload"
    if [[ ${#uploaded_urls[@]} -gt 0 ]]; then
      echo "Uploaded URLs:" >> "$tmp_payload"
      for u in "${uploaded_urls[@]}"; do echo "$u" >> "$tmp_payload"; done
    fi
    echo >> "$tmp_payload"
    cat "$SUMMARY_FILE" >> "$tmp_payload"
    post_webhook "$tmp_payload" "$SDK_WEBHOOK_URL"
    rm -f "$tmp_payload"
  fi
  exit $rc
fi

if [[ $FLASH_ONLY -eq 1 ]]; then
  echo "Running flash step (flash only)" | tee -a "$LOG_FLASH"
  run_cmd_to_log FLASH_CMD "$LOG_FLASH"
  rc=$?
  echo "Flash exit code: $rc" | tee -a "$LOG_FLASH"
  echo "Flash complete. Logs: $LOG_FLASH"
  echo "Flash finished with rc=$rc" > "$SUMMARY_FILE"
  tail -n 200 "$LOG_FLASH" >> "$SUMMARY_FILE" 2>/dev/null || true
  if [[ -n "${SDK_SUMMARY_TO:-}" || -n "${SDK_SUMMARY_TO}" ]]; then
    if command -v mail >/dev/null 2>&1; then
      cat "$SUMMARY_FILE" | mail -s "SDKManager flash summary $timestamp" "$SDK_SUMMARY_TO"
    elif command -v sendmail >/dev/null 2>&1; then
      (echo "Subject: SDKManager flash summary $timestamp"; cat "$SUMMARY_FILE") | sendmail "$SDK_SUMMARY_TO"
    else
      echo "No mailer found; summary saved to $SUMMARY_FILE"
    fi
  else
    echo "Summary saved to $SUMMARY_FILE"
  fi
  exit $rc
fi

echo "Step 1/2: download packages (this may take tiempo). Logs -> $LOG_DOWNLOAD"
run_cmd_to_log DOWNLOAD_CMD "$LOG_DOWNLOAD"
rc_download=$?

echo "Step 2/2: running flash (asegúrate que el target está en modo recovery). Logs -> $LOG_FLASH"
run_cmd_to_log FLASH_CMD "$LOG_FLASH"
rc_flash=$?

{
  echo "SDKManager run summary:"
  echo "Product: $PRODUCT"
  echo "Target: $TARGET"
  echo "Version: $VERSION"
  echo "Download rc: $rc_download"
  echo "Flash rc: $rc_flash"
  echo
  echo "--- tail of download log ---"
  tail -n 200 "$LOG_DOWNLOAD" 2>/dev/null || true
  echo
  echo "--- tail of flash log ---"
  tail -n 200 "$LOG_FLASH" 2>/dev/null || true
} > "$SUMMARY_FILE"

if [[ -n "${SDK_SUMMARY_TO:-}" ]]; then
  if command -v mail >/dev/null 2>&1; then
    cat "$SUMMARY_FILE" | mail -s "SDKManager summary $timestamp" "$SDK_SUMMARY_TO"
  elif command -v sendmail >/dev/null 2>&1; then
    (echo "Subject: SDKManager summary $timestamp"; cat "$SUMMARY_FILE") | sendmail "$SDK_SUMMARY_TO"
  else
    echo "No mailer found; summary saved to $SUMMARY_FILE"
  fi
else
  echo "Summary saved to $SUMMARY_FILE"
fi
# optional: upload and webhook
if [[ -n "${SDK_S3_BUCKET:-}" ]]; then
  enc_summary="$SUMMARY_FILE.gpg"
  encrypt_file "$SUMMARY_FILE" "$enc_summary" && upload_to_s3 "$enc_summary" "$SDK_S3_BUCKET" || true
fi
if [[ -n "${SDK_GCS_BUCKET:-}" ]]; then
  enc_summary="$SUMMARY_FILE.gpg"
  encrypt_file "$SUMMARY_FILE" "$enc_summary" && upload_to_gcs "$enc_summary" "$SDK_GCS_BUCKET" || true
fi
if [[ -n "${SDK_WEBHOOK_URL:-}" ]]; then
  post_webhook "$SUMMARY_FILE" "$SDK_WEBHOOK_URL"
fi

if [[ $rc_download -ne 0 || $rc_flash -ne 0 ]]; then
  echo "One or more steps failed: download_rc=$rc_download flash_rc=$rc_flash" >&2
  exit 1
fi

echo "Done. Revisa $SUMMARY_FILE para detalles."
