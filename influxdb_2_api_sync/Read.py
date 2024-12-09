import pytz
import logging
from influxdb_client import InfluxDBClient

def read(url , token, org, bucket, team, sensor, field_name, start_time, end_time):
    client = InfluxDBClient(url=url, token=token, org=org)

    try:
        query = f'''
                from(bucket: "{bucket}")
                  |> range(start: {start_time}, stop: {end_time})
                  |> filter(fn: (r) => r["_measurement"] == "{team}")
                  |> filter(fn: (r) => r["sensor"] == "{sensor}")
                  |> filter(fn: (r) => r["_field"] == "{field_name}")
                '''
        tables = client.query_api().query(query)
    except Exception as e:
        logging.critical(f"Error querying data in `read`: {e}")
        client.close()
        raise

    # Extract data
    time_values = []
    measurement_values = []

    for table in tables:
        for record in table.records:
            time_values.append(record.get_time())
            measurement_values.append(record.get_value())

    # Close the client
    client.close()

    # Convert UTC time to local timezone
    timezone = 'Europe/Paris'
    local_timezone = pytz.timezone(timezone)
    time_values_local = [time.astimezone(local_timezone) for time in time_values]

    return time_values_local, measurement_values

def get_first_record_datetime(url, token, org, bucket, team, sensor, field_name):
    client = InfluxDBClient(url=url, token=token, org=org)

    try:
        # Flux dotaz pro získání prvního záznamu
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: 0)  // Od začátku databáze
              |> filter(fn: (r) => r["_measurement"] == "{team}")
              |> filter(fn: (r) => r["sensor"] == "{sensor}")
              |> filter(fn: (r) => r["_field"] == "{field_name}")
              |> sort(columns: ["_time"], desc: false)  // Seřazení vzestupně podle času
              |> limit(n: 1)  // Omezení na 1 záznam
        '''
        tables = client.query_api().query(query)
    except Exception as e:
        logging.critical(f"Error querying data in `get_first_record_datetime`: {e}")
        client.close()
        raise

    # Zpracování výsledku
    first_time = None
    for table in tables:
        for record in table.records:
            first_time = record.get_time()
            break  # První záznam je nalezen, ukončujeme iteraci
        if first_time:
            break

    # Zavření klienta
    client.close()

    if first_time:
        # Převod na lokální časové pásmo
        timezone = 'Europe/Paris'
        local_timezone = pytz.timezone(timezone)
        first_time_local = first_time.astimezone(local_timezone)
        return first_time_local
    else:
        return None

