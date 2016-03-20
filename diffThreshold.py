# second try : use diff with fixed first frame + threshold

# Usage : shapesVideo inputVideoFile [ outputFile ]
# during replay :
#  hit 'q' to exit
#  hit 's' to save current frame with annotations
#  hit 'i' to get info on pathes
#  hit 'm' to get info on moments
 
import numpy as np
import cv2
from sys import argv
from time import sleep

inputFile = argv[1]

# resize video (too fit my screen, and reduce cpu work)
scale = 0.5
# limit between black (0) and white (255) to convert un BW picture
bgThreshold = 50

# if distance between a point and last position in a path is lower,
# consider it as path element 
pathThreshold = 50
# if distance is lower, don't add the point to the path, to avoid huge polylines
pathSubThreshold = 5

# every "refresh" frames, clean pathes which didn't changed since previous one
refreshPathRate = 50

# percent in Y coordinate for "ingoing line" and "outgoing line"
# 0 being top of image
limitIn = 10
limitOut = 85

nbIn = 0
nbOut = 0

# raw capture
cap = cv2.VideoCapture(inputFile)

# read first frame
ret, firstFrame = cap.read()
firstFrame = cv2.resize(firstFrame, (0,0), fx=scale, fy=scale)

# TODO : why 0 0 0 ??????
w = firstFrame.shape[1]
#cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
h = firstFrame.shape[0]
#cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)

fps = cap.get(cv2.cv.CV_CAP_PROP_FPS)
if fps == 0:
    fps = 25
fcc = cap.get(cv2.cv.CV_CAP_PROP_FOURCC)
if fcc == 0:
    fcc = cv2.cv.CV_FOURCC(*'XVID')
print "video {} {}x{} @ {}".format(fcc, w, h, fps)

# image size is known => deduce real Y limits
limitIn  = h * limitIn  / 100
limitOut = h * limitOut / 100

cv2.line(firstFrame, (0, limitIn), (w, limitIn), (0, 255, 0), 3)
cv2.line(firstFrame, (0, limitOut), (w, limitOut), (0, 0, 255), 3)
cv2.imshow("background", firstFrame)
k = cv2.waitKey(0)
cv2.destroyWindow("background")

if len(argv) > 2:
    outputFile = argv[2]
    out = cv2.VideoWriter(
            outputFile,
            fcc, fps,
            (w*scale, h*scale)
    )
else:
    outputFile = False

# approximation level of contour recognition
kSize = 15
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kSize, kSize)) #np.ones((5,5),np.uint8)

maxContours = 0
biggestContour = 0
frameNumber = 0

# list of dictionaries, where each entry has folling keys :
# line = polyline coordinates showing this follower path
# x, y : last seen position (=line[-1])
# f : last seen frame number
# x0, y0 : first seen coordinates (=line[0])
followers = []

#def trajectory(path):

def closeTo(p1, p2, threshold):
    return  ( abs(p1[0] - p2[0]) < threshold ) \
        and ( abs(p1[1] - p2[1]) < threshold )

def searchFollower(frameNumber, x, y):
    global followers
    for f in followers:
        if closeTo((f['x'], f['y']), (x, y), pathThreshold):
            if not closeTo((f['x'], f['y']), (x, y), pathSubThreshold):
                f['line'].append([x,y])
            else:
                f['line'][-1] = [x,y]
            f['f'] = frameNumber
            f['x'] = x
            f['y'] = y
            #trajectory(f)
            return

    #not found -> create new one
    followers.append({
        'f'  : frameNumber,
        'x0' : x,
        'y0' : y,
        'x'  : x,
        'y'  : y,
        'line': [[x, y]]
    })


def refreshPath(ttl):
    global followers, frameNumber, refreshPathRate
    global nbOut, nbIn

    print "refreshPath", ttl, "on", len(followers), "elements"
    newFollowers = []
    for f in followers:
        if f['f'] > ttl:
            newFollowers.append(f)
        else:
            if f['y0'] < limitIn and f['y'] > limitOut:
                nbOut = nbOut + 1
                print "### -1 =>", nbOut
            elif f['y0'] > limitOut and f['y'] < limitIn:
                nbIn = nbIn + 1
                print "### +1 =>", nbIn
            
    followers = newFollowers
    print "=>", len(followers)


while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (0,0), fx=scale, fy=scale)

    frameNumber += 1

    if (frameNumber % refreshPathRate) == 0:
        refreshPath(frameNumber - refreshPathRate / 2)

    k = cv2.waitKey(1) & 0xFF;
    if k == ord('q'):
        print "Break at frame", frameNumber
        break
    elif k == ord('s'):
        cv2.imwrite("{}_{}.png".format(argv[1], frameNumber), frame)
    
    # get "movement part" of image
    #- make diff with bg
    fgmask = cv2.absdiff(firstFrame, frame)
    #- blur it
    img = cv2.blur(fgmask, (25,25))
    #- enhance each color
    ret,img = cv2.threshold(img, bgThreshold, 255, cv2.THRESH_BINARY)
    #- convert to gray (needed y contour detection)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #- force to threshold
    ret,img = cv2.threshold(img, bgThreshold, 255, cv2.THRESH_BINARY)
    cv2.imshow('fgmask', img)

    # find contours Into it
    contours,h = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #contours,h = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_L1)

    # statistics about number of contours + max number of segments in them
    if len(contours) > maxContours:
        maxContours = len(contours)
    for cnt in contours:
        if len(cnt) > biggestContour:
            biggestContour = len(cnt)

#    cv2.drawContours(frame, contours, -1, (255, 0, 0), 1)
    for i,cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > 300:
            perim = cv2.arcLength(cnt, True)
            M = cv2.moments(cnt)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            
            cv2.drawContours(frame, [cnt], 0, (0, 255, 0), 1)
            cv2.circle(frame, (cx, cy), 5, (0,0,255), -1)

            searchFollower(frameNumber, cx, cy)

            if k == ord('i'):
                print "frame", frameNumber, ": contour", i, "A=", area, "P=", perim, "center=", cx, "x", cy
                cv2.imwrite("{}_{}_i.png".format(argv[1], frameNumber), frame)
#         approx = cv2.approxPolyDP(cnt, 0.05 * perim, True)
#         cv2.drawContours(frame, [approx], 0, (0, 255, 0), 1)

    # draw followers
    for f in followers:
        pts = np.array(f['line'], np.int32)
        pts = pts.reshape((-1,1,2))
        cv2.polylines(frame, [pts], False, (255,255,255))

    if k == ord('m'):
        for cnt in contours:
            print cv2.moments(cnt)

# TODO :
# follow points -> draw lines between them : img = cv2.line(img,(0,0),(511,511),(255,0,0),5)

#     for cnt in contours:
#         approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
#         if len(approx)==5:
#             cv2.drawContours(frame,[approx],0,255,-1)
#         elif len(approx)==3:
#             cv2.drawContours(frame,[approx],0,(0,255,0),-1)
#         elif len(approx)==4:
#             cv2.drawContours(frame,[approx],0,(0,0,255),-1)
#         elif len(approx) == 9:
#             cv2.drawContours(frame,[approx],0,(255,255,0),-1)
#         elif len(approx) > 15:
#             cv2.drawContours(frame,[approx],0,(0,255,255),-1)

    # Display the resulting frame
    cv2.imshow('shapes',frame)
    if outputFile != False:
        out.write(frame)

    if k == ord('s'):
        cv2.imwrite("{}_{}.out.png".format(argv[1], frameNumber), frame)
        print "saved frame", frameNumber

#     if len(followers) > 0:
#         sleep(0.1)

refreshPath(0)

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()

if outputFile != False:
    out.release()

print "Total frames =", frameNumber
print "Max contours =", maxContours
print "Longest one =", biggestContour

print "in  :", nbIn
print "out :", nbOut