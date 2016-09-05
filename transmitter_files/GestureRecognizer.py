#! usr/bin/python

import cv2
import numpy as np
import sys
import math


# CONSTANTS
UNLOCATED = (0,0)
# MINCONTOURSIZE = 100000
MINCONTOURSIZE = 100000 / 6
NOCONTOURFOUND = None

# drawing parameters
FILLCONTOURS = -1
WHITE = (255,255,255)
RED = (0,0,255)
WIDTH = int(1280 * 0.9)
HEIGHT = int(720 * 0.9)

# Gaussian blur parameters
gaussian_ksize = 11

# skin extraction
lower = np.array([0, 30, 60], dtype = "uint8")
upper = np.array([20, 150, 255], dtype = "uint8")

# background subtractor parameters
backgroundRatio = 0.4
history = 200
complexityReductionThreshold = 0.05
varThreshold = 10
kernel_dim = 15

# frame analysis parameters
newCenterInterval = 13
steadySpeed = 5 
barelyMovingSpeed = 13
minNoMovementTimeLimit = 5
# minMovementTimeLimit = 10

# convex hull operations constants
epsilon = 0.01

# finger counting parameters
maxFingergapAngle = 90


class HandState:
	steady = 0
	barelyMoving = 1
	movingFast = 2
	absent = 3

class Gesture:
	select = 1
	submit = 2
	incomprehensible = 0

class GestureRecognizer:
	

	def __init__(self, verbose):

		self.verbose_mode = verbose
		self.initializebgSubtractor()
		self.skinMask = None
		self.largestSkinMask = None
		self.movementMask = None
		self.resultMask = None
		self.handCenter = None
		self.lastHandCenter = None
		self.handCenterSpeed = None
		self.lastHandCenterSpeed = None
		self.handState = HandState.barelyMoving
		self.largestResultContour = None
		self.videoObj = None
		self.fps = 0
		self.totalframes = 0
		self.intervalCounter = 0
		self.noMovementCounter = 0
		self.movementCounter = 0
		self.handMovementDirection = None
		self.currentgesture = Gesture.incomprehensible
		self.fingerCount = 0
		# self.determineMovementDelay = 0
		# self.movementDelayLimit = 4

	def normalize(self,v):
		norm=np.linalg.norm(v)
		if norm==0: 
			return v
		return v/norm

	def calcDistance(self, pt1, pt2):
		d = (abs(pt1[0] - pt2[0]))**2 +  (abs(pt1[1] - pt2[1]))**2
		m = math.sqrt(d)
		return m


	def initializebgSubtractor(self):
		self.bgSubtractor = cv2.createBackgroundSubtractorMOG2(history=history,varThreshold=varThreshold, detectShadows=True)
		self.bgSubtractor.setComplexityReductionThreshold(complexityReductionThreshold)
		self.bgSubtractor.setBackgroundRatio(backgroundRatio)

	def videoinit(self, video):
		self.videoObj = cv2.VideoCapture(video)
		self.videoObj.set(cv2.CAP_PROP_FPS, 30)
		#self.videoObj.open(video)
		if(self.verbose_mode): 
			if not self.videoObj.isOpened():
				print("Video failed to open!")
				self.exit()
		#self.fps = 10
		self.fps = self.videoObj.get(cv2.CAP_PROP_FPS) * 0.1
		# self.totalframes = self.videoObj.get(cv2.CAP_PROP_FRAME_COUNT)
		print("Listening.....")

	def readVideo(self):
		ret, frame = self.videoObj.read()
		if(not ret): 
			print("Failed to read frame")
			self.exit()
		if(self.verbose_mode):
			pass
			# print("Reading frame {} of video with {} FPS".format(self.videoObj.get(cv2.CAP_PROP_POS_FRAMES), self.fps))

		# winname =  "Frame"
		# img = frame
		# cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
		# cv2.resizeWindow(winname, WIDTH, HEIGHT)
		# cv2.imshow(winname, img)
		# print "."
		return frame

	def extractSkinContour(self, frame):
		frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
		frame = cv2.GaussianBlur(frame, (gaussian_ksize, gaussian_ksize), 0)
		self.skinMask = cv2.inRange(frame, lower, upper)
		skinMaskcopy = self.skinMask.copy()
		_, skinContours, hierarchy = cv2.findContours(skinMaskcopy, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
		largestSkinContour = self.findLargestContour(skinContours)
		self.largestSkinMask = np.zeros(self.skinMask.shape, np.uint8)
		cv2.drawContours(self.largestSkinMask,[largestSkinContour],0,WHITE,FILLCONTOURS)


	def subtractBackground(self, frame):
		self.foreground = self.bgSubtractor.apply(frame)


	def foregroundErosionAndDilations(self):
		kernel = np.ones((kernel_dim, kernel_dim), np.uint8)
		self.foreground = cv2.dilate(self.foreground, kernel, iterations=4)
		self.foreground = cv2.dilate(self.foreground, kernel, iterations=6)

	def multiplyMasks(self):
		if(self.handState == HandState.steady):
			self.resultMask = cv2.bitwise_and(self.skinMask, self.largestSkinMask)
		else:
			self.resultMask = cv2.bitwise_and(self.foreground, self.skinMask, mask=self.largestSkinMask)

	
	def findHandCenter(self):
		contourMoments = cv2.moments(self.largestResultContour)
		if contourMoments['m00']!=0:
			cx = int(contourMoments['m10']/contourMoments['m00']) # cx = M10/M00
			cy = int(contourMoments['m01']/contourMoments['m00']) # cy = M01/M00
		self.handCenter=(cx,cy)  

	def findLargestContour(self, contours):
		max_area = 0
		for i in range(len(contours)):
			contour = contours[i]
			area = cv2.contourArea(contour)
			if(area > max_area):
				max_area = area
				indexOfLargestContour = i

		if(max_area < MINCONTOURSIZE): return NOCONTOURFOUND

		largestContour = contours[indexOfLargestContour]
		return largestContour

	def determineHandMovement(self):
		handCenterSpeed = 0
		self.handMovementDirection = None
		if(self.lastHandCenter != None and self.handCenter != UNLOCATED):
			self.handMovementDirection = 'right' if ((self.handCenter[0] - self.lastHandCenter[0]) > 0) else 'left'
			distance = self.calcDistance(self.handCenter, self.lastHandCenter)
			timeInterval = (newCenterInterval / self.fps)
			self.handCenterSpeed = distance / timeInterval
			self.lastHandCenterSpeed = self.handCenterSpeed
		else: self.handCenterSpeed = self.lastHandCenterSpeed

		if(self.intervalCounter % newCenterInterval == 0 and self.handCenter != UNLOCATED):
			self.lastHandCenter = self.handCenter

		if(self.handCenterSpeed < steadySpeed):
			self.noMovementCounter += 1
			self.movementCounter = 0
			noMovementTime = self.noMovementCounter / self.fps
			if(noMovementTime > minNoMovementTimeLimit):
				self.handState = HandState.steady
				self.noMovementCounter = 0
		elif(self.handCenterSpeed > barelyMovingSpeed):
			# self.movementCounter += 1
			self.noMovementCounter = 0
			# movementTime = self.movementCounter / self.fps
			# if(movementTime > minMovementTimeLimit):
			self.handState = HandState.movingFast
			# self.movementCounter = 0
		else: 
			self.noMovementCounter = 0
			self.movementCounter = 0
			self.handState = HandState.barelyMoving


	def findAngle(self, p0, p1, p2):
		v1 = np.array(p1) - np.array(p0)
		v2 = np.array(p2) - np.array(p0)
		v1 = self.normalize(v1)
		v2 = self.normalize(v2)
		return math.acos(v1.dot(v2)) * (180 / math.pi)


	def determineGesture(self):
		self.fingerCount = 0
		approxcontour = cv2.approxPolyDP(self.largestResultContour,epsilon*cv2.arcLength(self.largestResultContour,True),True)
		self.findConvexityDefects(approxcontour)
		if(self.convexityDefects == None or len(self.convexityDefects) == 0): return Gesture.incomprehensible

		

		farthestPtsList = []
		startPtsList = []
		endingPtList = []
		distanceList = []

		for i in range(self.convexityDefects.shape[0]):
			startingDefectidx, endingDefectidx, farthestPtfromconvexHullidx, defectDistance = self.convexityDefects[i, 0]
			startPt = tuple(approxcontour[startingDefectidx][0])
			endingPt = tuple(approxcontour[endingDefectidx][0])        
			farthestPt = tuple(approxcontour[farthestPtfromconvexHullidx][0])

			if(self.findAngle(farthestPt, startPt, endingPt) < maxFingergapAngle):
				if(self.fingerCount == 0):
					self.fingerCount += 2
				else:
					self.fingerCount += 1

		if(self.fingerCount == 3 and self.handState == HandState.steady): self.currentgesture = Gesture.select
		elif(self.fingerCount > 4 and self.handState == HandState.steady): self.currentgesture = Gesture.submit
		else: 
			self.currentgesture = Gesture.incomprehensible
		return self.currentgesture




	def findConvexityDefects(self,contour):
		hullIndices = cv2.convexHull(contour, returnPoints=False)
		self.convexityDefects = cv2.convexityDefects(contour, hullIndices)



	def recognize(self, frame):
		if(frame == None): return 
		self.extractSkinContour(frame)
		self.subtractBackground(frame)
		self.foregroundErosionAndDilations()
		self.multiplyMasks()

		resultMaskcopy = self.resultMask.copy()
		_, contours, hierarchy = cv2.findContours(resultMaskcopy, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

		if(len(contours) == 0): 
			self.handCenter = UNLOCATED
			self.handCenterSpeed = 0
			self.handState = HandState.absent
			self.fingerCount = 0
			return Gesture.incomprehensible
		else: 
			self.largestResultContour = self.findLargestContour(contours)
			if(self.largestResultContour == NOCONTOURFOUND): 
				self.handCenter = UNLOCATED
				self.handCenterSpeed = 0
				self.handState = HandState.absent
				self.fingerCount = 0
				return Gesture.incomprehensible 

		self.findHandCenter()
		self.determineHandMovement()

		# if self.determineMovementDelay <= 2:
		# 	self.determineHandMovement()
		# 	self.determineMovementDelay += 1

		# else:
		# 	if self.determineMovementDelay == self.movementDelayLimit:
		# 		self.determineMovementDelay = 0
		# 	else:
		# 		self.determineMovementDelay += 1

		return self.handMovementDirection if self.handState == HandState.movingFast else self.determineGesture()


	def showProcessedFrames(self):
		winname = "Result"
		img = self.resultMask.copy()
		img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
		img = cv2.resize(img, (WIDTH,HEIGHT))
		cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
		cv2.resizeWindow(winname, WIDTH, HEIGHT)

		text = ''
		if(self.currentgesture == Gesture.select): text = "SELECT"
		if(self.currentgesture == Gesture.submit): text = "SUBMIT"
		if(self.currentgesture == Gesture.incomprehensible and self.handState == HandState.movingFast): text = self.handMovementDirection
		cv2.putText(img, text,(WIDTH - 200, HEIGHT - 125), cv2.FONT_HERSHEY_SIMPLEX, 1, RED, 3)
		cv2.putText(img, "no movement time: {}".format(self.noMovementCounter / self.fps),(WIDTH - 400, HEIGHT - 25), cv2.FONT_HERSHEY_SIMPLEX, 1, RED, 1)
		cv2.putText(img, "hand speed: {}".format(self.handCenterSpeed),(WIDTH - 400, HEIGHT - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, RED, 1)
		cv2.putText(img, "movement time: {}".format(self.movementCounter / self.fps),(WIDTH - 400, HEIGHT - 75), cv2.FONT_HERSHEY_SIMPLEX, 1, RED, 1)
		cv2.putText(img, "finger count: {}".format(self.fingerCount),(WIDTH - 400, HEIGHT - 105), cv2.FONT_HERSHEY_SIMPLEX, 1, RED, 1)


		cv2.imshow(winname, img)
		if(cv2.waitKey(1) == 27): self.exit()

	def exit(self):
		self.videoObj.release()
		exit()




if __name__ == "__main__":
	gr = GestureRecognizer(False)
	gr.videoinit('vids/testcase5.mov')
	while(True):
		gesture = gr.recognize(gr.readVideo())
		if(gr.verbose_mode): gr.showProcessedFrames()
	















