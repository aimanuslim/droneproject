#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import spidev
import os
import wx
import Queue
import wx.grid as gridlib
from threading import Thread
from lib_nrf24 import NRF24
from wx.lib.pubsub import pub
import wx.lib.agw.fourwaysplitter as fws

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

MENU = ["Cappucino","Latte", "Flatwhite", "Americano", "Machiatto"]

def main():
	app = wx.App(False)
 
	frame = MyFrame()
	app.SetTopWindow(frame)
	frame.Show()
	#frame.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)
	frame.Maximize(True)
	app.MainLoop()

class RadioThread(Thread):
	def __init__(self):

		Thread.__init__(self)
		#addresses for communication with transmitter
		self.messageQueue = Queue.Queue()

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
		#self.radio.printDetails()

		#start listening to incoming messages
		self.radio.startListening()
		self.start()
	
	def run(self):
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
			self.messageQueue.put(self.stringMessage)

			wx.CallAfter(pub.sendMessage,"update panel",message = self.messageQueue.get())


class OrderPanel(wx.Panel):
	def __init__(self,splitter,count):
		wx.Panel.__init__(self,splitter)
		self.color = wx.BLUE
		self.fontSize = 20
		self.distanceFromTop = 10;
		self.distanceFromSide = 10;
		self.distanceFromPanelInfo = 50
		self.panelInfoFont = wx.Font(self.fontSize,wx.SWISS,wx.NORMAL,wx.BOLD,underline=True)
		self.orderInfoFont = wx.Font(self.fontSize,wx.SWISS,wx.NORMAL,wx.BOLD)

		self.panelInfo = wx.StaticText(self,-1, "ORDER PANEL " + str(count),pos=(self.distanceFromSide,self.distanceFromTop))
		self.panelInfo.SetForegroundColour(wx.WHITE)
		self.panelInfo.SetFont(self.panelInfoFont)

		self.orderNumberInfo = wx.StaticText(self,-1, "#",pos = (800,self.distanceFromTop))
		self.orderNumberInfo.SetForegroundColour(wx.WHITE)
		self.orderNumberInfo.SetFont(self.panelInfoFont)
		
		newDistance = self.distanceFromTop + self.distanceFromPanelInfo + self.fontSize
		self.orderInfo = wx.StaticText(self,-1, "", pos=(self.distanceFromSide,newDistance))
		self.orderInfo.SetFont(self.orderInfoFont)
		self.orderInfo.SetForegroundColour(wx.WHITE)

		self.SetBackgroundColour(self.color)


class MyFrame(wx.Frame):
 
	#----------------------------------------------------------------------
	def __init__(self):
		wx.Frame.__init__(self, None, title="Order Screen")
		splitter = fws.FourWaySplitter(self, agwStyle=wx.SP_LIVE_UPDATE)
		self.maxNumberOfPanels = 4
		self.orderPanels = []
		self.currentPanel = 0
		self.currentOrder = 1
		self.color = wx.BLUE

		print("Subscribing.....")
		pub.subscribe(self.onOrderReceived,"update panel")
		print("Subscribed to updatePanels")

		print("Starting RadioThread")
		RadioThread()
		print("RadioThread started")
		#create individual Panels
		for i in range (1,self.maxNumberOfPanels + 1):
			panel = OrderPanel(splitter,i)
			splitter.AppendWindow(panel)
			self.orderPanels.append(panel)

	def getListOfOrder(self,order):
		global MENU
		currentIndex = 0
		orderList = ""
		print("Order is: {}".format(order))
		for c in order:
			if int(c) == 1:
				orderList = orderList + "[+] " + MENU[currentIndex] +"\n"

			currentIndex = currentIndex + 1

		return orderList.rstrip()

	def onOrderReceived(self,message):
		# Parse the order string
		orderList = self.getListOfOrder(message)

		#update currentPanel
		for panel in self.orderPanels:
			panel.SetBackgroundColour(wx.BLUE)

		self.orderPanels[self.currentPanel].orderInfo.SetLabel(orderList)
		self.orderPanels[self.currentPanel].SetBackgroundColour(wx.RED)
		self.orderPanels[self.currentPanel].orderNumberInfo.SetLabel("# " + str(self.currentOrder))

		self.currentOrder = self.currentOrder + 1
		self.currentPanel = self.currentPanel + 1

		if self.currentPanel > 3:
			self.currentPanel = 0
		
main()


