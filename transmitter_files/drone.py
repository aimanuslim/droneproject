#!/usr/bin/env python

import glob
import os
import wx
import sys
import time
import serial
from threading import Thread
from wx.lib.pubsub import setuparg1
from wx.lib.pubsub import pub as Publisher
import wx.lib.agw.pybusyinfo as PBI

#from wx.lib.pubsub import Publisher
MENU = ["Espresso", "Caffe Latte", "Cappuccino", "Americano", "Caffe Mocha", "Cafe au Lait"]

def main():
	app = wx.PySimpleApp()
	app.TopWindow = ViewerFrame()
	app.MainLoop()

class GestureThread(Thread):
	## This class is made for all the openCV processing and methods.
	## Please note how to communicate with the GUI via the following function calls

	"""
		1) Next picture      : wx.CallAfter(Publisher().sendMessage,"next picture","")
		2) Previous picture  : wx.CallAfter(Publisher().sendMessage,"previous picture","")
		3) Select picture    : wx.CallAfter(Publisher().sendMessage,"select picture","")
		4) Deselect picture  : wx.CallAfter(Publisher().sendMessage,"unselect picture","")
		5) Send order        : wx.CallAfter(Publisher().sendMessage,"send order","")
	"""


	def __init__(self):

		# this time.sleep must be here
		time.sleep(3)
		Thread.__init__(self)
		self.start()

	def run(self):
		"""
		Place your openCV processing codes in here
		Currently the codes in here are just for testing
		"""

		for i in range(1,1000):
			time.sleep(0.5)
			print("Gesture Thread # {}. Modulo by 5 is {}".format(i, i % 5))

			if (i%5) == 0:
				print("Entered next picture")
				wx.CallAfter(Publisher.sendMessage,"next picture","")
				#wx.CallAfter(Publisher().sendMessage,"next picture","")

			if (i%12) == 0:
				print("Selected this picture")
				wx.CallAfter(Publisher.sendMessage,"select picture","")
			  	#wx.CallAfter(Publisher().sendMessage,"select picture","")

			if (i%17) == 0:
				wx.CallAfter(Publisher.sendMessage,"send order","")
				time.sleep(5)
				#wx.CallAfter(Publisher().sendMessage,"send order","")

#############################################################################

class RadioThread(Thread):
	def __init__(self):
		Thread.__init__(self)

		print("Creating my Arduino object...............")

		self.serialPort = glob.glob("/dev/ttyUSB*")[0]
		self.baudRate = 9600
		
		# Establish serial connection with Arduino
		print("Initiating serial port connection")
		self.arduinoSerial = serial.Serial(self.serialPort,self.baudRate)
		
		# Testing connection
		# Upon successful connection, Arduino will give out 3 short beeps
		# and return "OK"
		print("Testing serial connection.....")
		time.sleep(3)
		self.arduinoSerial.write("xxxx")

		# Test to see if Arduino returns "OK" to acknowledge connection
		print("Waiting for reply from arduino.....")
		time.sleep(2)
		reply = self.arduinoSerial.readline().rstrip()
		
		if reply == "OK":
			print("SUCCESS. Serial connection with Arduino on {} with speed {}".format(self.serialPort,self.baudRate))

		else:
			print("FAIL. Serial connection with Arduino on {} with speed {}".format(self.serialPort,self.baudRate))
		self.start()

	def run(self):
		print("Arduino is listening on serial.")

	def writeToArduino(self, msg):

		# send message to arduino via Serial
		self.arduinoSerial.write(msg)
		print("Sent {} to Arduino!".format(msg))


class ViewerPanel(wx.Panel):

	def __init__(self, parent):
		time.sleep(3)
		wx.Panel.__init__(self, parent)
		
		width, height = wx.DisplaySize()
		width = 858
		height = 480
		print("Screen is {} x {}".format(width,height))
		self.softBlue = "#46C6F3"
		self.green = "#09C595"
		self.picPaths = []
		self.checkBoxPath = os.getcwd() + "/img_src/" + "check_box.jpg"
		self.currentPicture = 0
		self.selectedPictures = []
		self.totalPictures = 0
		self.photoMaxSize = width/2
		print("photomax size is {}".format(self.photoMaxSize))
		#self.arduino = RadioThread()


		Publisher.subscribe(self.updateImages, ("update images"))
		print("Subscribed to updateImages")
		Publisher.subscribe(self.nextPicture,("next picture"))
		print("Subscribed to nextPicture")
		Publisher.subscribe(self.previousPicture,("previous picture"))
		print("Subscribed to prevPicture")
		Publisher.subscribe(self.selectPicture,("select picture"))
		print("Subscribed to selectPicture")
		Publisher.subscribe(self.unselectPicture,("unselect picture"))
		print("Subscribed to unselectPicture")
		Publisher.subscribe(self.sendOrder,("send order"))
		print("Subscribed to sendOrder")

		"""
		Publisher().subscribe(self.updateImages, ("update images"))
		print("Subscribed to updateImages")
		Publisher().subscribe(self.nextPicture,("next picture"))
		print("Subscribed to nextPicture")
		Publisher().subscribe(self.previousPicture,("previous picture"))
		print("Subscribed to prevPicture")
		Publisher().subscribe(self.selectPicture,("select picture"))
		print("Subscribed to selectPicture")
		Publisher().subscribe(self.unselectPicture,("unselect picture"))
		print("Subscribed to unselectPicture")
		Publisher().subscribe(self.sendOrder,("send order"))
		print("Subscribed to sendOrder")
		"""

		self.layout()
		
	#----------------------------------------------------------------------



	def layout(self):
		
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		btnSizer = wx.BoxSizer(wx.HORIZONTAL)
		
		img = wx.EmptyImage(self.photoMaxSize,self.photoMaxSize)
		self.imageCtrl = wx.StaticBitmap(self, wx.ID_ANY, 
										 wx.BitmapFromImage(img))
		self.mainSizer.Add(self.imageCtrl, 0, wx.ALL|wx.CENTER, 5)
		self.imageLabel = wx.StaticText(self, label="")
		self.imageLabelFont = wx.Font(30,wx.SCRIPT,wx.NORMAL,wx.NORMAL)
		self.imageLabel.SetFont(self.imageLabelFont)
		self.imageLabel.SetForegroundColour(wx.WHITE)

		self.mainSizer.Add(self.imageLabel, 0, wx.ALL|wx.CENTER, 5)
		
			
		self.mainSizer.Add(btnSizer, 0, wx.CENTER)
		self.SetSizer(self.mainSizer)
		
	#----------------------------------------------------------------------
	def loadImage(self, image):
		""""""
		global MENU

		#img = wx.Image(self.checkBoxPath, wx.BITMAP_TYPE_ANY)
		img = wx.Image(image, wx.BITMAP_TYPE_ANY)
		# scale the image, preserving the aspect ratio
		W = img.GetWidth()
		H = img.GetHeight()
		if W > H:
			NewW = self.photoMaxSize
			NewH = self.photoMaxSize * H / W
		else:
			NewH = self.photoMaxSize
			NewW = self.photoMaxSize * W / H
		img = img.Scale(NewW,NewH)

		self.imageCtrl.SetBitmap(wx.BitmapFromImage(img))

		if self.selectedPictures[self.currentPicture] is True:
			self.SetBackgroundColour(self.green)

		else:
			self.SetBackgroundColour(self.softBlue)

		self.imageLabel.SetLabel(MENU[self.currentPicture])
		self.Refresh()
		Publisher.sendMessage("resize", "")
		#Publisher().sendMessage("resize", "")

	def loadOrderSent(self):
		print("Entered order sent!")
		#self.arduino.writeToArduino(order)
		message = "Processing your order. Please wait 3 seconds....."
		orderSentDialog = PBI.PyBusyInfo(message,parent=None,title="Order Sent!")
		
		for i in xrange(3):
			wx.MilliSleep(1000)

		del orderSentDialog

		self.currentPicture = 0
		self.loadImage(self.picPaths[self.currentPicture])
		print("RESET")
		
	#----------------------------------------------------------------------
	def nextPicture(self,msg):
		"""
		Loads the next picture in the directory
		"""
		if self.currentPicture == self.totalPictures-1:
			self.currentPicture = 0
		else:
			self.currentPicture += 1
		self.loadImage(self.picPaths[self.currentPicture])
		
	#----------------------------------------------------------------------
	def previousPicture(self,msg):
		"""
		Displays the previous picture in the directory
		"""
		if self.currentPicture == 0:
			self.currentPicture = self.totalPictures - 1
		else:
			self.currentPicture -= 1
		self.loadImage(self.picPaths[self.currentPicture])
		
		
	#----------------------------------------------------------------------
	def updateImages(self, msg):
		"""
		Updates the picPaths list to contain the current folder's images
		"""
		self.picPaths = msg.data
		self.totalPictures = len(self.picPaths)

		for i in range(0,self.totalPictures):
			self.selectedPictures.append(False)

		self.loadImage(self.picPaths[0])
		
	#----------------------------------------------------------------------
	def selectPicture(self, msg):
		"""
		Select current picture and mark the corresponding list to True
		Change the label to selected
		"""
		self.selectedPictures[self.currentPicture] = True
		self.SetBackgroundColour(self.green)
		self.Refresh()


	def unselectPicture(self, msg):
		"""
		Unselect current picture and mark the corresponding list to False
		Set the label to unselected
		"""
		self.selectedPictures[self.currentPicture] = False
		self.SetBackgroundColour(self.softBlue)
		self.Refresh()

	def sendOrder(self, msg):

		"""
		Convert the selectedPictures list into string and send this string to the RadioThread Object
		Set all the elements in selectedPictures to false

		"""
		order = str(len(self.selectedPictures))

		for selection in self.selectedPictures:
			if selection is True:
				order = order + str(1)

			else:
				order = order + str(0)

		print("The array is {} and string is {}".format(self.selectedPictures,order))

		self.selectedPictures = [False for n in self.selectedPictures]
		print(self.selectedPictures)
		self.loadOrderSent()


########################################################################
class ViewerFrame(wx.Frame):

	#----------------------------------------------------------------------
	def __init__(self):
		wx.Frame.__init__(self, None, title="Image Viewer")
		panel = ViewerPanel(self)
		self.folderPath = ""
		Publisher.subscribe(self.resizeFrame, ("resize"))
		#Publisher().subscribe(self.resizeFrame, ("resize"))
		
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(panel, 1, wx.EXPAND)
		self.SetSizer(self.sizer)
		self.openDirectory()
		
		self.Show()
		#self.Maximize(True)
		#self.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)
		self.sizer.Fit(self)
		GestureThread()
		self.Center()
		

	def openDirectory(self):
		self.folderPath = os.getcwd()
		print(self.folderPath)
		picPaths = sorted(glob.glob(self.folderPath + "/img_src/" + "/0*.jpg"))
		print picPaths
		print(len(picPaths))
		Publisher.sendMessage("update images", picPaths)
		#Publisher().sendMessage("update images", picPaths)
		
	#----------------------------------------------------------------------
	def resizeFrame(self, msg):
		self.sizer.Fit(self)

main()