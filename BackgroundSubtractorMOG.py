# first tries, with BackgroundSubtractorMOG method to extract background

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

scale = 0.5

# raw capture
cap = cv2.VideoCapture(inputFile)

# read first frame
ret, firstFrame = cap.read()

# TODO : why 0 0 0 ??????
w = firstFrame.shape[0]
#cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
h = firstFrame.shape[1]
#cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
fps = cap.get(cv2.cv.CV_CAP_PROP_FPS)
fcc = cap.get(cv2.cv.CV_CAP_PROP_FOURCC)
print "video {} {}x{} @ {}".format(fcc, w, h, fps)

firstFrame = cv2.resize(firstFrame, (0,0), fx=scale, fy=scale)

if len(argv) > 2:
    outputFile = argv[2]
    out = cv2.VideoWriter(
            outputFile,
            cv2.cv.CV_FOURCC(*'XVID'), ##cap.get(cv2.cv.CV_CAP_PROP_FOURCC),
            25, #cap.get(cv2.cv.CV_CAP_PROP_FPS),
            (640, 400) #(int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)))
    )
else:
    outputFile = False

fgbg = cv2.BackgroundSubtractorMOG()
fgmask = fgbg.apply(firstFrame)

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

# if distance between a point and last position in a path is lower,
# consider it as path element 
threshold = 50
# if distance is lower, don't add the point to the path, to avoid huge polylines
subThreshold = 5

# every "refresh" frames, clean pathes which didn't changed since previous one
refreshPathRate = 100 # 4 seconds

def searchFollower(frameNumber, x, y):
    global followers
    for f in followers:
        if abs(f['x'] - x) < threshold and abs(f['y'] - y) < threshold:
            f['f'] = frameNumber
            f['x'] = x
            f['y'] = y
            if abs(f['x'] - x) < subThreshold and abs(f['y'] - y) < subThreshold:
                f['line'].append([x,y])
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


def refreshPath():
    global followers, frameNumber, refreshPathRate

    ttl = frameNumber - refreshPathRate / 2
    print "refreshPath", ttl, "on", len(followers), "elements"
    followers = [ x for x in followers if not x['f'] < ttl ]
    print "=>", len(followers)


while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()
    frame = cv2.resize(frame, (0,0), fx=scale, fy=scale)

    frameNumber += 1

    if not ret:
        break

    if (frameNumber % refreshPathRate) == 0:
        refreshPath()

    k = cv2.waitKey(1) & 0xFF;
    if k == ord('q'):
        print "Break at frame", frameNumber
        break
    elif k == ord('s'):
        cv2.imwrite("{}_{}.png".format(argv[1], frameNumber), frame)
    
    # get "movement part" of image
    fgmask = fgbg.apply(frame)
    cv2.imshow('fgmask', fgmask)
    ###gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


    # (try to) remove artefacts
    erosion = cv2.erode(fgmask,kernel,iterations = 1)
    #cv2.imshow('erosion', erosion)
    ###erosion = cv2.erode(gray, kernel, iterations = 1)
    img = cv2.dilate(erosion, kernel, iterations = 1)

    cv2.imshow('img',img)

    # find contours Into it
    #contours,h = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours,h = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_L1)

    # statistics about number of contours + max number of segments in them
    if len(contours) > maxContours:
        maxContours = len(contours)
    for cnt in contours:
        if len(cnt) > biggestContour:
            biggestContour = len(cnt)

#    cv2.drawContours(frame, contours, -1, (255, 0, 0), 1)
    for i,cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > 100:
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

    if len(followers) > 0:
        sleep(0.1)

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()

if outputFile != False:
    out.release()

print "Total frames =", frameNumber
print "Max contours =", maxContours
print "Longest one =", biggestContour