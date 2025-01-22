FROM debian:bullseye

# Aktualizace systému a instalace potřebných nástrojů
RUN apt-get update && apt-get install -y \
    cron \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Kopírování skriptu do kontejneru
COPY backup_script.sh /usr/local/bin/backup_script.sh
RUN chmod +x /usr/local/bin/backup_script.sh

# Nastavení cronu
COPY crontab /etc/cron.d/backup-cron
RUN chmod 0644 /etc/cron.d/backup-cron
RUN crontab /etc/cron.d/backup-cron

# Spuštění cronu při startu kontejneru
CMD ["cron", "-f"]
