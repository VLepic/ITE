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

# Helper function to validate payload data
def validate_payload(payload):
    try:
        team_name = payload.get("team_name", "unknown")
        temperature = float(payload["temperature"]) if "temperature" in payload else None
        humidity = float(payload["humidity"]) if "humidity" in payload else None
        illumination = float(payload["illumination"]) if "illumination" in payload else None

        if not isinstance(team_name, str):
            raise ValueError("Invalid team_name")
        if temperature is None:
            raise ValueError("Temperature data missing")

        return team_name, temperature, humidity, illumination
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error: {e}")
        return None

# Callback for receiving MQTT messages and writing to InfluxDB
def on_message(client, userdata, msg):
    try:
        # Decode the JSON payload
        payload = json.loads(msg.payload.decode())
        logger.debug(f"Raw payload received: {payload}")

        # Validate and parse payload
        result = validate_payload(payload)
        if result is None:
            logger.error("Invalid payload, skipping InfluxDB write.")
            return

        team_name, temperature, humidity, illumination = result
        timestamp = payload.get("timestamp", datetime.utcnow().isoformat())

        # Log the received message details
        logger.info(f"Received message from team '{team_name}' on topic {msg.topic}: {payload}")
        logger.info(f"Parsed Data - Team: {team_name}, Timestamp: {timestamp}, Temperature: {temperature}°C")

        if humidity is not None:
            logger.info(f"Humidity: {humidity}%")
        if illumination is not None:
            logger.info(f"Illumination: {illumination} lux")
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)

        # Convert timestamp to Unix timestamp in nanoseconds
        timestamp_dt = datetime.fromisoformat(payload['timestamp'])
        timestamp_ns = int(timestamp_dt.timestamp() * 1e9)  # Convert to nanoseconds

        # Create a point using values from the payload
        point = (
            Point(str(payload['team_name']))  # Measurement name is the team name
            .field("temperature", float(payload['temperature']))  # Adding temperature field
            .field("humidity", float(payload['humidity']))  # Adding humidity field
            .time(timestamp_ns, WritePrecision.NS)  # Use the timestamp in nanoseconds
        )


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







