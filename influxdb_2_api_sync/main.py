import os
import sys
import time

import tooling
from tqdm import tqdm
from ITE_2024_api_handlerv2 import *
from tooling import *
import Read
import logging
import pprint
import pytz
from datetime import datetime
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client import *
import ujson
from datetime import datetime, timedelta, timezone
from time_lib import *

with open("sync_config.json") as f:
    secrets = ujson.load(f)


BASE_URL = secrets["BASE_URL"]
AIMTEC_USERNAME = secrets["AIMTEC_USERNAME"]
AIMTEC_PASSWORD = secrets["AIMTEC_PASSWORD"]
log_level = secrets["LOG_LEVEL"].upper()
INFLUXDB_URL=secrets["INFLUXDB_URL"]
INFLUXDB_TOKEN=secrets["INFLUXDB_TOKEN"]
INFLUXDB_ORG=secrets["INFLUXDB_ORG"]
INFLUXDB_BUCKET=secrets["INFLUXDB_BUCKET"]
TEAM_NAME = secrets["TEAM_NAME"]
MEASUREMENTS_TO_SYNC=["temperature","humidity","illumination"]
WRITE_TO_OPTIONS=["BOTH","ONLY_INFLUXDB","ONLY_API"]
INTERVAL_SECONDS=secrets["INTERVAL_SECONDS"]
WRITE_TO_SELECTED=secrets["WRITE_TO_SELECTED"]
numeric_level = getattr(logging, log_level, logging.INFO)

influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

logging.basicConfig(
    level=numeric_level,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
with open("UUIDs.json") as f:
    UUIDs = ujson.load(f)

api = ITE_2024_APIv2(base_url=BASE_URL, username=AIMTEC_USERNAME, password=AIMTEC_PASSWORD, temperature_sensor_uuid=UUIDs["temperature"], humidity_sensor_uuid=UUIDs["humidity"], illumination_sensor_uuid=UUIDs["illumination"])

def sync_influxdb_to_api(NOT_IN_INFLUXDB, measurement):
    for formatted_timestamp, measurement_value in tqdm(zip(NOT_IN_INFLUXDB[0], NOT_IN_INFLUXDB[1]),desc=f"[{measurement}]: Syncing influxdb to API",total=len(NOT_IN_INFLUXDB[0])):
        write_to_InfluxDB(formatted_timestamp, measurement, measurement_value)


def sync_api_to_influxdb(NOT_IN_API, measurement):
    for formatted_timestamp, measurement_value in tqdm(zip(NOT_IN_API[0], NOT_IN_API[1]), desc=f"[{measurement}]: Syncing API to influxdb", total=len(NOT_IN_API[0])):
        api.createMeasurement(UUIDs[measurement], formatted_timestamp, measurement_value, "TEST")

def write_to_InfluxDB(timestamp: str, measurement: str, value):
    timestamp_dt = datetime.fromisoformat(timestamp)
    timestamp_ns = int(timestamp_dt.timestamp() * 1e9)  # Convert to nanoseconds

    # Create a point using values from the payload
    point = (
        Point(str(TEAM_NAME))  # Measurement name is the team name
        .time(timestamp_ns, WritePrecision.NS)  # Use the timestamp in nanoseconds
    )

    if 'temperature' == measurement:
        temperature_point = point.field("value", round(float(value), 2))
        # temperature_point = temperature_point.field("datetime", payload['timestamp'])
        temperature_point = temperature_point.tag("sensor", "temperature")
        write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, temperature_point)

    if 'humidity' == measurement:
        humidity_point = point.field("value", round(float(value), 1))
        # humidity_point = humidity_point.field("datetime", payload['timestamp'])
        humidity_point = humidity_point.tag("sensor", "humidity")
        write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, humidity_point)

    if 'illumination' == measurement:
        illumination_point = point.field("value", round(float(value), 1))
        # illumination_point = illumination_point.field("datetime", payload['timestamp'])
        illumination_point = illumination_point.tag("sensor", "illumination")
        write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, illumination_point)

def sync(measurement, write_to_option, time_from, time_to, api_datapoints):

    NOT_IN_INFLUXDB = [[],[]]
    NOT_IN_API = [[],[]]

    IN_API = [[],[]]
    IN_INFLUXDB = [[],[]]


    InfluxDB_raw_time_values_local, InfluxDB_raw_measurement_values = Read.read(INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET, TEAM_NAME, measurement, "value",time_from, time_to)


    print(len(InfluxDB_raw_time_values_local), len(api_datapoints))

    # PROCESSING VALUES TO COMMON TIME FORMAT
    # Process InfluxDB values
    InfluxDB_formatted_time_values = []
    for InfluxDB_raw_time_value, InfluxDB_raw_measurement_value in tqdm(
            zip(InfluxDB_raw_time_values_local, InfluxDB_raw_measurement_values), desc=f"[{measurement}]: Processing InfluxDB values", total=len(InfluxDB_raw_time_values_local)):
        InfluxDB_formatted_timestamp = InfluxDB_raw_time_value.strftime('%Y-%m-%dT%H:%M:%S.%f')[
                                       :-3] + InfluxDB_raw_time_value.strftime('%z')
        InfluxDB_formatted_time_values.append(
            InfluxDB_formatted_timestamp[:-2] + ':' + InfluxDB_formatted_timestamp[-2:])
    IN_INFLUXDB[0] = InfluxDB_formatted_time_values
    IN_INFLUXDB[1] = InfluxDB_raw_measurement_values

    # Process API values
    if api_datapoints:
        api_raw_time_values = []
        api_raw_measurement_values = []
        for datapoint in tqdm(api_datapoints, desc=f"[{measurement}]: Processing API values", total=len(api_datapoints)):
            api_raw_time_values.append(convert_to_utc_plus_one(datapoint["createdOn"]))
            api_raw_measurement_values.append(datapoint["temperature"])
        IN_API[0] = api_raw_time_values
        IN_API[1] = api_raw_measurement_values

    #COMPARING DATA
    #Sync API to InfluxDB
    time_value_not_in_api = []
    measurement_not_in_api = []
    for InfluxDB_formatted_time_value, InfluxDB_measurement_value in tqdm(zip(IN_INFLUXDB[0], IN_INFLUXDB[1]), desc=f"[{measurement}]: Looking for missing values in API", total=len(IN_INFLUXDB[0])):
        if InfluxDB_formatted_time_value not in IN_API[0]:
            time_value_not_in_api.append(InfluxDB_formatted_time_value)
            measurement_not_in_api.append(InfluxDB_measurement_value)
    NOT_IN_API[0] = time_value_not_in_api
    NOT_IN_API[1] = measurement_not_in_api

    # Sync InfluxDB to API
    time_value_not_in_influxdb = []
    measurement_not_in_influxdb = []
    for API_formatted_time_value, API_measurement_value in tqdm(zip(IN_API[0], IN_API[1]), desc=f"[{measurement}]: Looking for missing values in InfluxDB", total=len(IN_API[0])):
        if API_formatted_time_value not in IN_INFLUXDB[0]:
            time_value_not_in_influxdb.append(API_formatted_time_value)
            measurement_not_in_influxdb.append(API_measurement_value)
    NOT_IN_INFLUXDB[0] = time_value_not_in_influxdb
    NOT_IN_INFLUXDB[1] = measurement_not_in_influxdb

    logging.info(f"[{measurement}]: Records not in API: {len(NOT_IN_API[0])}")
    logging.info(f"[{measurement}]: Records not in INFLUXDB: {len(NOT_IN_INFLUXDB[0])}")

    #SYNC
    if write_to_option == "BOTH" or write_to_option == "API":
        sync_api_to_influxdb(NOT_IN_API, measurement)
    if write_to_option == "BOTH" or write_to_option == "INFLUXDB":
        sync_influxdb_to_api(NOT_IN_INFLUXDB, measurement)

def execute_periodically(interval):
    while True:


        while not api.login():
            logging.info("Attempting to log in to API...")
            time.sleep(2)
        temp_data = api.readAllMeasurements_from_single_sensor_by_type("temperature")
        hum_data = api.readAllMeasurements_from_single_sensor_by_type("humidity")
        ill_data = api.readAllMeasurements_from_single_sensor_by_type("illumination")
        data = {"temperature": temp_data, "humidity": hum_data, "illumination": ill_data}
        first_date_api = find_first_date(temp_data, hum_data, ill_data)
        first_date_influxdb = Read.get_first_record_datetime(INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET, TEAM_NAME, "illumination", "value").isoformat().replace("+01:00", "Z")
        start, end = get_date_range(find_earliest_datetime([first_date_api, first_date_influxdb]), datetime.now(timezone(timedelta(hours=1))).isoformat(timespec='seconds').replace('+01:00', 'Z'))

        print(end)

        for start_date, end_date in zip(start, end):
            print(f"{start_date} - {end_date}")
            for measurement_to_sync in MEASUREMENTS_TO_SYNC:
                sync(measurement_to_sync, WRITE_TO_SELECTED.upper(), start_date, end_date, filter_data_by_date_range(data[measurement_to_sync], start_date, end_date))
        time.sleep(interval)




execute_periodically(INTERVAL_SECONDS)







