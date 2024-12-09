import ITE_2024_api_handlerv2
import pprint
import logging
from datetime import datetime, timedelta

def is_date_in_range(start_date: str, end_date: str, input_date: str) -> bool:
    # Convert strings to datetime objects
    start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    input_dt = datetime.fromisoformat(input_date.replace("Z", "+00:00"))

    # Check if the input_date is within the range [start, end]
    return start <= input_dt <= end

def find_latest_date(temp_data, hum_data, ill_data) -> str:
    dates = [data["createdOn"] for data in (temp_data + hum_data + ill_data)]

    # Convert strings to datetime objects
    datetime_objects = [datetime.fromisoformat(date.replace("Z", "+00:00")) for date in dates]

    # Find the latest datetime
    latest_datetime = max(datetime_objects)

    # Return the latest date as a string in ISO 8601 format
    return latest_datetime.isoformat().replace("+00:00", "Z")

def find_first_date(temp_data, hum_data, ill_data) -> str:
    dates = [data["createdOn"] for data in (temp_data + hum_data + ill_data)]

    # Convert strings to datetime objects
    datetime_objects = [datetime.fromisoformat(date.replace("Z", "+00:00")) for date in dates]

    # Find the latest datetime
    first_datetime = min(datetime_objects)

    # Return the latest date as a string in ISO 8601 format
    return first_datetime.isoformat().replace("+00:00", "Z")

def get_date_range(input_date: str, end_date: str) -> tuple:
    input_date = datetime.strptime(input_date, "%Y-%m-%dT%H:%M:%SZ")
    end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%SZ")

    start = []
    end = []
    current = input_date

    while current.date() < end_date.date():  # Iterate until the day before end_date
        start_date = current.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date_daily = current.replace(hour=23, minute=59, second=59, microsecond=0)
        start.append(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        end.append(end_date_daily.strftime("%Y-%m-%dT%H:%M:%SZ"))
        current += timedelta(days=1)

    # Add the final day with the exact end_date time
    start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    start.append(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
    end.append(end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))

    return start, end


def update_time_fields(data: list, time_shift_hours: int = 1) -> list:
    updated_data = []
    for record in data:
        updated_record = record.copy()

        # Shift `createdOn`
        if "createdOn" in updated_record:
            original_created = datetime.strptime(updated_record["createdOn"], "%Y-%m-%dT%H:%M:%S.%fZ")
            new_created = original_created + timedelta(hours=time_shift_hours)
            updated_record["createdOn"] = new_created.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # Shift `modifiedOn`
        if "modifiedOn" in updated_record:
            original_modified = datetime.strptime(updated_record["modifiedOn"], "%Y-%m-%dT%H:%M:%S.%fZ")
            new_modified = original_modified + timedelta(hours=time_shift_hours)
            updated_record["modifiedOn"] = new_modified.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # Shift `timestamp` (convert milliseconds to datetime, update, then back to milliseconds)
        if "timestamp" in updated_record:
            original_timestamp = datetime.utcfromtimestamp(updated_record["timestamp"] / 1000)
            new_timestamp = original_timestamp + timedelta(hours=time_shift_hours)
            updated_record["timestamp"] = int(new_timestamp.timestamp() * 1000)

        updated_data.append(updated_record)

    return updated_data

def filter_data_by_date_range(data: list, start_date: str, end_date: str) -> list:
    return [record for record in data if is_date_in_range(start_date, end_date, record["createdOn"])]

def find_earliest_datetime(datetimes):

    if not datetimes:
        return None

    try:
        # Převést všechny datetimy na objekty datetime
        datetime_objects = [datetime.fromisoformat(dt.replace("Z", "+00:00")) for dt in datetimes]

        # Najít nejdřívější datetime
        earliest = min(datetime_objects)

        # Vrátit jako ISO 8601 řetězec
        return earliest.isoformat().replace("+00:00", "Z")
    except Exception as e:
        raise ValueError(f"Chyba při zpracování datetime: {e}")