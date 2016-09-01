#!/usr/bin/env python

#import RPi.GPIO as GPIO
import time
#import spidev
import os
import wx
import Queue
import wx.grid as gridlib
from threading import Thread
#from lib_nrf24 import NRF24
from wx.lib.pubsub import Publisher

#GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)

def main():
	app = PhotoCtrl()
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
		self.radio.printDetails()

		#start listening to incoming messages
		self.radio.startListening()
	
		self.start()
	
	def run(self):
		while True:
			print("Radio Radio Radio")
			time.sleep(1)
			
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
			self.stringMessage = self.stringMessage[:-1]
			print("Message -1 : {}".format(self.stringMessage))
			self.messageQueue.put(self.stringMessage)
			

class PhotoCtrl(wx.App):
    def __init__(self, redirect=False, filename=None):
    	wx.App.__init__(self, redirect, filename)
    	RadioThread()
    	self.screenWidth, self.screenHeight = wx.GetDisplaySize()
    	self.frame = wx.Frame(None, title="Order Screen",size=(self.screenWidth,self.screenHeight))
        self.panel = wx.Panel(self.frame)
        self.grid = gridlib.Grid(self.panel)
        self.grid.CreateGrid(3,2)
        #self.frame.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)
        self.frame.Show()

        #self.createWidgets()
        
 
    def createWidgets(self):
        instructions = 'Browse for an image'

        img = wx.EmptyImage(self.screenWidth/2,self.screenHeight/2)
        self.imageCtrl = wx.StaticBitmap(self.panel, wx.ID_ANY, 
                                         wx.BitmapFromImage(img))
 
        instructLbl = wx.StaticText(self.panel, label=instructions)
        self.photoTxt = wx.TextCtrl(self.panel, size=(200,-1))
        browseBtn = wx.Button(self.panel, label='Browse')
        browseBtn.Bind(wx.EVT_BUTTON, self.onBrowse)
 
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
 
        self.mainSizer.Add(wx.StaticLine(self.panel, wx.ID_ANY),
                           0, wx.ALL|wx.EXPAND, 5)
        self.mainSizer.Add(instructLbl, 0, wx.ALL, 5)
        self.mainSizer.Add(self.imageCtrl, 0, wx.ALL, 5)
        self.sizer.Add(self.photoTxt, 0, wx.ALL, 5)
        self.sizer.Add(browseBtn, 0, wx.ALL, 5)        
        self.mainSizer.Add(self.sizer, 0, wx.ALL, 5)
 
        self.panel.SetSizer(self.mainSizer)
        self.mainSizer.Fit(self.frame)
 
        self.panel.Layout()
 
    def onBrowse(self, event):
        """ 
        Browse for file
        """
        wildcard = "JPEG files (*.jpg)|*.jpg"
        dialog = wx.FileDialog(None, "Choose a file",
                               wildcard=wildcard,
                               style=wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self.photoTxt.SetValue(dialog.GetPath())
        dialog.Destroy() 
        self.onView()
 
main()