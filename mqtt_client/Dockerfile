FROM python:3.7-slim

WORKDIR /app
COPY mqtt_client.py /app/mqtt_client.py
COPY mqtt_client_config.json /app/mqtt_client_config.json

# Install Python packages
RUN pip install hbmqtt websockets==8.1 paho-mqtt typing_extensions ujson

CMD ["python", "mqtt_client.py"]




