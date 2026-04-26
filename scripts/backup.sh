#!/bin/bash
# backup.sh — PostgreSQL database backup
# Usage: bash scripts/backup.sh
# Schedule (add to host crontab): 0 */6 * * * /home/viko/real-estate-watchdog/app/scripts/backup.sh

set -euo pipefail

BACKUP_DIR=/home/viko/real-estate-watchdog/backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/watchdog_${TIMESTAMP}.sql.gz"

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

echo "[$(date -u +%FT%TZ)] Starting backup → ${BACKUP_FILE}"

# pg_dump from inside the DB container, piped to gzip on the host
docker exec watchdog-db-1 pg_dump -U watchdog watchdog | gzip > "${BACKUP_FILE}"

# Verify the backup file is non-empty
BACKUP_SIZE=$(stat -c%s "${BACKUP_FILE}" 2>/dev/null || stat -f%z "${BACKUP_FILE}")
if [ "${BACKUP_SIZE}" -lt 1024 ]; then
    echo "[$(date -u +%FT%TZ)] ERROR: Backup file is suspiciously small (${BACKUP_SIZE} bytes). Check DB connectivity."
    exit 1
fi

# Rotate: keep the 28 most recent backups (7 days × 4/day)
ls -t "${BACKUP_DIR}"/*.sql.gz | tail -n +29 | xargs rm -f 2>/dev/null || true

BACKUP_COUNT=$(ls "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | wc -l)
echo "[$(date -u +%FT%TZ)] Backup complete: ${BACKUP_FILE} (${BACKUP_SIZE} bytes). Total backups: ${BACKUP_COUNT}"
