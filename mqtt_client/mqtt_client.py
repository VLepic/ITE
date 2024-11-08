import os
import json
import logging
from datetime import datetime
import paho.mqtt.client as mqtt

import ujson

# Load Wi-Fi and MQTT credentials from JSON file
with open("mqtt_client_config.json") as f:
    secrets = ujson.load(f)

BROKER_IP = secrets["BROKER_IP"]
BROKER_PORT = secrets["BROKER_PORT"]
BROKER_USERNAME = secrets["BROKER_USERNAME"]
BROKER_PASSWORD = secrets["BROKER_PASSWORD"]
INFLUXDB_URL = secrets["INFLUXDB_URL"]
INFLUXDB_TOKEN = secrets["INFLUXDB_TOKEN"]
INFLUXDB_ORG = secrets["INFLUXDB_ORG"]
INFLUXDB_BUCKET = secrets["INFLUXDB_BUCKET"]
TEAM_NAME = secrets["TEAM_NAME"]
TOPIC = "ite/#"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Callback for successful connection
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker successfully")
    else:
        logger.error(f"Failed to connect, return code {rc}")
    client.subscribe(TOPIC)
    logger.info(f"Subscribed to topic pattern: {TOPIC}")


# Callback for received messages
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        team_name = payload.get("team_name", "unknown")
        logger.info(f"Received message from team '{team_name}' on topic {msg.topic}: {payload}")

        logger.info(f"Team: {team_name}, Timestamp: {payload.get('timestamp')}")
        logger.info(f"Temperature: {payload.get('temperature')}°C")

        if "humidity" in payload:
            logger.info(f"Humidity: {payload['humidity']}%")
        if "illumination" in payload:
            logger.info(f"Illumination: {payload['illumination']} lux")

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON payload")
    except Exception as e:
        logger.error(f"Error processing message: {e}")


# Initialize MQTT client
client = mqtt.Client()
client.username_pw_set(BROKER_USERNAME, BROKER_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect(BROKER_IP, BROKER_PORT, 60)
client.loop_forever()



