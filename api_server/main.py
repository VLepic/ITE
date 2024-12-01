# Importing the libraries
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
import eventlet
from threading import Thread
import os
from joblib import Parallel, delayed
from Read import read, read_latest  # Assuming these functions are properly imported
from datetime import datetime
from approutes.RESTAPI import *
import threading

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
numeric_level = getattr(logging, log_level, logging.INFO)
logging.basicConfig(
    level=numeric_level,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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
RESTAPI_route(app)
latest_RESTAPI_route(app)

@socketio.on('connect')
def handle_connect():
    logging.info(f'Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logging.info(f'Client {request.sid} disconnected')

    # Remove client from all subscribed measurements and teams
    with thread_lock:
        for (measurement, team), client_set in clients.items():
            if request.sid in client_set:
                client_set.remove(request.sid)
                logging.info(f'Client {request.sid} unsubscribed from {measurement} - {team}')

clients = {}
thread_lock = threading.Lock()

# Weather socket update loop
def weather_socket(socketio):
    """Function to send updates for specific measurements and teams to subscribed clients."""
    logging.info('Running weather socket updates')
    entity_ids = {
        ("temperature", "black"): "temperature_team1",
        ("humidity", "black"): "humidity_team1",
        ("illumination", "black"): "humidity_team1",
        ("temperature", "blue"): "temperature_team_blue",
        ("humidity", "blue"): "humidity_team_blue",
        ("illumination", "blue"): "illumination_team_blue",
        ("temperature", "green"): "temperature_team_green",
        ("humidity", "green"): "humidity_team_green",
        ("illumination", "green"): "illumination_team_green",
        ("temperature", "pink"): "temperature_team_pink",
        ("humidity", "pink"): "humidity_team_pink",
        ("illumination", "pink"): "illumination_team_pink",
        ("temperature", "red"): "temperature_team_red",
        ("humidity", "red"): "humidity_team_red",
        ("illumination", "red"): "illumination_team_red",
        ("temperature", "yellow"): "temperature_team_yellow",
        ("humidity", "yellow"): "humidity_team_yellow",
        ("illumination", "yellow"): "illumination_team_yellow"
    }
    last_times = {key: None for key in entity_ids}

    while True:
        with thread_lock:
            if all(len(client_set) == 0 for client_set in clients.values()):
                eventlet.sleep(5)
                continue

        for (measurement, team), entity_id in entity_ids.items():
            try:
                time_values, measurement_values = read_latest(
                    INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team, measurement, "value", "-60h"
                )
            except Exception as e:
                logging.critical(f'Error fetching latest data for {measurement} - {team}: {e}')
                socketio.emit('error', {'message': f'Error fetching latest data for {measurement} - {team}'})
                continue
            if time_values and measurement_values:
                latest_time = time_values[0]
                if last_times[(measurement, team)] is None or latest_time != last_times[(measurement, team)]:
                    data = {
                        'measurement': measurement,
                        'team': team,
                        'time_values': [latest_time.isoformat()],
                        'measurement_values': measurement_values
                    }
                    last_times[(measurement, team)] = latest_time

                    # Emit data only to clients subscribed to this measurement and team
                    with thread_lock:
                        for client in clients.get((measurement, team), []):
                            logging.info(f'Sending {measurement} update for team {team} to client {client}')
                            socketio.emit(f'{measurement}_update', data, to=client)

        eventlet.sleep(1)  # Repeat every second

# Manage client subscriptions
@socketio.on('subscribe')
def handle_subscribe(data):
    global clients
    measurement = data.get('measurement')
    team = data.get('team')
    if (measurement, team) not in clients:
        clients[(measurement, team)] = set()
    with thread_lock:
        clients[(measurement, team)].add(request.sid)
    logging.info(f'Client {request.sid} subscribed to {measurement} - {team}')
    # Send immediate data upon subscription
    try:
        send_initial_data(measurement, team, request.sid)
    except KeyError as e:
        logging.error(f'Error: {e} - The session {request.sid} is disconnected')

def send_initial_data(measurement, team, sid):
    logging.info(f'Sending initial data to {sid} for {measurement} - {team}')
    """Send the initial data for a measurement after subscribing."""

    try:
        time_values, measurement_values = read_latest(
            INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team, measurement, "value", "-60h"
        )
    except Exception as e:
        logging.critical(f'Error fetching initial data for {measurement} - {team}: {e}')
        socketio.emit('error', {'message': f'Error fetching initial data for {measurement} - {team}'})
        return
    if time_values and measurement_values:
        data = {
            'measurement': measurement,
            'team': team,
            'time_values': [time_values[0].isoformat()],
            'measurement_values': measurement_values
        }
        socketio.emit(f'{measurement}_update', data, to=sid)

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









