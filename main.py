import time
import dht
import machine
import network
import ubinascii
from umqtt.simple import MQTTClient
from machine import Pin
from ntptime import settime
from time import localtime, mktime
import ujson
import json

# Sensor and MQTT configuration
sensor = dht.DHT22(Pin(5))
ledBlue = Pin(12, Pin.OUT)
ledRed = Pin(4, Pin.OUT)
ledGreen = Pin(14, Pin.OUT)

with open("config/esp_8266_config.json") as f:
    secrets = ujson.load(f)

SSID = secrets["WIFI_SSID"]
PASSWORD = secrets["WIFI_PASSWORD"]
BROKER_IP = secrets["BROKER_IP"]
BROKER_PORT = secrets["BROKER_PORT"]
BROKER_USERNAME = secrets["BROKER_USERNAME"]
BROKER_PASSWORD = secrets["BROKER_PASSWORD"]
TEAM_NAME = secrets["TEAM_NAME"]
TIME_SYNC_INTERVAL = int(secrets["TIME_SYNC_INTERVAL"])
TOPIC = f"ite/{TEAM_NAME}"

def setledcolor(R, G, B):
    ledRed.value(R)
    ledGreen.value(G)
    ledBlue.value(B)

# Connect to Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(1)


# Connect to MQTT broker
def connect_mqtt():
    client_id = ubinascii.hexlify(machine.unique_id())
    client = MQTTClient(client_id, BROKER_IP, port=BROKER_PORT, user=BROKER_USERNAME, password=BROKER_PASSWORD)
    try:
        client.connect()
        return client
    except Exception as e:
        print("Failed to connect to MQTT broker:", e)
        return None


# Get current timestamp with UTC+1 offset
def get_timestamp():
    now = mktime(localtime()) + 3600  # Add offset for UTC+1
    adjusted_time = localtime(now)
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.{:06d}".format(*adjusted_time, 0)


# Publish data to MQTT broker
def publish_data(client, temperature, humidity=None):
    if client is None:
        return False
    try:
        timestamp = get_timestamp()
        message = {
            "team_name": TEAM_NAME,
            "timestamp": timestamp,
            "temperature": float("{:.2f}".format(temperature))
        }
        if humidity is not None:
            message["humidity"] = round(humidity, 1)
        payload = json.dumps(message)
        client.publish(TOPIC, payload)
        print("Published:", payload)
        return True
    except Exception as e:
        print("Error publishing data:", e)
        return False


# Main function
def main():
    setledcolor(1,0,0)
    connect_wifi()
    print("Connected to Wi-Fi")
    client = connect_mqtt()
    if client is not None:
        print("Connected to MQTT broker")
    settime()
    last_sync = time.time()
    last_publish = time.time() - 60  # Publish immediately on start
    setledcolor(0,1,0)
    try:
        while True:
            current_time = time.time()

            # Check if it's time to publish
            if current_time - last_publish >= 60:
                setledcolor(0,0,1)
                # Attempt to read sensor data
                for attempt in range(3):
                    try:
                        sensor.measure()
                        temperature = sensor.temperature()
                        humidity = sensor.humidity()
                        break
                    except Exception as e:
                        print(f"Error reading sensor data, attempt {attempt + 1}: {e}")
                        setledcolor(1, 0, 0)
                        time.sleep(1)
                else:
                    print("Failed to read sensor data after multiple attempts, skipping publish.")
                    setledcolor(1, 0, 0)
                    time.sleep(0.5)
                    last_publish = current_time  # Skip to next interval
                    continue

                # Publish data and reconnect if needed
                if not publish_data(client, temperature, humidity):
                    print("Reconnecting to MQTT broker...")
                    client = connect_mqtt()
                    if client is not None:
                        print("Reconnected to MQTT broker.")

                last_publish = current_time  # Update publish time after successful publish
            # Sync time every X seconds
            if current_time - last_sync > TIME_SYNC_INTERVAL:
                setledcolor(0,1,1)
                try:
                    settime()
                    last_sync = current_time
                except Exception as e:
                    print("Failed to sync time:", e)
                    setledcolor(1, 0, 0)
                    time.sleep(0.5)

            time.sleep(0.1)
            setledcolor(0, 1, 0)


    except KeyboardInterrupt:
        print("Program stopped")
    finally:
        if client is not None:
            client.disconnect()
main()

























