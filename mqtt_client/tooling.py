import pytz
from datetime import datetime, timezone, timedelta
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client import *

def convert_to_utc_plus_one(timestamp: str) -> str:
    """
    Convert a UTC timestamp to UTC+1 timezone with the format 'YYYY-MM-DDTHH:MM:SS.mmm+01:00'.

    Args:
        timestamp (str): The original timestamp in UTC, e.g., '2024-11-14T01:46:19.000Z'.

    Returns:
        str: The converted timestamp in UTC+1 timezone with the format 'YYYY-MM-DDTHH:MM:SS.mmm+01:00'.
    """
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

def convert_ns_to_iso8601(timestamp_ns: int, offset_hours=1) -> str:
    # Convert nanoseconds to seconds
    timestamp_s = timestamp_ns / 1e9
    # Create a datetime object from the timestamp in UTC
    dt_utc = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
    # Apply the timezone offset (e.g., +01:00)
    dt_with_offset = dt_utc + timedelta(hours=offset_hours)
    # Format with millisecond precision and timezone offset
    formatted_timestamp = dt_with_offset.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + f"+{offset_hours:02}:00"
    return formatted_timestamp