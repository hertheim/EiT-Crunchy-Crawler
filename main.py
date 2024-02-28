from network import LTE
import time
import socket
import machine
import pycom
from lib.dht import DHT
from lib.hx711 import HX711
import json
import crypto

pycom.heartbeat(False)
pycom.rgbled(0x001000) # green

th = DHT('P23',0)
hx = HX711('P9', 'P10') # data, clock
hx.set_scale(8388.6) # 2**24/1000/2 This seams to be wrong, needs to be calibrated
hx.tare()
time.sleep(2) # wait for the dht sensor to stabilize


result = th.read()
while result.is_valid() == False:   ## loop to get valid data, shuold theorethically not be needed
    time.sleep(1)
    result = th.read()

if result.is_valid():
    print("Temperature:", result.temperature, "C")
    print("Humidity:", result.humidity, "%")

val = hx.get_value(5)   # get the weight
print("Weight:", val, "g")

data = {
    "id": str(crypto.getrandbits(32)),
    "temperature": result.temperature,
    "humidity": result.humidity,
    "weight": val
}
out = json.dumps(data)
print(out)
pycom.rgbled(0x000010) # blue


lte = LTE()
print("init..")
lte.attach(apn="mda.lab5e") # attach the cellular modem to the network using lab5e APN
print("attaching..",end='')
while not lte.isattached():
    time.sleep(0.25)

    print('.',end='')
    print(lte.send_at_cmd('AT!="fsm"'))         # get the System FSM
print("attached!")

lte.connect()
print("connecting [##",end='')
while not lte.isconnected():
    time.sleep(0.25)
    print('#',end='')
    #print(lte.send_at_cmd('AT!="showphy"'))
    print(lte.send_at_cmd('AT!="fsm"'))
print("] connected!")

print("LTE connected: " + str(lte.isconnected()))

soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP socket
print("Socket created")
pycom.rgbled(0x100000) # red

for i in range(1, 2):   # send the data 2 times to make sure it gets through
    print("Sending data")
    soc.sendto(out, ('172.16.15.14', 1234))
    print("Sent data")
    time.sleep(5)
soc.close()
print("Socket closed")

lte.deinit() # disconnect the modem
pycom.rgbled(0x000000) # off

machine.deepsleep(10*60*1000) # sleep for 10 minutes