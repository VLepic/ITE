#!/bin/bash

# Nastavení časového razítka
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# PostgreSQL záloha
docker exec postgres-db pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > /backups/postgres_backup_$TIMESTAMP.sql

# InfluxDB záloha
docker exec influxdb influx backup /backups/influx_backup_$TIMESTAMP

# Log zálohy
echo "Backup completed at $TIMESTAMP" >> /backups/backup.log
