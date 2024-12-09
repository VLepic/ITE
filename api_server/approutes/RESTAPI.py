"""Route for retrieving outdoor temperature data from InfluxDB"""
from influxdb_client import InfluxDBClient
import os
from threading import Thread
from flask import jsonify, request
from flask_socketio import SocketIO
import eventlet
from Read import read, read_latest, count_all_datapoints
from datetime import datetime
import logging

def RESTAPI_route(app):

    @app.route('/<team_name>/<measurement>', methods=['GET'])
    def get_data(team_name, measurement):
        INFLUXDB_URL = "http://influxdb:8086"
        INFLUXDB_TOKEN = os.environ.get('DOCKER_INFLUXDB_INIT_API_SERVER_TOKEN', 'default-influxdb-token')
        ORG = os.environ.get('DOCKER_INFLUXDB_INIT_ORG', 'default-influxdb-org')
        BUCKET = os.environ.get('DOCKER_INFLUXDB_INIT_BUCKET', 'default-influxdb-bucket')
        field = "value"

        if not is_team_in_database(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name):
            return jsonify({'error': 'Team not found in the database'}), 404
        if not is_measurement_in_database(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name, "sensor", measurement):
            return jsonify({'error': 'Measurement not found in the database'}), 404


        # Retrieve start and stop time arguments from the request URL parameters
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        logging.info(f'Received request for {team_name} {measurement} data between {start_time} and {end_time}')

        # Check if start_time and end_time are provided in the request, otherwise return error message
        if not start_time or not end_time:
            return jsonify({'error': 'Please provide start_time and end_time parameters in the URL'}), 400

        # Fetch data for temperature within the specified time range
        try:
            time_values, measurement_values = read(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name, measurement, field, start_time, end_time)
        except Exception as InfluxDBReadError:
            logging.critical(f"Error fetching data for {team_name} {measurement}: {InfluxDBReadError}")
            return jsonify({'500 Server error': 'An error occurred while fetching data from InfluxDB'}), 500
        # Convert datetime objects to ISO 8601 format
        time_values_iso = [time.isoformat() for time in time_values]

        return jsonify({'time_values': time_values_iso, 'measurement_values': measurement_values}), 200


def latest_RESTAPI_route(app):

    @app.route('/<team_name>/<measurement>/latest', methods=['GET'])
    def get_latest_data(team_name, measurement):
        INFLUXDB_URL = "http://influxdb:8086"
        INFLUXDB_TOKEN = os.environ.get('DOCKER_INFLUXDB_INIT_API_SERVER_TOKEN', 'default-influxdb-token')
        ORG = os.environ.get('DOCKER_INFLUXDB_INIT_ORG', 'default-influxdb-org')
        BUCKET = os.environ.get('DOCKER_INFLUXDB_INIT_BUCKET', 'default-influxdb-bucket')
        field = "value"

        if not is_team_in_database(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name):
            return jsonify({'error': 'Team not found in the database'}), 404
        if not is_measurement_in_database(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name, "sensor", measurement):
            return jsonify({'error': 'Measurement not found in the database'}), 404

        logging.info(f'Received request for latest {team_name} {measurement}')

        # Fetch data for temperature within the specified time range
        try:
            time_values, measurement_values = read_latest(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name, measurement, field,
                                                          "-60h")
        except Exception as InfluxDBReadError:
            logging.critical(f"Error fetching data for latest {team_name} {measurement}: {InfluxDBReadError}")
            return jsonify({'500 Server error': 'An error occurred while fetching data from InfluxDB'}), 500
        # Convert datetime objects to ISO 8601 format
        time_values_iso = [time.isoformat() for time in time_values]

        return jsonify({'time_values': time_values_iso, 'measurement_values': measurement_values}), 200

def static_info_RESTAPI_route(app):
    @app.route('/static_info', methods=['GET'])
    def get_static_info():
        return jsonify({"ESP8266" : "30.10.2024", "DHT22": "30.10.2024", "BH1750": "21.11.2024", "RTC DS3231 AT24C32": "21.11.2024"})

def metadata_RESTAPI_route(app):

    @app.route('/<team_name>/metadata', methods=['GET'])
    def get_metadata(team_name):
        measurements = ['temperature', 'humidity', 'illumination']
        measurement_exist = []
        INFLUXDB_URL = "http://influxdb:8086"
        INFLUXDB_TOKEN = os.environ.get('DOCKER_INFLUXDB_INIT_API_SERVER_TOKEN', 'default-influxdb-token')
        ORG = os.environ.get('DOCKER_INFLUXDB_INIT_ORG', 'default-influxdb-org')
        BUCKET = os.environ.get('DOCKER_INFLUXDB_INIT_BUCKET', 'default-influxdb-bucket')
        field = "value"

        if not is_team_in_database(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name):
            return jsonify({'error': 'Team not found in the database'}), 404


        logging.info(f'Received request for {team_name} metadata')
        is_teamperature = is_measurement_in_database(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name, "sensor", "temperature")
        is_humidity = is_measurement_in_database(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name, "sensor", "humidity")
        is_illumination = is_measurement_in_database(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name, "sensor", "illumination")

        count_temperature = 0
        count_humidity = 0
        count_illumination = 0

        if is_teamperature:
            count_temperature = count_all_datapoints(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name, "temperature", field)
        if is_humidity:
            count_humidity = count_all_datapoints(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name, "humidity", field)
        if is_illumination:
            count_illumination = count_all_datapoints(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name, "illumination", field)


        return jsonify({'team name': f'{team_name}',
                        'temperature': is_measurement_in_database(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name, "sensor", "temperature"),
                        'humidity': is_measurement_in_database(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name, "sensor", "humidity"),
                        'illumination': is_measurement_in_database(INFLUXDB_URL, INFLUXDB_TOKEN, ORG, BUCKET, team_name, "sensor", "illumination"),
                        'num_of_temperature_datapoints': count_temperature,
                        'num_of_humidity_datapoints': count_humidity,
                        'num_of_illumination_datapoints': count_illumination
                        }), 200




def is_measurement_in_database(url: str, token: str, org: str, bucket: str, team: str, tag_key: str, tag_value: str) -> bool:
    client = InfluxDBClient(url=url, token=token, org=org)

    # Flux dotaz
    flux_query = f'''
    from(bucket: "{bucket}")
      |> range(start: -1000h) 
      |> filter(fn: (r) => r._measurement == "{team}")
      |> keep(columns: ["{tag_key}"])
      |> distinct(column: "{tag_key}")
    '''

    # Dotazování pomocí QueryApi
    query_api = client.query_api()
    result = query_api.query(flux_query)

    # Zpracování výsledků a ověření přítomnosti tag_value
    contains_value = any(record.values.get(tag_key) == tag_value for table in result for record in table.records)

    # Uzavření klienta
    client.close()

    return contains_value


def is_team_in_database(url: str, token: str, org: str, bucket: str, team: str) -> bool:
    client = InfluxDBClient(url=url, token=token, org=org)

    # Flux dotaz pro získání všech měření (_measurements)
    flux_query = f'''
    import "influxdata/influxdb/schema"
    schema.measurements(bucket: "{bucket}")
    '''

    # Dotazování pomocí QueryApi
    query_api = client.query_api()
    result = query_api.query(flux_query)


    # Zpracování výsledků a ověření přítomnosti měření (team)
    contains_team = any(record.get_value() == team for table in result for record in table.records)

    # Uzavření klienta
    client.close()

    return contains_team