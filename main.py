import pycom
import time
from dht import DHT

pycom.heartbeat(False)
pycom.rgbled(0x000008) # blue
th = DHT('P23',0)
while True:
    time.sleep(2)
    result = th.read()
    if result.is_valid():
        pycom.rgbled(0x001000) # green
        print("Temperature:", result.temperature, "C")
        print("Humidity:", result.humidity, "%")
