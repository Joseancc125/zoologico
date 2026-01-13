#!/usr/bin/env bash
set -euo pipefail

OUTDIR="$(pwd)/certs"
mkdir -p "$OUTDIR"

CSR_SUBJ="/C=US/ST=Denial/L=Springfield/O=Zoologico/CN=localhost"

echo "Generating self-signed certificate into $OUTDIR"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$OUTDIR/dashboard.key" -out "$OUTDIR/dashboard.crt" \
  -subj "$CSR_SUBJ"

chmod 600 "$OUTDIR/dashboard.key" || true
echo "Done. Files: $OUTDIR/dashboard.crt, $OUTDIR/dashboard.key"
