import RPi.GPIO as GPIO
from lib_nrf24 import NRF24
import time
import spidev
import os

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class RadioClass():
	def __init__(self):
		#addresses for communication with transmitter
		self.pipes = [[0xE8, 0xE8, 0xF0, 0xF0, 0xE1], [0xF0, 0xF0, 0xF0, 0xF0, 0xE1]]
		self.radio = NRF24(GPIO, spidev.SpiDev())
		self.receivedMessage = []
		self.stringMessage = ""
		#arguments are (CSN,CE) pins
		self.radio.begin(0,17)
		self.radio.setPayloadSize(32)
		self.radio.setChannel(0x76)

		# better range with lower transfer rate)
		self.radio.setDataRate(NRF24.BR_1MBPS)

		self.radio.setPALevel(NRF24.PA_MAX)

		self.radio.setAutoAck(True)
		self.radio.enableDynamicPayloads()
		self.radio.enableAckPayload()

		self.radio.openReadingPipe(1,self.pipes[1])
		self.radio.printDetails()

		#start listening to incoming messages
		self.radio.startListening()

	def getOrders(self):
		while True:
			while not self.radio.available(0):
        			time.sleep(1/100)


			self.receivedMessage = []
			self.radio.read(self.receivedMessage, self.radio.getDynamicPayloadSize())

			print("Received: {}".format(self.receivedMessage))

			print("translating our received Message into unicode characters...")

			#Decode into standard unicode set
			self.stringMessage = ""

			for n in self.receivedMessage:
				if (n >= 32 and n<= 126):
        				self.stringMessage += chr(n)

			print("Message decodes to : {}".format(self.stringMessage))

piRadio = RadioClass()
piRadio.getOrders()
