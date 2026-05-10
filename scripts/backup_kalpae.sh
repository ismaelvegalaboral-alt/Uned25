#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/kalpae/ausencias}"
BACKUP_DIR="${BACKUP_DIR:-/home/kalpae/backups/ausencias}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

STAMP="$(date +'%Y%m%d_%H%M%S')"
TMP_DIR="$(mktemp -d)"
ARCHIVE="$BACKUP_DIR/kalpae_ausencias_$STAMP.tar.gz"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "[backup] Copiando base de datos..."
python3 - <<PY
import sqlite3
from pathlib import Path

src = Path("$APP_DIR") / "db.sqlite3"
dst = Path("$TMP_DIR") / "db.sqlite3"

src_conn = sqlite3.connect(src)
dst_conn = sqlite3.connect(dst)
with dst_conn:
    src_conn.backup(dst_conn)
dst_conn.close()
src_conn.close()
PY

echo "[backup] Copiando media..."
if [ -d "$APP_DIR/media" ]; then
  cp -a "$APP_DIR/media" "$TMP_DIR/media"
fi

echo "[backup] Creando archivo $ARCHIVE..."
tar -czf "$ARCHIVE" -C "$TMP_DIR" .
chmod 600 "$ARCHIVE"

echo "[backup] Eliminando backups de más de $RETENTION_DAYS días..."
find "$BACKUP_DIR" -type f -name 'kalpae_ausencias_*.tar.gz' -mtime +"$RETENTION_DAYS" -delete

echo "[backup] OK: $ARCHIVE"
