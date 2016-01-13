import numpy as np
import cv2
from sys import argv
from time import sleep

inputFile = argv[1]
cap = cv2.VideoCapture(inputFile)
ret, frame = cap.read()
# TODO : why 0 0 0 ??????
w = cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
h = cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
fps = cap.get(cv2.cv.CV_CAP_PROP_FPS)
print "video {}x{} @ {}".format(w, h, fps)

if len(argv) > 2:
    outputFile = argv[2]
    out = cv2.VideoWriter(
            outputFile,
            cap.get(cv2.cv.CV_CAP_PROP_FOURCC),
            cap.get(cv2.cv.CV_CAP_PROP_FPS),
            (int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))))
else:
    outputFile = False

fgbg = cv2.BackgroundSubtractorMOG()
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15)) #np.ones((5,5),np.uint8)

maxContours = 0
biggestContour = 0
frameNumber = 0

followers = []
# line = polyline coordinates showing this follower trace
# x, y : last seen position (=line[-1])
# f : last seen frame number
# x0, y0 : first seen coordinates (=line[0])

threshold = 50

def searchFollower(frameNumber, x, y):
    for f in followers:
        if abs(f['x'] - x) < threshold and abs(f['y'] - y) < threshold:
            f['f'] = frameNumber
            f['line'].append([x,y])
            f['x'] = x
            f['y'] = y
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
    
while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()
    frameNumber += 1

    if not ret:
        break

    k = cv2.waitKey(1) & 0xFF;
    if k == ord('q'):
        print "Break at frame", frameNumber
        break
    elif k == ord('s'):
        cv2.imwrite("{}_{}.png".format(argv[1], frameNumber), frame)
    
    # get "movement part" of image
    fgmask = fgbg.apply(frame)

    # (try to) remove artefacts
    erosion = cv2.erode(fgmask,kernel,iterations = 1)
    img = cv2.dilate(erosion,kernel,iterations = 1)
    cv2.imshow('img',img)

    # find contours Into it
    contours,h = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # statistics about number of contours + max number of segments in them
    if len(contours) > maxContours:
        maxContours = len(contours)
    for cnt in contours:
        if len(cnt) > biggestContour:
            biggestContour = len(cnt)

#    cv2.drawContours(frame, contours, -1, (255, 0, 0), 1)
    for i,cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > 1000:
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