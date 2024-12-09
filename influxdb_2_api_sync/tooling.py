import pytz
from datetime import datetime
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client import *

def convert_to_utc_plus_one(timestamp: str) -> str:

    # Parse the original UTC timestamp
    utc_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")

    # Set timezone to UTC
    utc_time = utc_time.replace(tzinfo=pytz.UTC)

    # Convert to UTC+1 timezone
    local_time = utc_time.astimezone(pytz.timezone("Europe/Paris"))

    # Format the timestamp to the desired format
    formatted_timestamp = local_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + local_time.strftime("%z")
    formatted_timestamp = formatted_timestamp[:-2] + ':' + formatted_timestamp[-2:]

    return formatted_timestamp

