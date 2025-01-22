
from influxdb_client import InfluxDBClient
import os
from threading import Thread
from flask import jsonify, request
from flask_socketio import SocketIO
import eventlet
from Read import read, read_latest
from datetime import datetime
import logging
import os
import logging
import requests
from typing import Dict, List, Optional
from tqdm import tqdm
import os
import psycopg2
import secrets

class alert_manager:

    def __init__(self, AIMTEC_USERNAME, AIMTEC_PASSWORD, BASE_URL, sensorUUID_TEMPERATURE, sensorUUID_HUMIDITY, sensorUUID_ILLUMINATION):
        self.BASE_URL = BASE_URL
        self.AIMTEC_USERNAME = AIMTEC_USERNAME
        self.AIMTEC_PASSWORD = AIMTEC_PASSWORD
        self.sensorUUID_TEMPERATURE = sensorUUID_TEMPERATURE
        self.sensorUUID_HUMIDITY = sensorUUID_HUMIDITY
        self.sensorUUID_ILLUMINATION = sensorUUID_ILLUMINATION
        self.temperature_sensor = None
        self.humidity_sensor = None
        self.illumination_sensor = None
        self.api = None

    def setup(self):
        try:
            self.api = ITE_2024_API(self.BASE_URL, self.AIMTEC_USERNAME, self.AIMTEC_PASSWORD)
            self.api.login()
            sensors = self.api.readAllSensors()
            for sensor in sensors:
                if sensor["sensorUUID"] == self.sensorUUID_TEMPERATURE:
                    self.temperature_sensor = sensor

                if sensor["sensorUUID"] == self.sensorUUID_HUMIDITY:
                    self.humidity_sensor = sensor

                if sensor["sensorUUID"] == self.sensorUUID_ILLUMINATION:
                    self.illumination_sensor = sensor

            return True
        except Exception as e:
            print(e)
            return False

    def create_alert(self, sensor_type, timestamp, value):
        sensors = self.api.readAllSensors()
        for sensor in sensors:
            if sensor["sensorUUID"] == self.sensorUUID_TEMPERATURE:
                self.temperature_sensor = sensor

            if sensor["sensorUUID"] == self.sensorUUID_HUMIDITY:
                self.humidity_sensor = sensor

            if sensor["sensorUUID"] == self.sensorUUID_ILLUMINATION:
                self.illumination_sensor = sensor
        if sensor_type == "temperature":
            self.api.createAlert(self.temperature_sensor["sensorUUID"], timestamp, value, self.temperature_sensor["minTemperature"], self.temperature_sensor["maxTemperature"])
        if sensor_type == "humidity":
            self.api.createAlert(self.humidity_sensor["sensorUUID"], timestamp, value, self.humidity_sensor["minHumidity"], self.humidity_sensor["maxHumidity"])
        if sensor_type == "illumination":
            self.api.createAlert(self.illumination_sensor["sensorUUID"], timestamp, value, self.illumination_sensor["minIllumination"], self.illumination_sensor["maxIllumination"])

    def change_boundaries(self, sensor_type, min_value, max_value):
        if sensor_type == "temperature":
            self.api.updateSensor_by_id(self.temperature_sensor["id"], self.temperature_sensor["name"], self.temperature_sensor["location"], min_value, max_value)
        if sensor_type == "humidity":
            self.api.updateSensor_by_id(self.humidity_sensor["id"], self.humidity_sensor["name"], self.humidity_sensor["location"], min_value, max_value)
        if sensor_type == "illumination":
            self.api.updateSensor_by_id(self.illumination_sensor["id"], self.illumination_sensor["name"], self.illumination_sensor["location"], min_value, max_value)

    def read_alerts(self, sensor_type):
        target_alerts = []
        target_sensor = None
        if sensor_type == "temperature":
            target_sensor = self.temperature_sensor
        if sensor_type == "humidity":
            target_sensor = self.humidity_sensor
        if sensor_type == "illumination":
            target_sensor = self.illumination_sensor
        if sensor_type == "all":
            return self.api.readAllAlerts()

        for alert in self.api.readAllAlerts():
            if alert["sensorUUID"] == target_sensor["sensorUUID"]:
                target_alerts.append(alert)

        return target_alerts

    def delete_alert(self, alert_id):
        self.api.deleteAlert_by_id(alert_id)

    def delete_all_alerts(self):
        for alert in self.api.readAllAlerts():
            self.delete_alert(alert["id"])

class ITE_2024_API:
    def __init__(self, base_url: str, username: str, password: str):
        """Initialize API connection."""
        self.base_url = base_url
        self.username = username
        self.password = password
        self.headers = {
            "Content-Type": "application/json"
        }
        self.team_uuid: Optional[str] = None

    def post_(self, endpoint: str, body: Dict) -> Dict:
        """Helper function to send a POST request."""
        try:
            response = requests.post(endpoint, json=body, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            logging.error(f"HTTP error occurred during POST to {endpoint}: {http_err}")
            raise
        except requests.RequestException as req_err:
            logging.error(f"Request error occurred during POST to {endpoint}: {req_err}")
            raise
        except ValueError as val_err:
            logging.error(f"Error decoding JSON response for POST to {endpoint}: {val_err}")
            raise
        return {}

    def get_(self, endpoint: str) -> Dict:
        """Helper function to send a GET request."""
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            logging.error(f"HTTP error occurred during GET from {endpoint}: {http_err}")
        except requests.RequestException as req_err:
            logging.error(f"Request error occurred during GET from {endpoint}: {req_err}")
        except ValueError as val_err:
            logging.error(f"Error decoding JSON response for GET from {endpoint}: {val_err}")
        return {}

    def put_(self, endpoint: str, body: Dict) -> Dict:
        """Helper function to send a PUT request."""
        try:
            response = requests.put(endpoint, json=body, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            logging.error(f"HTTP error occurred during PUT to {endpoint}: {http_err}")
        except requests.RequestException as req_err:
            logging.error(f"Request error occurred during PUT to {endpoint}: {req_err}")
        except ValueError as val_err:
            logging.error(f"Error decoding JSON response for PUT to {endpoint}: {val_err}")
        return {}

    def delete_(self, endpoint: str) -> Dict:
        """Helper function to send a DELETE request."""
        try:
            response = requests.delete(endpoint, headers=self.headers)
            response.raise_for_status()
            return {"message": "Successfully deleted."}
        except requests.HTTPError as http_err:
            logging.error(f"HTTP error occurred during DELETE at {endpoint}: {http_err}")
        except requests.RequestException as req_err:
            logging.error(f"Request error occurred during DELETE at {endpoint}: {req_err}")
        return {}

    def login(self) -> bool:
        """Log into the API and retrieve teamUUID from response."""
        payload = {"username": self.username, "password": self.password}
        response = self.post_(f"{self.base_url}/login", payload)
        if response:
            self.team_uuid = response.get("teamUUID")
            if self.team_uuid:
                self.headers["teamUUID"] = self.team_uuid
                logging.debug("Login successful. Team UUID set.")
                return True
            logging.warning("Login response does not contain teamUUID.")
        logging.error("Login failed.")
        return False

    def readAllSensors(self) -> List[Dict]:
        """Retrieve all sensors."""
        logging.debug("Retrieving all sensors.")
        return self.get_(f"{self.base_url}/sensors")

    def readSingleSensor_by_id(self, sensor_id: str) -> Dict:
        """Retrieve a single sensor by its ID."""
        logging.debug("Retrieving sensor with ID: %s", sensor_id)
        return self.get_(f"{self.base_url}/sensors/{sensor_id}")

    def updateSensor_by_id(self, Sensorid: int, name: str, location: str, minTemperature: float,
                    maxTemperature: float) -> Dict:
        """Update sensor metadata."""
        payload = {
            "name": name,
            "location": location,
            "minTemperature": minTemperature,
            "maxTemperature": maxTemperature
        }
        logging.debug("Updating sensor with payload: %s", payload)
        return self.put_(f"{self.base_url}/sensors/{Sensorid}", payload)

    def readAllMeasurements(self) -> List[Dict]:
        """Retrieve all measurements."""
        logging.debug("Retrieving all measurements.")
        return self.get_(f"{self.base_url}/measurements")

    def readSingleMeasurement_by_id(self, measurement_id: str) -> Dict:
        """Retrieve a single measurement by its ID."""
        logging.debug("Retrieving measurement with ID: %s", measurement_id)
        return self.get_(f"{self.base_url}/measurements/{measurement_id}")

    def readAllMeasurements_from_single_sensor_by_id(self, sensorUUID) -> List[Dict]:
        """Retrieve all measurements from single sensor by its ID."""
        logging.debug(f"Retrieving all measurements from sensor {sensorUUID}.")
        measurements = self.readAllMeasurements()
        correct_measurements = []

        for measurement in measurements:
            if measurement["sensorUUID"] == sensorUUID:
                correct_measurements.append(measurement)
        return correct_measurements

    def createMeasurement(self, sensor_uuid: str, created_on: str, temperature: float, status: str) -> Dict:
        """Create a new measurement for a sensor."""
        payload = {
            "createdOn": created_on,
            "sensorUUID": sensor_uuid,
            "temperature": str(temperature),
            "status": status
        }
        logging.debug("Creating measurement with payload: %s", payload)
        return self.post_(f"{self.base_url}/measurements", payload)

    def updateMeasurement_by_id(self, measurement_id: str, temperature: float) -> Dict:
        """Update an existing measurement by its ID."""
        payload = {
            "temperature": str(temperature)
        }
        logging.debug("Updating measurement %s with temperature: %s", measurement_id, temperature)
        return self.put_(f"{self.base_url}/measurements/{measurement_id}", payload)

    def deleteMeasurement_by_id(self, measurement_uuid: str) -> Dict:
        """Delete a measurement by its UUID."""
        logging.debug("Deleting measurement with ID: %s", measurement_uuid)
        return self.delete_(f"{self.base_url}/measurements/{measurement_uuid}")

    def readAllAlerts(self) -> List[Dict]:
        """Retrieve all alerts."""
        logging.debug("Retrieving all alerts.")
        return self.get_(f"{self.base_url}/alerts")

    def readSingleAlert_by_id(self, alert_id: str) -> Dict:
        """Retrieve a single alert by its ID."""
        logging.debug("Retrieving alert with ID: %s", alert_id)
        return self.get_(f"{self.base_url}/alerts/{alert_id}")

    def createAlert(self, sensor_uuid: str, created_on: str, temperature: float, low_temp: float,
                    high_temp: float) -> Dict:
        """Create a new alert for a sensor."""
        payload = {
            "createdOn": created_on,
            "sensorUUID": sensor_uuid,
            "temperature": temperature,
            "lowTemperature": low_temp,
            "highTemperature": high_temp
        }
        logging.debug("Creating alert with payload: %s", payload)
        return self.post_(f"{self.base_url}/alerts", payload)

    def updateAlert_by_id(self, alert_id: str, high_temp: float) -> Dict:
        """Update an existing alert by setting a new highTemperature."""
        payload = {
            "highTemperature": high_temp
        }
        logging.debug("Updating alert %s with highTemperature: %s", alert_id, high_temp)
        return self.put_(f"{self.base_url}/alerts/{alert_id}", payload)

    def deleteAlert_by_id(self, alert_id: str) -> Dict:
        """Delete an alert by its ID."""
        logging.debug("Deleting alert with ID: %s", alert_id)
        return self.delete_(f"{self.base_url}/alerts/{alert_id}")

    def delete_all_measurements(self):
        """Delete all measurements."""
        masurements = self.readAllMeasurements()
        for measurement in tqdm(masurements):
            self.deleteMeasurement_by_id(measurement["id"])

def getalerts_route(app):

    @app.route('/aimtecapi/alerts/getalerts/<sensor_type>', methods=['GET'])
    def getalerts(sensor_type):
        logging.info(f'GET /aimtecapi/alerts/getalerts/{sensor_type}')
        if sensor_type not in ["temperature", "humidity", "illumination", "all"]:
            return jsonify({'error': 'Invalid sensor type'}), 400

        if not request.args.get('login') or not request.args.get('password'):
            return jsonify({'error': 'Please provide login and password parameters in the URL'}), 400


        BASE_URL = "https://ro7uabkugk.execute-api.eu-central-1.amazonaws.com/Prod"
        AIMTEC_USERNAME = request.args.get('login')
        AIMTEC_PASSWORD = request.args.get('password')
        sensorUUID_TEMPERATURE = os.environ.get('sensorUUID_TEMPERATURE', '27f05ba8-f6fa-4210-8dba-8281d5124e3c')
        sensorUUID_HUMIDITY = os.environ.get('sensorUUID_HUMIDITY', '2772ce03-2fe3-4a42-95f6-f9af10ebe6ce')
        sensorUUID_ILLUMINATION = os.environ.get('sensorUUID_ILLUMINATION', 'fd324f1a-c9c9-49d0-9ecf-c59404710bbf')

        api = ITE_2024_API(BASE_URL, AIMTEC_USERNAME, AIMTEC_PASSWORD)
        alert_m = alert_manager(AIMTEC_USERNAME, AIMTEC_PASSWORD, BASE_URL, sensorUUID_TEMPERATURE, sensorUUID_HUMIDITY, sensorUUID_ILLUMINATION)
        try:
            alert_m.setup()
            api.login()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                logging.error("Bad login.")
                return jsonify({'error': 'Bad login.'}), 400
            elif e.response.status_code == 500:
                logging.error(f"Failed to create api connection. {e}")
                return jsonify({'error': 'Failed to create api connection.'}), 500
            else:
                logging.error(f"Failed to create api connection. {e}")
                return jsonify({'error': 'Failed to create api connection.'}), 500

        time_stamps = []
        alert_values = []
        measurement_type = []
        min_value = []
        max_value = []


        alerts = alert_m.read_alerts(sensor_type)
        for alert in alerts:
            time_stamps.append(alert["timestamp"])
            alert_values.append(alert["temperature"])
            if alert["sensorUUID"] == sensorUUID_TEMPERATURE:
                measurement_type.append("temperature")

            if alert["sensorUUID"] == sensorUUID_HUMIDITY:
                measurement_type.append("humidity")

            if alert["sensorUUID"] == sensorUUID_ILLUMINATION:
                measurement_type.append("illumination")
            min_value.append(alert["lowTemperature"])
            max_value.append(alert["highTemperature"])





        return jsonify({'time_values': time_stamps, 'alert_values': alert_values, 'measurement_type': measurement_type, 'low_value': min_value, 'high_value': max_value}), 200

def change_boundaries_route(app):

    @app.route('/aimtecapi/alerts/changeboundaries/<sensor_type>', methods=['PUT'])
    def change_boundaries(sensor_type):
        import os
        AIMTECPASS = os.environ.get("AIMTEC_PASSWORD")
        conn = psycopg2.connect(
            dbname=os.environ.get("POSTGRES_DB"),
            user=os.environ.get("POSTGRES_USER"),
            password=os.environ.get("POSTGRES_PASSWORD"),
            host=os.environ.get("POSTGRES_HOST", "postgres"),
            port=5432
        )
        cursor = conn.cursor()

        logging.info(f'PUT /aimtecapi/alerts/changeboundaries/{sensor_type}')
        if sensor_type not in ["temperature", "humidity", "illumination"]:
            return jsonify({'error': 'Invalid sensor type'}), 400

        if not request.args.get('min_value') or not request.args.get('max_value'):
            return jsonify({'error': 'Please provide min_value and max_value parameters in the URL'}), 400

        if not request.args.get('login') or not request.args.get('password'):
            return jsonify({'error': 'Please provide login and password parameters in the URL'}), 400

        if float(request.args.get('min_value')) > float(request.args.get('max_value')):
            return jsonify({'error': 'min_value cannot be higher than max_value'}), 400

        BASE_URL = "https://ro7uabkugk.execute-api.eu-central-1.amazonaws.com/Prod"
        AIMTEC_USERNAME = request.args.get('login')
        AIMTEC_PASSWORD = request.args.get('password')
        sensorUUID_TEMPERATURE = "27f05ba8-f6fa-4210-8dba-8281d5124e3c"
        sensorUUID_HUMIDITY = "2772ce03-2fe3-4a42-95f6-f9af10ebe6ce"
        sensorUUID_ILLUMINATION = "fd324f1a-c9c9-49d0-9ecf-c59404710bbf"

        cursor.execute("SELECT 1 FROM login_tokens WHERE logintoken = %s LIMIT 1;", (AIMTEC_PASSWORD,))
        token_present = cursor.fetchone() is not None

        if(token_present):
            AIMTEC_PASSWORD = AIMTECPASS

        api = ITE_2024_API(BASE_URL, AIMTEC_USERNAME, AIMTEC_PASSWORD)
        alert_m = alert_manager(AIMTEC_USERNAME, AIMTEC_PASSWORD, BASE_URL, sensorUUID_TEMPERATURE, sensorUUID_HUMIDITY, sensorUUID_ILLUMINATION)
        try:
            alert_m.setup()
            api.login()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                logging.error("Bad login.")
                return jsonify({'error': 'Bad login.'}), 400
            elif e.response.status_code == 500:
                logging.error(f"Failed to create api connection. {e}")
                return jsonify({'error': 'Failed to create api connection.'}), 500
            else:
                logging.error(f"Failed to create api connection. {e}")
                return jsonify({'error': 'Failed to create api connection.'}), 500

        alert_m.change_boundaries(sensor_type, request.args.get('min_value'), request.args.get('max_value'))

        return jsonify({'message': 'Boundaries changed successfully'}), 200

def get_boundaries_route(app):

    @app.route('/aimtecapi/alerts/getboundaries/<sensor_type>', methods=['GET'])
    def get_boundaries(sensor_type):
        logging.info(f'GET /aimtecapi/alerts/getboundaries/{sensor_type}')
        if sensor_type not in ["temperature", "humidity", "illumination"]:
            return jsonify({'error': 'Invalid sensor type'}), 400


        BASE_URL = "https://ro7uabkugk.execute-api.eu-central-1.amazonaws.com/Prod"
        AIMTEC_USERNAME = os.environ.get('AIMTEC_USERNAME')
        AIMTEC_PASSWORD = os.environ.get('AIMTEC_PASSWORD')
        sensorUUID_TEMPERATURE = os.environ.get('sensorUUID_TEMPERATURE')
        sensorUUID_HUMIDITY = os.environ.get('sensorUUID_HUMIDITY')
        sensorUUID_ILLUMINATION = os.environ.get('sensorUUID_ILLUMINATION')

        api = ITE_2024_API(BASE_URL, AIMTEC_USERNAME, AIMTEC_PASSWORD)

        try:
            api.login()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                logging.error("Bad login.")
                return jsonify({'error': 'Bad login.'}), 400
            elif e.response.status_code == 500:
                logging.error(f"Failed to create api connection. {e}")
                return jsonify({'error': 'Failed to create api connection.'}), 500
            else:
                logging.error(f"Failed to create api connection. {e}")
                return jsonify({'error': 'Failed to create api connection.'}), 500

        sensors = api.readAllSensors()
        target_sensor = None
        target_sensor_UUID = None
        if sensor_type == "temperature":
            target_sensor_UUID = sensorUUID_TEMPERATURE
        if sensor_type == "humidity":
            target_sensor_UUID = sensorUUID_HUMIDITY
        if sensor_type == "illumination":
            target_sensor_UUID = sensorUUID_ILLUMINATION


        for sensor in sensors:
            if sensor["sensorUUID"] == target_sensor_UUID:
                target_sensor = sensor
        if not target_sensor:
            return jsonify({'error': 'Failed to find sensor'}), 500

        return jsonify({'lowValue': f'{target_sensor["minTemperature"]}', 'highValue': f'{target_sensor["maxTemperature"]}'}), 200
