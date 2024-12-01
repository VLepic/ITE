import logging
import requests
from typing import Dict, List, Optional
from tqdm import tqdm


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
        except requests.RequestException as req_err:
            logging.error(f"Request error occurred during POST to {endpoint}: {req_err}")
        except ValueError as val_err:
            logging.error(f"Error decoding JSON response for POST to {endpoint}: {val_err}")
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
                logging.info("Login successful. Team UUID set.")
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



