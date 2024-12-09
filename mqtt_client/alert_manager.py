import ITE_2024_api_handler

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
            self.api = ITE_2024_api_handler.ITE_2024_API(self.BASE_URL, self.AIMTEC_USERNAME, self.AIMTEC_PASSWORD)
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