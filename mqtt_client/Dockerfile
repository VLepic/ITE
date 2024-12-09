FROM python:3.12-slim

WORKDIR /app
COPY ./ /app/

# Install Python packages
RUN pip install hbmqtt websockets==8.1 paho-mqtt typing_extensions ujson influxdb_client requests tqdm pytz

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh





