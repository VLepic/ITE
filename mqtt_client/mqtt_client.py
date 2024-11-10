import logging
from datetime import datetime
import json
import time
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import ujson
from paho.mqtt.client import LOGGING_LEVEL

# Load configuration from JSON file
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
LOG_LEVEL = secrets["LOGGING_LEVEL"]
TOPIC = "ite/#"


# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize InfluxDB client
influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)
# Wait for InfluxDB to be reachable
while True:
    try:
        if influx_client.ping():
            logger.info("Connected to InfluxDB successfully.")
            break
        else:
            raise ConnectionError("InfluxDB ping failed")
    except ConnectionError as e:
        logger.warning(f"Waiting for InfluxDB to be reachable... {e}")
        time.sleep(5)

# Callback for successful MQTT connection
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker successfully")
        client.subscribe(TOPIC)
        logger.info(f"Subscribed to topic pattern: {TOPIC}")
    else:
        logger.critical(f"Failed to connect, return code {rc}")

# Callback for receiving MQTT messages and writing to InfluxDB
def on_message(client, userdata, msg):
    try:
        # Decode the JSON payload
        payload = json.loads(msg.payload.decode())
        logger.debug(f"Raw payload received: {payload}")

        timestamp = payload.get("timestamp", datetime.utcnow().isoformat())

        # Log the received message details
        logger.info(f"Received message from team '{str(payload['team_name'])}' on topic {msg.topic}: {payload}")


        # Convert timestamp to Unix timestamp in nanoseconds
        timestamp_dt = datetime.fromisoformat(payload['timestamp'])
        timestamp_ns = int(timestamp_dt.timestamp() * 1e9)  # Convert to nanoseconds

        # Create a point using values from the payload
        point = (
            Point(str(payload['team_name']))  # Measurement name is the team name
            .time(timestamp_ns, WritePrecision.NS)  # Use the timestamp in nanoseconds
        )

        if 'temperature' in payload:
            point = point.field("temperature", float(payload['temperature']))  # Adding temperature field
            logger.info(f"Temperature: {float(payload['temperature'])}%")
        if 'humidity' in payload:
            point = point.field("humidity", float(payload['humidity']))  # Adding temperature field
            logger.info(f"Humidity: {float(payload['humidity'])}%")
        if 'illumination' in payload:
            point = point.field("illumination", float(payload['illumination']))  # Adding humidity field
            logger.info(f"Illumination: {float(payload['illumination'])}%")

        # Write the point to InfluxDB
        write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, point)
        logger.info("Data written to InfluxDB successfully.")

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON payload")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

# Initialize and configure MQTT client
client = mqtt.Client()
client.username_pw_set(BROKER_USERNAME, BROKER_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker and start listening
client.connect(BROKER_IP, BROKER_PORT, 60)
client.loop_forever()







