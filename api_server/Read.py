import pytz
import logging
from influxdb_client import InfluxDBClient

def read(url, token, org, bucket, team, sensor, field_name, start_time, end_time):
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

def read_latest(url, token, org, bucket, team, sensor, field_name, sampling_period):
    client = InfluxDBClient(url=url, token=token, org=org)

    try:
        query = f'''
                        from(bucket: "{bucket}")
                          |> range(start: {sampling_period})
                          |> filter(fn: (r) => r["_measurement"] == "{team}")
                          |> filter(fn: (r) => r["sensor"] == "{sensor}")
                          |> filter(fn: (r) => r["_field"] == "{field_name}")
                          |> last()
                        '''
        tables = client.query_api().query(query=query)
    except Exception as e:
        logging.critical(f"Error querying data in `read_latest`: {e}")
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

from influxdb_client import InfluxDBClient
import logging

def count_all_datapoints(url, token, org, bucket, team, sensor, field_name):
    client = InfluxDBClient(url=url, token=token, org=org)

    try:
        query = f'''
                        from(bucket: "{bucket}")
                          |> range(start: 0)  // Unbounded range from Unix epoch
                          |> filter(fn: (r) => r["_measurement"] == "{team}")
                          |> filter(fn: (r) => r["sensor"] == "{sensor}")
                          |> filter(fn: (r) => r["_field"] == "{field_name}")
                          |> count()
                        '''
        tables = client.query_api().query(query=query)
    except Exception as e:
        logging.critical(f"Error querying data in `count_all_datapoints`: {e}")
        client.close()
        raise

    # Extract count
    count_values = []

    for table in tables:
        for record in table.records:
            count_values.append(record.get_value())

    # Close the client
    client.close()

    # Sum counts if multiple tables
    total_count = sum(count_values) if count_values else 0

    return total_count

