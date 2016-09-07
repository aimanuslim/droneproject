#!/usr/bin/env python

import time
import os
import wx
import Queue
import socket
import sys
import wx.grid as gridlib
from threading import Thread
from wx.lib.pubsub import pub
import wx.lib.agw.fourwaysplitter as fws

MENU = ["Espresso", "Caffe Latte", "Cappuccino", "Americano", "Caffe Mocha", "Cafe au Lait"]

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
		self.receivedMessage = ""

		self.serverIP = "192.168.150.1"
		self.port = 11850
		self.msgSize = 1024
		self.clientSocket = socket.socket()
		self.start()
	
	def run(self):
		while True:
			try:
				print("Trying")
				self.clientSocket.connect((self.serverIP,self.port))
			except:
				print("Server not started yet. Sleeping....")
				time.sleep(5)
				continue

			print("Connected to server!")
			break

		while True:
			self.receivedMessage = self.clientSocket.recv(self.msgSize)
			if self.receivedMessage is "":
				continue
			
			else:
				self.messageQueue.put(self.receivedMessage)
				wx.CallAfter(pub.sendMessage,"update panel",message = self.messageQueue.get())


class OrderPanel(wx.Panel):
	def __init__(self,splitter,count):
		wx.Panel.__init__(self,splitter)
		self.color = "#46C6F3"
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
		self.color = "#46C6F3"
		self.selectedColor = "#09C595"

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
			panel.SetBackgroundColour(self.color)

		self.orderPanels[self.currentPanel].orderInfo.SetLabel(orderList)
		self.orderPanels[self.currentPanel].SetBackgroundColour(self.selectedColor)
		self.orderPanels[self.currentPanel].orderNumberInfo.SetLabel("# " + str(self.currentOrder))

		self.currentOrder = self.currentOrder + 1
		self.currentPanel = self.currentPanel + 1

		if self.currentPanel > 3:
			self.currentPanel = 0
		
main()


