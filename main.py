from network import LTE
import time
import socket
import machine
import pycom
from lib.dht import DHT
from lib.hx711 import HX711
import json
import crypto

# Constants
green_hex = 0x001000
red_hex = 0x100000
blue_hex = 0x000010
off_hex = 0x000000

weight_sensor_scale = 8388.6 # 2**24/1000/2 This seams to be wrong, needs to be calibrated

apn_name = 'mda.lab5e'
ip_adress = '172.16.15.14'
port = 1234

sleep_time_ms = 10*1000 # sleep for 10 seconds


def sensor_setup(tare: bool):
    global weight_sensor_scale

    print("Setting up sensors")

    dht = DHT('P23', 0)
    hx = HX711('P9', 'P10') # data, clock
    hx.set_scale(weight_sensor_scale)
    if tare:
        hx.tare()
    time.sleep(2) # wait for the dht sensor to stabilize

    return dht, hx
    

def read_data(dht, hx):
    global green_hex

    print("Reading sensor data")
    pycom.rgbled(green_hex)

    result = dht.read()
    while result.is_valid() == False: # loop to get valid data, shuold theorethically not be needed
        time.sleep(1)
        result = dht.read()

    if result.is_valid():
        print("Temperature:", result.temperature, "C")
        print("Humidity:", result.humidity, "%")

    # get the weight, using get_units considers the scale, while get_value does not (Just raw value)
    val = hx.get_units(times=5) 
    print("Weight:", val, "g")

    data = {
        "id": str(crypto.getrandbits(32)),
        "temperature": result.temperature,
        "humidity": result.humidity,
        "weight": val
    }
    out = json.dumps(data)
    print(out)
    return out


def lte_setup(apn_name):
    global blue_hex
    pycom.rgbled(blue_hex)

    # Attach the cellular modem to the network using lab5e APN
    # TODO: Sometimes crashes between the start of this function and before the print("init...") below
    lte = LTE()
    print("init ...")
    lte.attach(apn=apn_name)
    print("attaching ...",end='')
    i = 0
    while not lte.isattached():
        time.sleep(0.25)
        i += 1
        print('Check number ' + str(i))
        print(lte.send_at_cmd('AT!="fsm"')) # get the System FSM
    print("attached! Checked " + str(i) + " times while attaching")

    # Connect the LTE
    print("Connecting ...")
    lte.connect()
    i = 0
    while not lte.isconnected(): # Usually it is already connected, but in case something is wrong:
        time.sleep(0.25)
        i += 1
        print('Check number ' + str(i))
        
        # Need to surround the send_at_cmd call with suspend and presume to avoid the modem being in datastate (connected)
        lte.pppsuspend()
        # print(lte.send_at_cmd('AT!="showphy"'))
        print(lte.send_at_cmd('AT!="fsm"'))
        lte.pppresume()
    print("Connected! Checked " + str(i) + " times while connecting")

    return lte


def send_udp_package(json_package):
    global red_hex
    pycom.rgbled(red_hex)

    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP socket
    print("Socket created")

    for i in range(2):   # send the data 2 times to make sure it gets through
        print("Sending data")
        soc.sendto(json_package, (ip_adress, port))
        print("Sent data")
        time.sleep(5) # TODO: Sometimes randomly crashes after the first "Sent" but before the second "Sending"
    soc.close() # Can randomly crash here
    print("Socket closed")


def disconnet_lte(lte):
    # If the modem is not properly disconnected, and the IoT device is not properly reset
    # Then it crashes when trying to set it up next time it starts
    print('Disconnecting LTE')
    lte.deinit() # Disconnect the modem


# Previous deepsleep code (Not used currently)
def main_deepsleep():
    pycom.heartbeat(False)
    pycom.rgbled(green_hex) 

    dht, hx = sensor_setup(tare=True)
    json_data = read_data(dht, hx)
    lte = lte_setup(apn_name)
    send_udp_package(json_data)



    disconnet_lte(lte) # Disconnect the modem
    pycom.rgbled(off_hex) 


    machine.deepsleep(10*60*1000) # sleep for 10 minutes


def main_lightsleep():
    global sleep_time_ms
    
    pycom.heartbeat(False)
    pycom.rgbled(green_hex)


    def iteration_func(tare: bool):

        dht, hx = sensor_setup(tare=tare)
        json_data = read_data(dht, hx)
        lte = lte_setup(apn_name)
        send_udp_package(json_data)

        disconnet_lte(lte)
        pycom.rgbled(off_hex) 

        print('Sleeping for ' + str(sleep_time_ms/1000) + ' seconds')
        time.sleep(0.5) # Trying to fix weird issues with the terminal where only the "Sleeping f" part of the print above is displayed
        machine.sleep(sleep_time_ms) 


    iteration_number = 1
    print('\n######################################')
    print('Iteration number ' + str(iteration_number))
    iteration_func(tare=True)


    while True:
        iteration_number += 1
        print('\n######################################')
        print('Iteration number ' + str(iteration_number))

        iteration_func(tare=False)


    

main_lightsleep()