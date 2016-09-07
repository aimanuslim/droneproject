#!/usr/bin/env python

import glob
import os
import wx
import sys
import time
import socket
from threading import Thread
from wx.lib.pubsub import setuparg1
from wx.lib.pubsub import pub as Publisher
import wx.lib.agw.pybusyinfo as PBI
from GestureRecognizer import * 

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
		Thread.__init__(self)
		self.latency = 0
		self.start()

	def run(self):
		"""
		Place your openCV processing codes in here
		Currently the codes in here are just for testing
		"""

		# gr = GestureRecognizer(True)
		# counter = 0
		# commandExecuted = False
		# #gr.videoinit("/dev/video0")
		# gr.videoinit(-1)
		# while(True):
		# 	gesture = gr.recognize(gr.readVideo())

		# 	# if gr.handCenterSpeed != 0: print "Speed: {}".format(gr.handCenterSpeed)
		# 	#print "Steady time: {} Finger count: {}".format(gr.noMovementCounter, gr.fingerCount)

		# 	# gr.showProcessedFrames()
		# 	# timeoutCounter += 1
		# 	# if timeoutCounter > timeoutLimit: timeout = True
		# 	if(not commandExecuted):
		# 		if(gesture == Gesture.select): 
		# 			print("Made selection")
		# 			wx.CallAfter(Publisher.sendMessage,"make selection","")
		# 			wx.MilliSleep(self.latency)
		# 			commandExecuted = True
				
		# 		elif(gesture == Gesture.submit): 
		# 			print("Sent order")
		# 			wx.CallAfter(Publisher.sendMessage,"send order","")
		# 			wx.MilliSleep(self.latency)
		# 			time.sleep(3)
		# 			commandExecuted = True	
				
		# 		elif(gr.handState == HandState.movingFast):
		# 			if(gr.handMovementDirection == 'right'):
		# 				print("PREVIOUS PIC!")
		# 				wx.CallAfter(Publisher.sendMessage,"previous picture","")
		# 				wx.MilliSleep(self.latency)
		# 			else:
		# 				print("NEXT PIC!")
		# 				wx.CallAfter(Publisher.sendMessage,"next picture","")
		# 				wx.MilliSleep(self.latency)
		#  					# command = Command.RIGHT if gr.handMovementDirection == 'right' else Command.LEFT
		#  			commandExecuted = True
	 # 		else:
	 # 			counter += 1
	 # 			if(counter > 20):
	 # 				counter = 0
	 # 				commandExecuted = False
	 # 				print("counter reset")






		# Testing code down here...
		for i in range(1,1000):
			time.sleep(1)
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

class WifiClass(Thread):
	def __init__(self):
		Thread.__init__(self)

		self.serverSocket = socket.socket()
		self.port = 11850
		self.serverSocket.bind(("",self.port))
		self.serverSocket.listen(5)
		self.clientSocket = ""
		self.clientAddr = ""
		self.start()

	def run(self):
		print("wifiAdapter ready to transmit...")
		self.clientSocket, self.clientAddr = self.serverSocket.accept()
	
	def sendToClient(self, msg):
		self.clientSocket.send(msg)
		print("Sent {} to Client!".format(msg))


class ViewerPanel(wx.Panel):

	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		width, height = wx.DisplaySize()
		print("Screen is {} x {}".format(width,height))
		self.softBlue = "#46C6F3"
		self.green = "#09C595"
		self.picPaths = []
		self.currentPicture = 0
		self.selectedPictures = []
		self.totalPictures = 0
		self.photoMaxSize = width - 800
		print("photomax size is {}".format(self.photoMaxSize))

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
		Publisher.subscribe(self.makeSelection,("make selection"))
		print("Subscribed to makeSelection")

		self.layout()
		self.wifiAdapter = WifiClass()
		
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

	def loadOrderSent(self,order):
		print("Entered order sent!")

		self.wifiAdapter.sendToClient(order)

		dlgTitle = "Processing order"
		dlgMessage = "Please be patient while we process your order"
		maxProg = 12
		dlg = wx.ProgressDialog(dlgTitle, dlgMessage, maximum=maxProg)

		for i in range(0,12):
			wx.MilliSleep(250)
			dlg.Update(i)

		dlg.Destroy()

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
		Convert the selectedPictures list into string and send this string to the WifiClass Object
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
		self.loadOrderSent(order)

	def makeSelection(self,msg):
		if self.selectedPictures[self.currentPicture] is True:
			self.unselectPicture("")

		else:
			self.selectPicture("")


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
		self.Maximize(True)
		#self.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)
		self.sizer.Fit(self)
		GestureThread()
		self.Center()
		

	def openDirectory(self):
		self.folderPath = os.getcwd()
		print(self.folderPath)
		picPaths = sorted(glob.glob(self.folderPath + "/img_src/" + "/0*.jpg"))
		# print picPaths
		# print(len(picPaths))
		Publisher.sendMessage("update images", picPaths)
		#Publisher().sendMessage("update images", picPaths)
		
	#----------------------------------------------------------------------
	def resizeFrame(self, msg):
		self.sizer.Fit(self)

main()
