import time
import dht
import machine
import network
import ubinascii
from umqtt.simple import MQTTClient
from machine import Pin
from ntptime import settime
from time import localtime, mktime

# Nastavení senzoru DHT22
sensor = dht.DHT22(Pin(5))

import ujson

# Load Wi-Fi credentials from the JSON file
with open("config/esp_8266_config.json") as f:
    secrets = ujson.load(f)

SSID = secrets["WIFI_SSID"]
PASSWORD = secrets["WIFI_PASSWORD"]

# Nastavení MQTT
BROKER_IP = secrets["BROKER_IP"]
BROKER_PORT = secrets["BROKER_PORT"]
BROKER_USERNAME = secrets["BROKER_USERNAME"]
BROKER_PASSWORD = secrets["BROKER_PASSWORD"]
TEAM_NAME = secrets["TEAM_NAME"]
TOPIC = f"ite/{TEAM_NAME}"

# Připojení k Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(1)
    #print("Connected to Wi-Fi:", wlan.ifconfig())

# Připojení k MQTT brokeru
def connect_mqtt():
    client_id = ubinascii.hexlify(machine.unique_id())
    client = MQTTClient(client_id, BROKER_IP, port=BROKER_PORT, user=BROKER_USERNAME, password=BROKER_PASSWORD)
    client.connect()
    #print("Connected to MQTT broker")
    return client

# Získání aktuálního času s UTC+1 offsetem v požadovaném formátu
def get_timestamp():
    settime()
    now = mktime(localtime()) + 3600
    adjusted_time = localtime(now)
    timestamp = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.{:06d}".format(*adjusted_time, 0)
    return timestamp

# Publikace dat na MQTT broker
def publish_data(client, temperature, humidity=None):
    timestamp = get_timestamp()
    message = {
        "team_name": TEAM_NAME,
        "timestamp": timestamp,
        "temperature": round(temperature, 2)
    }
    if humidity is not None:
        message["humidity"] = round(humidity, 1)
    payload = str(message).replace("'", "\"")  # Formátování na JSON-like string
    client.publish(TOPIC, payload)
    #print("Published message:", payload)

def main():
    connect_wifi()
    client = connect_mqtt()
    last_sync = time.time()

    try:
        while True:
            # Periodically re-sync the time to avoid drift
            if time.time() - last_sync > 3600:  # Re-sync every hour
                settime()
                last_sync = time.time()
                #print("Time re-synchronized with NTP")


            sensor.measure()
            temperature = sensor.temperature()
            humidity = sensor.humidity()

            publish_data(client, temperature, humidity)
            time.sleep(60)

    except KeyboardInterrupt:
        print("Program ukončen")
    finally:
        client.disconnect()



main()








