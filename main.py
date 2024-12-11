import time

import dht
import machine
from machine import Pin, I2C, RTC
from utime import sleep
from bh1750 import BH1750
from simple import MQTTClient
import ntptime
from time import localtime, mktime
import ubinascii
import ujson
import os
from collections import deque
from ds3231 import DS3231

# Initialize sensors and pins
sensor = dht.DHT22(Pin(5))  # DHT22 sensor on GPIO5
ledBlue = Pin(12, Pin.OUT)  # Blue LED on GPIO12
ledRed = Pin(2, Pin.OUT)  # Red LED on GPIO2
ledGreen = Pin(14, Pin.OUT)  # Green LED on GPIO14

rtc = RTC()  # Internal RTC

# I2C for BH1750 and DS3231: GPIO4 (SCL), GPIO13 (SDA)
try:
    i2c = I2C(scl=Pin(13), sda=Pin(4))
    devices = i2c.scan()
    if devices:
        print("I²C devices found at addresses:", [hex(device) for device in devices])
    else:
        print("No I²C devices found.")
    light_sensor = BH1750(i2c)
    rtc_ds = DS3231(i2c)  # RTC initialization
    print("BH1750 and DS3231 initialized successfully.")
except Exception as e:
    print(f"I²C device initialization error: {e}")
    light_sensor = None  # Continue without BH1750 if unavailable
    rtc_ds = None  # Continue without RTC if unavailable

# Load configuration
with open("config/esp_8266_config.json") as f:
    secrets = ujson.load(f)

SSID = secrets["WIFI_SSID"]
PASSWORD = secrets["WIFI_PASSWORD"]
BROKER_IP = secrets["BROKER_IP"]
BROKER_PORT = secrets["BROKER_PORT"]
BROKER_USERNAME = secrets["BROKER_USERNAME"]
BROKER_PASSWORD = secrets["BROKER_PASSWORD"]
TEAM_NAME = secrets["TEAM_NAME"]
TIME_SYNC_INTERVAL = int(secrets["TIME_SYNC_INTERVAL"])  # RTC synchronization interval in seconds
QUEUE_LENGTH = int(secrets["QUEUE_LENGTH"])  # Length of RAM queue
#TOPIC = 'ite/practise/test_topic'
TOPIC = f"ite/{TEAM_NAME}"
PAYLOAD_FILE = "payload_queue.json"


def is_valid_payload(payload):
    """Validate the payload format."""
    # Pokud je payload už dictionary, přeskočíme deserializaci
    if isinstance(payload, dict):
        data = payload
    else:
        try:
            data = ujson.loads(payload)
        except (ValueError, TypeError):
            return False

    # Kontrola klíčů a jejich typů
    required_keys = ["team_name", "timestamp"]
    return all(key in data for key in required_keys) and isinstance(data["timestamp"], str)

payload_queue = deque([], QUEUE_LENGTH)  # RAM queue


def setledcolor(R, G, B):
    """Set LED color using RGB values."""
    ledRed.value(R)
    ledGreen.value(G)
    ledBlue.value(B)


def connect_wifi(timeout=30):
    """Connect to Wi-Fi within a specified timeout period."""
    from network import WLAN, STA_IF
    wlan = WLAN(STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    start_time = time.time()

    while not wlan.isconnected():
        if time.time() - start_time > timeout:
            print("Wi-Fi connection failed. Proceeding in offline mode.")
            return False  # Connection failed
        time.sleep(1)

    print("Wi-Fi connected:", wlan.ifconfig())
    return True  # Connection successful

def get_time():
    """Get the current time from RTC or fallback to internal ESP time."""
    try:
        now = rtc_ds.datetime()  # Get time from RTC
        print("RTC Time (UTC):", now)
        return now
    except Exception as e:
        print("RTC unavailable, using internal ESP time:", e)
        return localtime()  # Fallback to ESP time

def connect_mqtt():
    """Connect to the MQTT broker."""
    client_id = ubinascii.hexlify(machine.unique_id())
    client = MQTTClient(client_id, BROKER_IP, port=BROKER_PORT, user=BROKER_USERNAME, password=BROKER_PASSWORD)
    try:
        client.connect()
        return client
    except Exception as e:
        print("MQTT connection error:", e)
        return None

def reconnect_mqtt(retries=3, delay=5):
    """Attempt to reconnect to MQTT broker."""
    for attempt in range(retries):
        try:
            print(f"Attempting to reconnect to MQTT broker (Attempt {attempt + 1}/{retries})...")
            client = connect_mqtt()
            if client is not None:
                print("Reconnected to MQTT broker.")
                return client
        except Exception as e:
            print(f"MQTT reconnection failed: {e}")
        time.sleep(delay)
    print("MQTT reconnection failed after retries.")
    return None


def sync_rtc_with_ntp():
    """Synchronize the RTC with an NTP server (UTC)."""
    if rtc_ds:
        try:
            ntptime.settime()  # Sync ESP time with NTP
            now = localtime()  # Get current UTC time

            # Adjust the time to remove unwanted offsets if necessary
            adjusted_time = mktime(now)
            adjusted_time_tuple = localtime(adjusted_time)

            # Set RTC to the adjusted time
            rtc_ds.datetime((
                adjusted_time_tuple[0],  # Year
                adjusted_time_tuple[1],  # Month
                adjusted_time_tuple[2],  # Day
                adjusted_time_tuple[3],  # Weekday
                adjusted_time_tuple[4],  # Hour
                adjusted_time_tuple[5],  # Minute
                adjusted_time_tuple[6],  # Second
                0  # Subsecond (not used)
            ))

            print("RTC synchronized with adjusted NTP time:", rtc_ds.datetime())
        except Exception as e:
            print("Error synchronizing RTC with NTP:", e)

def get_timestamp():
    """Generate ISO 8601 timestamp from RTC or fallback to ESP time."""
    time_tuple = get_time()  # Get current time
    if isinstance(time_tuple, tuple):  # Check if valid time tuple
        return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.000000".format(
            time_tuple[0], time_tuple[1], time_tuple[2],
            time_tuple[4], time_tuple[5], time_tuple[6])
    return "1970-01-01T00:00:00.000000"  # Default timestamp fallback


def debug_time():
    """Debug function to display current RTC and ESP internal times."""
    try:
        print("RTC Time (UTC):", rtc_ds.datetime())
    except Exception as e:
        print("RTC unavailable:", e)
    print("ESP Internal Time:", localtime())
    print("Generated Timestamp:", get_timestamp())


def get_rtc_unix_time():
    try:
        rtc_time = rtc_ds.datetime()  # Get the RTC time
        # RTC returns (year, month, day, weekday, hour, minute, second, subsecond)
        # mktime expects (year, month, day, hour, minute, second, weekday, yearday)

        weekday = (rtc_time[3] - 1) % 7

        # Create tuple in mktime's format
        time_tuple = (rtc_time[0], rtc_time[1], rtc_time[2],  # year, month, day
                      rtc_time[4], rtc_time[5], rtc_time[6],  # hour, minute, second
                      weekday, 0)  # weekday, yearday (yearday not used)

        # Convert to Unix timestamp
        unix_time = mktime(time_tuple)
        return unix_time
    except Exception as e:
        print("Error fetching RTC Unix time:", e)
        return None


def publish_data(client, temperature=None, humidity=None, illumination=None, timestamp=None):
    global payload_queue

    # Construct the payload
    message = {
        "team_name": TEAM_NAME,
        "timestamp": timestamp,
    }
    if temperature is not None:
        message["temperature"] = float("{:.2f}".format(temperature))
    if humidity is not None:
        message["humidity"] = round(humidity, 1)
    if illumination is not None:
        message["illumination"] = round(illumination, 1)

    payload = ujson.dumps(message)

    # Handle disconnected MQTT client
    if client is None:
        payload_queue.append(payload)  # Queue in RAM
        print("Queued payload to RAM:", payload)
        print("Current RAM queue length:", len(payload_queue))

        return False

    try:
        # Publish any queued payloads from RAM
        while payload_queue:
            queued_payload = payload_queue.popleft()
            queued_payload_bytes = queued_payload.encode('utf-8')  # Convert to bytes
            client.publish(TOPIC, queued_payload_bytes)
            print("Published queued payload from RAM:", queued_payload)
            print("Current RAM queue length:", len(payload_queue))

        # Publish the current payload
        payload_bytes = payload.encode('utf-8')  # Convert to bytes
        client.publish(TOPIC, payload_bytes)
        print("Published:", payload)
        return True
    except Exception as e:
        print("Error publishing data:", e)
        payload_queue.append(payload)  # Requeue in RAM
        print("Queued payload to RAM:", payload)
        print("Current RAM queue length:", len(payload_queue))
        return False






def main():
    setledcolor(1, 0, 0)
    if not connect_wifi():
        print("Operating in offline mode.")
    else:
        print("Wi-Fi connected successfully.")

    client = connect_mqtt()
    if client is not None:
        print("Connected to MQTT broker.")

    sync_rtc_with_ntp()  # Synchronize RTC with NTP
    last_sync = get_rtc_unix_time()

    # Initial measurement time
    planned_measurement_time = get_rtc_unix_time()  # Trigger first measurement immediately
    setledcolor(0, 1, 0)

    try:
        while True:
            # Get the current time
            current_time = get_rtc_unix_time()

            # Check if it's time to measure and publish data
            if current_time >= planned_measurement_time:
                setledcolor(0, 0, 1)  # Blue LED indicates data collection
                planned_measurement_time += 60  # Schedule next measurement
                timestamp = get_timestamp()

                # Collect sensor data
                temperature, humidity, illumination = None, None, None
                try:
                    sensor.measure()
                    temperature = sensor.temperature()
                    humidity = sensor.humidity()
                except Exception as e:
                    print("Error reading DHT22 sensor:", e)

                try:
                    illumination = light_sensor.luminance(BH1750.CONT_HIRES_1)
                except Exception as e:
                    print("Error reading BH1750 sensor:", e)

                # Publish the data
                if any([temperature, humidity, illumination]):
                    if not publish_data(client, temperature, humidity, illumination, timestamp):
                        print("Reconnecting to MQTT broker...")
                        client = reconnect_mqtt()
                        if client is not None:
                            print("Reconnected to MQTT broker.")
                else:
                    print("No data available to publish.")
            # Daily RTC synchronization
            if current_time - last_sync >= TIME_SYNC_INTERVAL:
                setledcolor(0, 1, 1)
                try:
                    sync_rtc_with_ntp()
                    last_sync = current_time
                except Exception as e:
                    print("Error during RTC synchronization:", e)

            time.sleep(0.1)
            setledcolor(0, 1, 0)  # Green LED indicates idle state

    except KeyboardInterrupt:
        print("Program terminated.")
    finally:
        if client is not None:
            client.disconnect()

# Start the main function
main()