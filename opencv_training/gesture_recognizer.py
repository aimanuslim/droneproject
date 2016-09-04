#! usr/bin/python

import cv2
import numpy as np
import sys
import math

# Code based on tutorial on this website: http://creat-tabu.blogspot.my/2013/08/opencv-python-hand-gesture-recognition.html
# Using angle idea based on: http://simena86.github.io/blog/2013/08/12/hand-tracking-and-recognition-with-opencv/

#TODO:
# 1. Save state when there is no movement.
# 2. Use hand gesture recognition from the new guy

class Direction:
    right = 0
    left = 1

IMG_TO_BE_TESTED = "Hand-Gestures.jpg"
WIDTH = int(1280 * 0.9)
HEIGHT = int(720 * 0.9)
maxAngle = 80
frameToInspect = 250
# parameters for MOG2 module
backgroundRatio = 0.4
history = 200
complexityReductionThreshold = 0.05

# threshold params
thresh_lower = 150
gaussian_ksize = 11

bufferLength = 80
typicalDistance = 1000000
intervals = 13
scale = 1
waitTime = 1


lower = np.array([0, 30, 60], dtype = "uint8")
upper = np.array([20, 150, 255], dtype = "uint8")





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

def find3rdPoint(pt, center, i):
    if(pt[0] >= 0 and pt[0] < WIDTH and pt[1] >= 0 and pt[1] < HEIGHT):
        d = calcDistance(pt, center)
        dcos = d * math.cos(math.pi / 4) 
        dsin = d * math.sin(math.pi / 4)
        if(i == 3 or i == 0): px = pt[0] - dsin
        else: px = pt[0] + dsin  
        if(i == 0 or i == 1): py = center[1] + dcos
        else: py = center[1] - dcos
        return (int(px), int(py))
    else: return None    


def findDividingLine(box, center):
    p0, p1, p2, p3 = box[0], box[1], box[2], box[3]
    # print("Box points {} {} {} {}".format(p0, p1, p2, p3))

    r0 = find3rdPoint(p0, center, 0)
    r1 = find3rdPoint(p1, center, 1)
    r2 = find3rdPoint(p2, center, 2)
    r3 = find3rdPoint(p3, center, 3)

    arrR = [r0, r1, r2, r3]
    indices = [i for i, e in enumerate(arrR) if e is not None]
    arrR = [e for e in arrR if e is not None]
    # print arrR
    return arrR, indices
    


    xdelta = float(p3[0] - p2[0])
    ydelta = float(p3[1] - p2[1])
    if(xdelta == 0 and ydelta != 0):
        x23_center = p3[0]
        y23_center = center[1]
    elif(ydelta == 0 and xdelta != 0):
        x23_center = center[0]
        y23_center = p3[1]
    else:
        m23 = ydelta / xdelta
        m_center = - 1 / m23
        c_center = center[1] - center[0] * m_center
        c23 =  p3[1] - p3[0] * m23
        x23_center = (c23 - c_center) / (m23 - m_center)
        y23_center = m23 * x23_center + c23

    xdelta = float(p0[0] - p1[0])
    ydelta = float(p0[1] - p1[1])
    if(xdelta == 0 and ydelta != 0):
        x01_center = p0[0]
        y01_center = center[1]
    elif(ydelta == 0 and xdelta != 0):
        x01_center = center[0]
        y01_center = p0[1]
    else:
        m01 = ydelta / xdelta
        c01 = p0[1] - p0[0] * m01
        x01_center = (c01 - c_center) / (m01 - m_center)
        y01_center = m01 * x01_center + c01


    r1 = (x23_center, y23_center)
    r2 = (x01_center, y01_center)
    # print("First point: {}, Second point: {}".format((x23_center, y23_center), (x01_center, y01_center)))

    return r1, r2

   


def findLargestContour(contours):
    max_area = 0
    for i in range(len(contours)):
        contour = contours[i]
        area = cv2.contourArea(contour)
        if(area > max_area):
            max_area = area
            indexOfLargestContour = i

    largestContour = contours[indexOfLargestContour]
    return largestContour





def  gestureRecognize(ori, bgremoved, steadystatus):
    # skin masking according to color
    skinMask = cv2.cvtColor(ori, cv2.COLOR_BGR2HSV)
    skinMask = cv2.GaussianBlur(skinMask, (gaussian_ksize, gaussian_ksize), 0)
    skinMask = cv2.inRange(skinMask, lower, upper)
    skinMaskCopy = skinMask.copy()
    _, contours, hierarchy = cv2.findContours(skinMaskCopy, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    largestSkinContour = findLargestContour(contours)
    largestSkinMask = np.zeros(skinMask.shape, np.uint8)
    cv2.drawContours(largestSkinMask,[largestSkinContour],0,(255,255,255),-1)


    # skinMask = cv2.erode(skinMask, kernel, iterations=2)
    # showImg("skinMask", skinMask)
    # _, skinMask = cv2.threshold(skinMask, thresh_lower, 255, 0)
    
    # skinMask = cv2.cvtColor(skinMask, cv2.COLOR_HSV2BGR)
    # print(skinMask.shape)

    # dilation, erosion and multiplication
    kernel = np.ones((15,15),np.uint8)
    # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))
    rgb = cv2.cvtColor(bgremoved, cv2.COLOR_GRAY2BGR)
    openedMask = cv2.dilate(rgb, kernel, iterations=4)
    openedMask = cv2.dilate(openedMask, kernel, iterations=6)
    # openedMask = cv2.morphologyEx(rgb, cv2.MORPH_OPEN, kernel)
    openedMaskSingleChannel = cv2.cvtColor(openedMask, cv2.COLOR_BGR2GRAY)
    # openedMask = cv2.erode(rgb, kernel, iterations=1)
    # showImg("operated", openedMask)
    
    if(steadystatus == True): openedMask = cv2.bitwise_and(skinMask, largestSkinMask)
    else: openedMask = cv2.bitwise_and(openedMaskSingleChannel, skinMask, mask=largestSkinMask)
    
    # grayMask = cv2.cvtColor(openedMask, cv2.COLOR_BGR2GRAY)
    grayMask = openedMask.copy()
    openedMask = cv2.cvtColor(openedMask, cv2.COLOR_GRAY2BGR)
    _, contours, hierarchy = cv2.findContours(grayMask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if(len(contours) == 0): return ori, openedMask, (0,0), 0

    # find contour with largest area (may not be necessary)
    max_area = 0
    for i in range(len(contours)):
        contour = contours[i]
        area = cv2.contourArea(contour)
        if(area > max_area):
            max_area = area
            indexOfLargestContour = i

    if(max_area < 10000): return ori, openedMask, (0,0), 0
    # else: print("max_area {}".format(max_area))

    largestContour = contours[indexOfLargestContour]

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

    

    approxcontour = cv2.approxPolyDP(largestContour,0.01*cv2.arcLength(largestContour,True),True)

    # cv2.drawContours(openedMask, [approxcontour], 0, (0,255,0), 2)
    # cv2.drawContours(ori, [approxcontour], 0, (0,255,0), 2)

    x,y,w,h = cv2.boundingRect(largestContour)
    openedMask = cv2.rectangle(openedMask,(x,y),(x+w,y+h),(0,255,0),2)

    rect = cv2.minAreaRect(approxcontour)
    # width, height = rect[1]
    width, height = w, h
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    for i in range(0,4): 
        # print("{}: {}".format(i, box[i]))
        if(box[i][0] >= 0 and box[i][1] >= 0): 
            cv2.putText(openedMask, str(i), tuple(box[i]), cv2.FONT_HERSHEY_PLAIN, 1, (102,255,204), 2)
            
    arrR, id = findDividingLine(box, center)

    for i, r in zip(id,arrR):
        if(r[0] >= 0 and r[1] >= 0): 
            cv2.putText(openedMask, "r{}".format(i), r, cv2.FONT_HERSHEY_PLAIN, 1, (102,255,204), 2) 
            # cv2.line(openedMask, center, r, (0,0,204),2)        

    # if(r1[0] >= 0 and r1[1] >= 0): 
    #     # cv2.putText(openedMask, "r1", r1, cv2.FONT_HERSHEY_PLAIN, 1, (102,255,204), 2) 
    #     cv2.line(openedMask, center, r1, (102,255,204),2)
    # if(r2[0] >= 0 and r2[1] >= 0):  
    #     # cv2.putText(openedMask, "r2", r2, cv2.FONT_HERSHEY_PLAIN, 1, (102,255,204), 2) 
    #     cv2.line(openedMask, center, r2, (102,255,204),2)
    # cv2.drawContours(openedMask,[box],0,(255,102,102),2)
    cv2.drawContours(openedMask,[approxcontour],0,(255,102,102),2)

    

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
    if(convexityDefects == None or len(convexityDefects) == 0): return ori, openedMask, center, 0

    for i in range(convexityDefects.shape[0]):
        startingDefectidx, endingDefectidx, farthestPtfromconvexHullidx, defectDistance = convexityDefects[i, 0]
        startPt = tuple(approxcontour[startingDefectidx][0])
        endingPt = tuple(approxcontour[endingDefectidx][0])
        
        farthestPt = tuple(approxcontour[farthestPtfromconvexHullidx][0])
        
        distance = cv2.pointPolygonTest(approxcontour, center, True)

        convexlineVector = np.array(endingPt) - np.array(startPt)
        convexlineLength = np.sqrt(convexlineVector.dot(convexlineVector))

        lineLengthList.append(convexlineLength)
        startPtsList.append(startPt)
        endingPtList.append(endingPt)
        farthestPtsList.append(farthestPt)
        distanceList.append(defectDistance)

        # cv2.putText(ori, str(findAngle(farthestPt, startPt, endingPt)), farthestPt, cv2.FONT_HERSHEY_PLAIN, 1, (0,0,0), 2)


    lineLength_avg = sum(lineLengthList) / len(lineLengthList)
    distance_avg = sum(distanceList) / len(distanceList)
    # print "Distance avg: {0}".format(distance_avg)



    # orientation = determineHandOrientation(endingPtList, center)

    totalFingers = 0
    for s,e,f,l,d in zip(startPtsList, endingPtList, farthestPtsList, lineLengthList, distanceList):
        # print("{}, {}, {}".format(s, e, center))
        s_distance = calcDistance(s, center)
        e_distance = calcDistance(e, center)
        cv2.line(openedMask, s,e, [130,255,255], 2)

        if(s_distance > height * 0.3 and e_distance > height * 0.3 and l > height * 0.3 and findAngle(f,s,e) < maxAngle):
            cv2.circle(openedMask, s, 10, [0,255,255],2)
            cv2.circle(openedMask, e, 10, [0,255,255],2)

        if(findAngle(f,s,e) < 90):
            if(totalFingers == 0): totalFingers = 2
            else: totalFingers += 1
            cv2.circle(openedMask, f, 10, [0,0,255], 5)


        # print "Length now is {0}, Distance is {1}".format(l, d)
        # cv2.line(openedMask, s, f, [0,30,255],2) 
        # cv2.line(openedMask, f, e, [0,30,255],2) 


        # if l < lineLength_avg and d > distance_a zg:
            # print "Its drawn"


     
        # cv2.circle(ori, f, 5, [0,0,255], -1)
        # cv2.circle(openedMask, s, 10, [0,255,255],2)
        # cv2.circle(openedMask, e, 10, [0,255,255],2)
        
        # if(findAngle(f,s,e) < maxAngle and l < lineLength_avg * 1.3): 
        #     totalFingers += 1
        #     cv2.circle(openedMask, f, 5, [0,0,255], -1)
        #     cv2.line(openedMask, s, f, [0,255,0],2)
        #     cv2.line(openedMask, f, e, [0,255,0],2)


    return ori, openedMask, center, totalFingers

    # TODO:
    # do motion gesture detection, check if hand has moved fast enough
                    
    # print "Fingers count: {0}".format(totalFingers)
    # showImg("Convex hull and contour", rgbMask)

def calcDistance(pt1, pt2):
    # print(pt1)
    # print(pt2)
    # print("Here")
    d = (abs(pt1[0] - pt2[0]))**2 +  (abs(pt1[1] - pt2[1]))**2

    m = math.sqrt(d)
    return m

def videoRW(videoFileName):
    capturer = cv2.VideoCapture(videoFileName)
    fps = capturer.get(cv2.CAP_PROP_FPS)
    framect = capturer.get(cv2.CAP_PROP_FRAME_COUNT)
    print("Frames: ", framect," FPS: ", fps, " Length: ", framect / fps, " s")

    # not so good
    # backgroundSubtractor = cv2.bgsegm.createBackgroundSubtractorMOG()

    # better but need tweaking
    backgroundSubtractor = cv2.createBackgroundSubtractorMOG2(history=history, varThreshold=10, detectShadows=True)
    backgroundSubtractor.setComplexityReductionThreshold(complexityReductionThreshold)
    backgroundSubtractor.setBackgroundRatio(backgroundRatio)

    out = open("mov.txt", 'w')

    # finger extraction parameters
    center = None
    lastCenter = center
    lastSpeed = 0
    minDistance = 1000000
    maxDistance = 0
    
    # timing parameters
    minSpeed = 400
    slowMovementCounter = 0
    slow = False
    timeSlow = 0
    slowtimeLimit = 3
    minSpeed = 500

    noMovementCounter = 0
    steadyState = False
    maxUnmovedSpeed = 20
    steadytimeLimit = 30

    maxMovingCounter = 0

    i = 0
    while(True):
        ret, frame = capturer.read()
        frame = cv2.flip(frame, 0)
        framenum = capturer.get(cv2.CAP_PROP_POS_FRAMES)
        if( ret == 0 ): 
            capturer.release()
            out.close()
            return
        fgmask = backgroundSubtractor.apply(frame)
    

        drawnOriginal, drawnMasked, center, fingers = gestureRecognize(frame, fgmask, (steadyState or slow))

        d = 0
        s = 0
        if(lastCenter != None and center != (0,0)):
                direction = Direction.right if ((center[0] - lastCenter[0]) > 0) else Direction.left
                d = calcDistance(center, lastCenter)
                # d = d / scale  # scale
                t = (intervals / fps)
                s = d / t
                lastSpeed = s
        else: s = lastSpeed
        if(i % intervals == 0 and center != (0,0)):
            lastCenter = center


        if(s < minSpeed ):
            slowMovementCounter += 1
            timeSlow = slowMovementCounter / fps
            if(timeSlow < slowtimeLimit): 
                slow = True
                slowMovementCounter = 0
        else:
            slow = False

        if(s < maxUnmovedSpeed):
            noMovementCounter += 1
            timeUnmoved = noMovementCounter / fps
            if(timeUnmoved < steadytimeLimit):
                steadyState = True
                noMovementCounter = 0
        else: 
            steadyState = False






        i += 1
  

        cv2.namedWindow("Original", cv2.WINDOW_NORMAL)
        drawnOriginal = cv2.resize(drawnOriginal, (WIDTH,HEIGHT))
        cv2.moveWindow("Original", 30, 100)
        cv2.resizeWindow("Original", WIDTH, HEIGHT)

        cv2.namedWindow("Result", cv2.WINDOW_NORMAL)
        drawnMasked = cv2.resize(drawnMasked, (WIDTH,HEIGHT))
        cv2.moveWindow("Result", 100, 100)
        cv2.resizeWindow("Result", WIDTH, HEIGHT)


        
        cv2.putText(drawnMasked, "s: {}".format(int(s)), ((WIDTH - 200), (HEIGHT - 100)), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,255), 2)

        gesture = ''
        if(fingers == 2 and steadyState == True): gesture = 'SELECT'
        if(fingers == 5 and steadyState == True): gesture = 'SUBMIT'
        cv2.putText(drawnMasked, "finger gesture: {} count: {}".format(gesture, fingers), ((WIDTH - 500), (HEIGHT - 150)), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,255), 2)

        cv2.putText(drawnMasked, "frame: {}".format(math.floor(framenum)), ((WIDTH - 200), (HEIGHT - 200)), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,255), 2)


        moveColor = (s / 2000) * 255

        cv2.putText(drawnMasked, "SLOW!" if (slow) else "", ((WIDTH - 200), (HEIGHT - 50)), cv2.FONT_HERSHEY_PLAIN, 1, (0,140,255), 3)

        cv2.putText(drawnMasked, ("MOVED {}!".format('right' if direction == Direction.right else 'left')) if (not slow) else "", ((WIDTH - 200), (HEIGHT - 35)), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,140), 3)

        cv2.putText(drawnMasked, "STEADY" if (steadyState) else "", ((WIDTH - 200), (HEIGHT - 20)), cv2.FONT_HERSHEY_PLAIN, 1, (0,140,255), 3)


        out.write("{},{}\n".format(s,math.floor(framenum)))



        # cv2.imshow("Original", frame)
        # cv2.imshow("Mask", fgmask)
        cv2.imshow("Result", drawnMasked)
        # cv2.imshow("Original", drawnOriginal)
        if(cv2.waitKey(waitTime) == 27): exit()



if __name__ == "__main__":
    # videoRW('vids/testcase_cut.mp4')
    # videoRW('vids/testcase1.mov')
    # videoRW('vids/testcase5.mov')
    # videoRW('vids/testcase4.mp4')
    videoRW('vids/testcase2.mov')
    # videoRW('vids/testcase3.mov')
    # videoRW('vids/testcase_ext.mp4')



