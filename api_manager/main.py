# Importing the libraries
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import eventlet
import os
from datetime import datetime
import ujson
from approutes.Aimtec import *
from Read import read, read_latest

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
numeric_level = getattr(logging, log_level, logging.INFO)
logging.basicConfig(
    level=numeric_level,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configuration
BASE_URL = "https://ro7uabkugk.execute-api.eu-central-1.amazonaws.com/Prod"
INFLUXDB_URL = "http://influxdb:8086"
INFLUXDB_TOKEN = os.environ.get('DOCKER_INFLUXDB_INIT_API_SERVER_TOKEN', 'default-influxdb-token')
ORG = os.environ.get('DOCKER_INFLUXDB_INIT_ORG', 'default-influxdb-org')
BUCKET = os.environ.get('DOCKER_INFLUXDB_INIT_BUCKET', 'default-influxdb-bucket')

# Initialize Flask app
eventlet.monkey_patch()
app = Flask(__name__)
CORS(app)

# Initialize SocketIO for WebSocket support
socketio = SocketIO(app, ping_timeout=60, ping_interval=30, cors_allowed_origins="*")

# Data routes
getalerts_route(app)
change_boundaries_route(app)
get_boundaries_route(app)


@socketio.on('connect')
def handle_connect():
    logging.info(f'Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    logging.info(f"Client disconnected")


# Weather socket update loop
def weather_socket(socketio):
    logging.info('Starting weather socket updates')
    last_times = {measurement: None for measurement in ['temperature', 'humidity', 'illumination']}

    while True:
        try:
            measurements = ['temperature', 'humidity', 'illumination']
            team = 'pink'

            for measurement in measurements:
                try:
                    # Fetch boundaries for the current measurement
                    boundaries = get_sensor_boundaries(measurement)
                    if 'error' in boundaries:
                        logging.error(f"Error fetching boundaries for {measurement}: {boundaries['error']}")
                        continue

                    low_value = float(boundaries['lowValue'])
                    high_value = float(boundaries['highValue'])

                    # Fetch the latest measurement data
                    time_values, measurement_values = read_latest(
                        INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team, measurement, "value", "-1h"
                    )
                    if not time_values or not measurement_values:
                        logging.warning(f"No data available for {measurement}")
                        continue

                    latest_time = time_values[0]  # Latest timestamp
                    latest_value = measurement_values[0]  # Latest value

                    # Check if the timestamp is newer than the last processed timestamp
                    if last_times[measurement] != latest_time:
                        last_times[measurement] = latest_time  # Update the last timestamp

                        # Check if the value is out of bounds
                        if latest_value < low_value or latest_value > high_value:
                            logging.info(f"Alert: {measurement} value {latest_value} out of bounds ({low_value}-{high_value})")
                            alert = {
                                'measurement': measurement,
                                'team': team,
                                'value': latest_value,
                                'time': latest_time.isoformat(),
                                'minValue': low_value,
                                'maxValue': high_value,
                                'alert': f"Value {latest_value} is out of bounds ({low_value}-{high_value})"
                            }
                            # Emit alert to all connected clients
                            socketio.emit(f'{measurement}_alert', alert)

                except Exception as e:
                    logging.error(f"Error processing {measurement}: {e}")

            # Pause before next iteration
            eventlet.sleep(5)

        except Exception as e:
            logging.critical(f"Critical error in weather_socket loop: {e}")
            eventlet.sleep(5)  # Prevent tight error loops


def get_sensor_boundaries(sensor_type):
    if sensor_type not in ["temperature", "humidity", "illumination"]:
        return {'error': 'Invalid sensor type'}

    sensorUUIDs = {
        "temperature": os.environ.get('sensorUUID_TEMPERATURE'),
        "humidity": os.environ.get('sensorUUID_HUMIDITY'),
        "illumination": os.environ.get('sensorUUID_ILLUMINATION')
    }

    api = ITE_2024_API(BASE_URL, os.environ.get('AIMTEC_USERNAME'), os.environ.get('AIMTEC_PASSWORD'))
    try:
        api.login()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            return {'error': 'Bad login'}
        elif e.response.status_code == 500:
            return {'error': 'Failed to create API connection'}
        else:
            return {'error': f"Unexpected error: {e}"}

    sensors = api.readAllSensors()
    target_sensor_UUID = sensorUUIDs[sensor_type]
    target_sensor = next((s for s in sensors if s["sensorUUID"] == target_sensor_UUID), None)

    if not target_sensor:
        return {'error': 'Failed to find sensor'}

    return {
        'lowValue': target_sensor.get("minTemperature", 0),
        'highValue': target_sensor.get("maxTemperature", 0)
    }


# Error handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '404 Not found', 'message': 'This route is not available. Please check your URL.'}), 404


logging.info('Starting weather socket thread...')
eventlet.spawn(weather_socket, socketio)
logging.info('Weather socket thread started.')

# Entry point
if __name__ == '__main__':
    logging.info('Starting Flask app with SocketIO...')
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, ping_timeout=20, ping_interval=5)
    logging.info('Flask app started')










