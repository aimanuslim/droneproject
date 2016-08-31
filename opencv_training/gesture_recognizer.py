#! usr/bin/python

# Code based on tutorial on this website: http://creat-tabu.blogspot.my/2013/08/opencv-python-hand-gesture-recognition.html
# Using angle idea based on: http://simena86.github.io/blog/2013/08/12/hand-tracking-and-recognition-with-opencv/

# IMG_TO_BE_TESTED = "ok_sign.jpg"
# IMG_TO_BE_TESTED = "imagex01.jpg"


IMG_TO_BE_TESTED = "Hand-Gestures.jpg"
WIDTH = int(1920 * 0.4)
HEIGHT = int(1080 * 0.4)
maxAngle = 80
frameToInspect = 250
# parameters for MOG2 module
backgroundRatio = 0.4
history = 500
complexityReductionThreshold = 0.02
bufferLength = 80
typicalDistance = 1000000
intervals = 3

import cv2
import numpy as np
import sys
import math


print("OpenCV version: ", cv2.__version__)

# Constants for finding range of skin color in YCrCb
min_colorRange = np.array([235,235,235],np.uint8)
max_colorRange = np.array([256,256,256],np.uint8)

def showImg(winname, img, waitTime=0):
    img = cv2.resize(img, (WIDTH,HEIGHT))
    cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(winname, WIDTH, HEIGHT)
    cv2.imshow(winname, img)
    if cv2.waitKey(waitTime) == 27:
        sys.exit()
    cv2.destroyWindow(winname)




# returns a true if hand is oriented upwards, false otherwise (not necessary)
def determineHandOrientation(endingPtList, center):
    ptabovecentercount = 0
    ptbelowcentercount = 0
    for pt in  endingPtList:
        ypos = pt[1]
        if ypos < center[1]: ptabovecentercount += 1
        else: ptbelowcentercount += 1
    if ptabovecentercount > ptbelowcentercount: return True
    else: return False 

# helper functions
def normalize(v):
    norm=np.linalg.norm(v)
    if norm==0: 
       return v
    return v/norm

# p0 is the origin point
# p1 and p2 are the points the lines are going to from p0
def findAngle(p0, p1, p2):
    v1 = np.array(p1) - np.array(p0)
    v2 = np.array(p2) - np.array(p0)
    v1 = normalize(v1)
    v2 = normalize(v2)
    return math.acos(v1.dot(v2)) * (180 / math.pi)



def  gestureRecognize(ori, mask):
    # rgbMask = cv2.imread(inputImgName)
    rgbMask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    kernel = np.ones((5,5),np.uint8)
    openedMask = cv2.morphologyEx(rgbMask, cv2.MORPH_OPEN, kernel)
    grayMask = cv2.cvtColor(openedMask, cv2.COLOR_BGR2GRAY)


    _, contours, hierarchy = cv2.findContours(grayMask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # cv2.namedWindow("Img", cv2.WINDOW_NORMAL)
    # rImage = cv2.resize(openedMask, (WIDTH,HEIGHT))
    # cv2.moveWindow("Img", 500, 400)
    # cv2.resizeWindow("Img", WIDTH, HEIGHT)
    # cv2.imshow("Img", rImage)
    # cv2.waitKey(1)

    # showImg("contour after", img)

    if(len(contours) == 0): return ori, openedMask, (0,0)

    # find contour with largest area (may not be necessary)
    max_area = 0
    for i in range(len(contours)):
        contour = contours[i]
        area = cv2.contourArea(contour)
        if(area > max_area):
            max_area = area
            indexOfLargestContour = i

    if(max_area < 10000): return ori, openedMask, (0,0)
    # else: print("max_area {}".format(max_area))

    largestContour = contours[indexOfLargestContour]
    convexHull = cv2.convexHull(largestContour)

    # for cnt in contours:
    contourMoments = cv2.moments(largestContour)
    convexHull = cv2.convexHull(largestContour)
    if contourMoments['m00']!=0:
        cx = int(contourMoments['m10']/contourMoments['m00']) # cx = M10/M00
        cy = int(contourMoments['m01']/contourMoments['m00']) # cy = M01/M00
        
    center=(cx,cy)       
    cv2.circle(openedMask ,center,5,[255,255,0],2)
    # cv2.drawContours(openedMask, [largestContour], 0, (0,255,0), 2)
    # cv2.drawContours(openedMask, [convexHull], 0, (0,0,255), 2)

    cv2.circle(ori ,center,5,[255,255,0],2)
    # cv2.drawContours(ori, [largestContour], 0, (0,255,0), 2)
    # cv2.drawContours(ori, [convexHull], 0, (0,0,255), 2)    

    

    approxcontour = cv2.approxPolyDP(largestContour,0.008*cv2.arcLength(largestContour,True),True)

    cv2.drawContours(openedMask, [approxcontour], 0, (0,255,0), 2)
    cv2.drawContours(ori, [approxcontour], 0, (0,255,0), 2)


    # showImg("output image so far", rgbMask)
    hullIndices = cv2.convexHull(approxcontour, returnPoints=False)   
    convexityDefects = cv2.convexityDefects(approxcontour, hullIndices)


    minDistance = 0
    maxDistance = 0

    lineLengthList = []
    farthestPtsList = []
    startPtsList = []
    endingPtList = []
    distanceList = []

    i = 0
    if(convexityDefects == None or len(convexityDefects) == 0): return ori, openedMask, center

    for i in range(convexityDefects.shape[0]):
        startingDefectidx, endingDefectidx, farthestPtfromconvexHullidx, defectDistance = convexityDefects[i, 0]
        startPt = tuple(approxcontour[startingDefectidx][0])
        endingPt = tuple(approxcontour[endingDefectidx][0])
        
        farthestPt = tuple(approxcontour[farthestPtfromconvexHullidx][0])
        distance = cv2.pointPolygonTest(approxcontour, center, True)

        convexlineVector = np.array(endingPt) - np.array(startPt)
        convexlineLength = np.sqrt(convexlineVector.dot(convexlineVector))
        # print "convex line {0} has length {1}".format(i,convexlineLength)
        lineLengthList.append(convexlineLength)
        startPtsList.append(startPt)
        endingPtList.append(endingPt)
        farthestPtsList.append(farthestPt)
        distanceList.append(defectDistance)
        cv2.putText(ori, str(findAngle(farthestPt, startPt, endingPt)), farthestPt, cv2.FONT_HERSHEY_PLAIN, 1, (0,0,0), 2)



    lineLength_avg = sum(lineLengthList) / len(lineLengthList)
    distance_avg = sum(distanceList) / len(distanceList)
    # print "Distance avg: {0}".format(distance_avg)
    totalFingers = 1


    # orientation = determineHandOrientation(endingPtList, center)

    for s,e,f,l,d in zip(startPtsList, endingPtList, farthestPtsList, lineLengthList, distanceList):
        # print "Length now is {0}, Distance is {1}".format(l, d)
        cv2.line(ori, s, e, [0,255,0],2)
        cv2.line(openedMask, s, e, [0,255,0],2)
        if l < lineLength_avg and d > distance_avg:
            # print "Its drawn"
            cv2.circle(ori, s, 10, [0,255,255],2)
            cv2.circle(ori, e, 10, [0,255,255],2)
            cv2.circle(ori, f, 5, [0,0,255], -1)
            cv2.circle(openedMask, s, 10, [0,255,255],2)
            cv2.circle(openedMask, e, 10, [0,255,255],2)
            cv2.circle(openedMask, f, 5, [0,0,255], -1)
        if(findAngle(f,s,e) < maxAngle): totalFingers += 1

    return ori, openedMask, center

    # TODO:
    # do motion gesture detection, check if hand has moved fast enough
                    
    # print "Fingers count: {0}".format(totalFingers)
    # showImg("Convex hull and contour", rgbMask)

def distance(pt1, pt2):
    # print(pt1)
    # print(pt2)
    d = abs(pt1[0] - pt2[0])**2 +  abs(pt1[1] - pt2[1])**2
    m = math.sqrt(d)
    return d

def videoRW(videoFileName):
    capturer = cv2.VideoCapture(videoFileName)
    fps = capturer.get(cv2.CAP_PROP_FPS)
    framect = capturer.get(cv2.CAP_PROP_FRAME_COUNT)
    # print "Frames: {0} FPS: {1} Length: {2} s".format(framect, fps, framect / fps)
    print("Frames: ", framect," FPS: ", fps, " Length: ", framect / fps, " s")

    backgroundSubtractor = cv2.createBackgroundSubtractorMOG2(history=history)
    backgroundSubtractor.setComplexityReductionThreshold(complexityReductionThreshold)
    backgroundSubtractor.setBackgroundRatio(backgroundRatio)

    center = None
    lastCenter = center
    minDistance = 1000000
    maxDistance = 0

    i = 0
    while(True):
        ret, frame = capturer.read()
        if( ret == 0 ): 
            capturer.release()
            out.release()
            return
        fgmask = backgroundSubtractor.apply(frame)
        # print("Frame number: ", capturer.get(cv2.CAP_PROP_POS_FRAMES))
    # if(capturer.get(cv2.CAP_PROP_POS_FRAMES)  > frameToInspect and capturer.get(cv2.CAP_PROP_POS_FRAMES)  > (frameToInspect + 2)): 
        # histr = cv2.calcHist([fgmask],[0],None,[256],[0,256])
        # minVal, maxVal, _, _ = cv2.minMaxLoc(histr) 
        # print("minVal for {} is {}, maxVal for {} is {}".format(0, minVal, 0, maxVal))

        drawnOriginal, drawnMasked, center = gestureRecognize(frame, fgmask)

        d = 0
        if(lastCenter != None):
                d = distance(center, lastCenter) 
        if(i % intervals == 0 and center != (0,0)):
            lastCenter = center

        i += 1
        # if(centerFIFO == None): 
        #     if(center != (0,0)): centerFIFO = [center for i in range(0,bufferLength)]
        # else: 
        #     if(center != (0,0)): centerFIFO = centerFIFO[1:bufferLength]+ [center]

        # fd = 0
        # if(centerFIFO != None):
        #     maxDistance = 0
        #     d = 0
        #     for i, p1 in enumerate(centerFIFO):
        #             d = distance(p1, center)
        #             if(d > typicalDistance * 0.7): 
        #                 fd = abs(bufferLength - i)
        #                 maxDistance = d
                        # if(d > 1500000 and fd > 50): 
                        #     pass
                        #     # print("Distance moved: {} Frame distance: {} Current frame: {}".format(d, fd, capturer.get(cv2.CAP_PROP_POS_FRAMES)))





        # if(avgDist > 250000):
        #     print("Movement detected")
        # else: print("Average distance {}".format(avgDist))

        # print("Average distance {}".format(avgDist))




        # cv2.namedWindow("Original", cv2.WINDOW_NORMAL)
        # frame = cv2.resize(frame, (WIDTH,HEIGHT))
        # cv2.moveWindow("Original", 500, 400)
        # cv2.resizeWindow("Original", WIDTH, HEIGHT)
        
        # cv2.namedWindow("Mask", cv2.WINDOW_NORMAL)
        # fgmask = cv2.resize(fgmask, (WIDTH,HEIGHT))
        # cv2.moveWindow("Mask", 100, 400)
        # cv2.resizeWindow("Mask", WIDTH, HEIGHT)

        cv2.namedWindow("Original", cv2.WINDOW_NORMAL)
        drawnOriginal = cv2.resize(drawnOriginal, (WIDTH,HEIGHT))
        cv2.moveWindow("Original", 30, 100)
        cv2.resizeWindow("Original", WIDTH, HEIGHT)

        cv2.namedWindow("Result", cv2.WINDOW_NORMAL)
        drawnMasked = cv2.resize(drawnMasked, (WIDTH,HEIGHT))
        cv2.moveWindow("Result", 600, 100)
        cv2.resizeWindow("Result", WIDTH, HEIGHT)


        waitTime = 1
        cv2.putText(drawnMasked, "d: {}".format(d), ((WIDTH - 200), (HEIGHT - 100)), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 2)

        cv2.putText(drawnMasked, "lastCenter: {}".format(lastCenter), ((WIDTH - 200), (HEIGHT - 200)), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 2)

        cv2.putText(drawnMasked, "center: {}".format(center), ((WIDTH - 200), (HEIGHT - 300)), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 2)


        # cv2.imshow("Original", frame)
        # cv2.imshow("Mask", fgmask)
        cv2.imshow("Result", drawnMasked)
        cv2.imshow("Original", drawnOriginal)
        if(cv2.waitKey(waitTime) == 27): exit()
        if(cv2.waitKey(waitTime) == 70): cv2.waitKey(0)


        # print("{}".format(result.shape))
        
        # color = ('b','g','r')
        # for i,col in enumerate(color):
        

        # showImg("FG", fgmask)

    capturer.release()


    



if __name__ == "__main__":
    videoRW('vids/testcase1.mov')



