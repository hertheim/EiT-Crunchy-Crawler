import pycom
import time
from lib.dht import DHT
from lib.hx711 import HX711
import json

pycom.heartbeat(False)
pycom.rgbled(0x000008) # blue
th = DHT('P23',0)
hx = HX711('P9', 'P10')
hx.set_scale(8388.6) # 2**24/1000/2
hx.tare()
while True:
    time.sleep(2)
    result = th.read()
    if result.is_valid():
        pycom.rgbled(0x001000) # green
        print("Temperature:", result.temperature, "C")
        print("Humidity:", result.humidity, "%")
    val = hx.get_value(5)
    val = ((val/2**24)/2)*1000 
    print(val)

    data = {
        "temperature": result.temperature,
        "humidity": result.humidity,
        "weight": val
    }
    print(json.dumps(data))
