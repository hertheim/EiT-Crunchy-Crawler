import pycom
from time import sleep_us, sleep
import machine
from lib.hx711 import HX711


print('Starting HX711 test')
hx = HX711('P9', 'P10')
hx.set_scale(2**24/1000)
hx.tare()
while True:
    #val = hx.get_units(5)
    val = hx.get_value(5)
    val = ((val/2**24)/2)*1000
    print(val)
    sleep(2)