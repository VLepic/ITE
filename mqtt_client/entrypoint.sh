#!/bin/sh

# Create or overwrite mqtt_client_config.json only if it does not exist
if [ ! -f /app/mqtt_client_config.json ]; then
cat <<EOF > /app/mqtt_client_config.json
{
  "TEAM_NAME": "${TEAM_NAME}",
  "BROKER_IP": "${BROKER_IP}",
  "BROKER_PORT": ${BROKER_PORT},
  "BROKER_USERNAME": "${BROKER_USERNAME}",
  "BROKER_PASSWORD": "${BROKER_PASSWORD}",
  "INFLUXDB_URL": "http://influxdb:8086",
  "INFLUXDB_TOKEN": "${DOCKER_INFLUXDB_INIT_MQTT_CLIENT_TOKEN}",
  "INFLUXDB_ORG": "${DOCKER_INFLUXDB_INIT_ORG}",
  "INFLUXDB_BUCKET": "${DOCKER_INFLUXDB_INIT_BUCKET}",
  "LOGGING_LEVEL": "${LOGGING_LEVEL}",
  "BASE_URL": "${BASE_URL}",
  "AIMTEC_USERNAME": "${AIMTEC_USERNAME}",
  "AIMTEC_PASSWORD": "${AIMTEC_PASSWORD}",
  "SEND_TO_API": "${SEND_TO_API}"
}
EOF
fi

# Create or overwrite UUIDs.json only if it does not exist
if [ ! -f /app/UUIDs.json ]; then
cat <<EOF > /app/UUIDs.json
{
  "temperature":"${sensorUUID_TEMPERATURE}",
  "humidity":"${sensorUUID_HUMIDITY}",
  "illumination":"${sensorUUID_ILLUMINATION}"
}
EOF
fi

# Start the MQTT client
exec python mqtt_client.py

