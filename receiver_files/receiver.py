import RPi.GPIO as GPIO
from lib_nrf24 import NRF24
import time
import spidev
import os

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#addresses for communication with transmitter
pipes = [[0xE8, 0xE8, 0xF0, 0xF0, 0xE1], [0xF0, 0xF0, 0xF0, 0xF0, 0xE1]]

radio = NRF24(GPIO, spidev.SpiDev())

#arguments are (CSN,CE) pins
radio.begin(0,17)

radio.setPayloadSize(32)
radio.setChannel(0x76)

# better range with lower transfer rate)
radio.setDataRate(NRF24.BR_1MBPS)

radio.setPALevel(NRF24.PA_MIN)

radio.setAutoAck(True)
radio.enableDynamicPayloads()
radio.enableAckPayload()

radio.openReadingPipe(1,pipes[1])
radio.printDetails()

#start listening to incoming messages
radio.startListening()
allowedSelections = ["coffee","tea","milo","coke"]

while True:
    ackPayLoad = [1]
    while not radio.available(0):
        time.sleep(1/100)


    receivedMessage = []
    radio.read(receivedMessage, radio.getDynamicPayloadSize())

    print("Received: {}".format(receivedMessage))

    print("translating our received Message into unicode characters...")

    #Decode into standard unicode set
    selection = ""

    for n in receivedMessage:
        if (n >= 32 and n<= 126):
            selection += chr(n)

    print("Drink selected : {}".format(selection))
    #radio.writeAckPayload(1,ackPayLoad,len(ackPayLoad))

"""
    if (selection in allowedSelections):
        pathToImg = "/home/pi/Documents/drone_receiver/img_src/" + selection + ".jpg"
        command = "sudo timeout 3s feh -ZF " + pathToImg
        os.system(command)
    #    time.sleep(3)
        os.system("sudo pkill feh")

    else:
        print("No such drinks available")
        
    #print ("Loaded payload reply of {}".format(ackPayLoad))
"""
