from datetime import datetime, timedelta, timezone
import json
import time
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import ujson
from ITE_2024_api_handler import *
import tooling
import alert_manager

# Load configuration from JSON file
with open("mqtt_client_config.json") as f:
    secrets = ujson.load(f)

with open("UUIDs.json") as f:
    UUIDs = ujson.load(f)

BROKER_IP = secrets["BROKER_IP"]
BROKER_PORT = secrets["BROKER_PORT"]
BROKER_USERNAME = secrets["BROKER_USERNAME"]
BROKER_PASSWORD = secrets["BROKER_PASSWORD"]
INFLUXDB_URL = secrets["INFLUXDB_URL"]
INFLUXDB_TOKEN = secrets["INFLUXDB_TOKEN"]
INFLUXDB_ORG = secrets["INFLUXDB_ORG"]
INFLUXDB_BUCKET = secrets["INFLUXDB_BUCKET"]
BASE_URL = secrets["BASE_URL"]
TEAM_NAME = secrets["TEAM_NAME"]
AIMTEC_USERNAME = secrets["AIMTEC_USERNAME"]
AIMTEC_PASSWORD = secrets["AIMTEC_PASSWORD"]
sensorUUID_TEMPERATURE = UUIDs["temperature"]
sensorUUID_HUMIDITY = UUIDs["humidity"]
sensorUUID_ILLUMINATION = UUIDs["illumination"]
LOG_LEVEL = secrets["LOGGING_LEVEL"]
SEND_TO_API = secrets["SEND_TO_API"].lower() == "true"

TEAMS = ["black", "blue", "green", "pink", "red", "yellow"]
api = ITE_2024_API(base_url=BASE_URL, username=AIMTEC_USERNAME, password=AIMTEC_PASSWORD)
alert_manager = alert_manager.alert_manager(AIMTEC_USERNAME, AIMTEC_PASSWORD, BASE_URL, sensorUUID_TEMPERATURE, sensorUUID_HUMIDITY, sensorUUID_ILLUMINATION)

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
if SEND_TO_API:
    while not api.login():
        logger.info("Attempting to login to API...")
        time.sleep(5)

    while not alert_manager.setup():
        logger.info("Attempting to login alert manager to API...")
        time.sleep(5)

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
        for team in TEAMS:
            client.subscribe(f"ite/{team}")
            logger.info(f"Subscribed to topic pattern: ite/{team}")
    else:
        logger.critical(f"Failed to connect, return code {rc}")

# Callback for receiving MQTT messages and writing to InfluxDB
def on_message(client, userdata, msg):
    try:

        payload = json.loads(msg.payload.decode())
        logger.debug(f"Raw payload received: {payload}")


        logger.info(f"Received message from team '{str(payload['team_name'])}' on topic {msg.topic}: {payload}")


        # Convert timestamp to Unix timestamp in nanoseconds
        timestamp_dt = datetime.fromisoformat(payload['timestamp'])
        current_utc = datetime.now(timezone.utc)
        assumed_utc_timestamp = timestamp_dt.replace(tzinfo=timezone.utc)
        delta = current_utc - assumed_utc_timestamp
        if abs(delta.total_seconds()) <= 2300:
            timestamp_dt += timedelta(hours=1)  # Add one hour to the timestamp
        timestamp_ns = int(timestamp_dt.timestamp() * 1e9)  # Convert to nanoseconds
        timestamp_for_api = tooling.convert_ns_to_iso8601(timestamp_ns)
        # Create a point using values from the payload
        point = (
            Point(str(payload['team_name']))
            .time(timestamp_ns, WritePrecision.NS)
        )
        try:
            if SEND_TO_API:
                sensors = api.readAllSensors()
                temperature_sensor = None
                humidity_sensor = None
                illumination_sensor = None
                for sensor in sensors:
                    if sensor["sensorUUID"] == sensorUUID_TEMPERATURE:
                        temperature_sensor = sensor

                    if sensor["sensorUUID"] == sensorUUID_HUMIDITY:
                        humidity_sensor = sensor

                    if sensor["sensorUUID"] == sensorUUID_ILLUMINATION:
                        illumination_sensor = sensor

        except Exception as er:
            logging.critical(f"Error while fetching sensors from api {er} Skipping...")

        if 'temperature' in payload:
            if str(payload['team_name']) == TEAM_NAME and SEND_TO_API:
                try:
                    api.createMeasurement(UUIDs['temperature'], timestamp_for_api, round(float(payload['temperature']), 2), "OK")
                    logger.debug("Temperature data written to API successfully.")
                except Exception as er:
                    logging.critical(f"Error while sending temperature to api {er} Skipping...")

                try:
                    if temperature_sensor["minTemperature"] > float(payload['temperature']) or temperature_sensor["maxTemperature"] < float(payload['temperature']):
                        alert_manager.create_alert("temperature", timestamp_for_api, float(payload['temperature']))
                        logger.warning(f"Temperature alert created for temperature {payload['temperature']}, out of interval: {temperature_sensor['minTemperature']} - {temperature_sensor['maxTemperature']}")
                except Exception as er:
                    logging.critical(f"Error while sending temperature alert to api {er} Skipping...")
            elif not SEND_TO_API:
                logger.warning("Not sending data to API as per configuration")
            temperature_point = point.field("value", round(float(payload['temperature']), 2))
            temperature_point = temperature_point.tag("sensor", "temperature")
            write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, temperature_point)
            logger.info(f"Temperature: {round(float(payload['temperature']), 2)}°C")

        if 'humidity' in payload:
            if str(payload['team_name']) == TEAM_NAME and SEND_TO_API:
                try:
                    api.createMeasurement(UUIDs['humidity'], timestamp_for_api, round(float(payload['humidity']), 2), "OK")
                    logger.debug("Humidity data written to API successfully.")
                except Exception as er:
                    logging.critical(f"Error while sending humidity to api {er} Skipping...")

                try:
                    if humidity_sensor["minTemperature"] > float(payload['humidity']) or humidity_sensor["maxTemperature"] < float(payload['humidity']):
                        alert_manager.create_alert("humidity", timestamp_for_api, float(payload['humidity']))
                        logger.warning(f"Humidity alert created for humidity {payload['humidity']}, out of interval: {humidity_sensor['minTemperature']} - {humidity_sensor['maxTemperature']}")
                except Exception as er:
                    logging.critical(f"Error while sending humidity alert to api {er} Skipping...")
            elif not SEND_TO_API:
                logger.warning("Not sending data to API as per configuration")
            humidity_point = point.field("value", round(float(payload['humidity']), 1))
            humidity_point = humidity_point.tag("sensor", "humidity")
            write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, humidity_point)
            logger.info(f"Humidity: {round(float(payload['humidity']), 1)}%")

        if 'illumination' in payload:
            if str(payload['team_name']) == TEAM_NAME and SEND_TO_API:
                try:
                    api.createMeasurement(UUIDs['illumination'], timestamp_for_api, round(float(payload['illumination']), 2), "OK")
                    logger.debug("Illumination data written to API successfully.")
                except Exception as er:
                    logging.critical(f"Error while sending illumination to api {er} Skipping...")

                try:
                    if illumination_sensor["minTemperature"] > float(payload['illumination']) or illumination_sensor["maxTemperature"] < float(payload['illumination']):
                        alert_manager.create_alert("illumination", timestamp_for_api, float(payload['illumination']))
                        logger.warning(f"Illumination alert created for illumination {payload['illumination']}, out of interval: {illumination_sensor['minTemperature']} - {illumination_sensor['maxTemperature']}")
                except Exception as er:
                    logging.critical(f"Error while sending illumination alert to api {er} Skipping...")
            elif not SEND_TO_API:
                logger.warning("Not sending data to API as per configuration")
            illumination_point = point.field("value", round(float(payload['illumination']), 1))
            illumination_point = illumination_point.tag("sensor", "illumination")
            write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, illumination_point)
            logger.info(f"Illumination: {round(float(payload['illumination']), 1)} lux")

        logger.debug("Data written to InfluxDB successfully.")

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







