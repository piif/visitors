import numpy as np
import cv2
from sys import argv

inputFile = argv[1]

cap = cv2.VideoCapture(inputFile)
fgbg = cv2.BackgroundSubtractorMOG()
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15)) #np.ones((5,5),np.uint8)

maxContours = 0
biggestContour = 0
frameNumber = 0

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
        
    fgmask = fgbg.apply(frame)

    erosion = cv2.erode(fgmask,kernel,iterations = 1)
    img = cv2.dilate(erosion,kernel,iterations = 1)
    cv2.imshow('img',img)

    contours,h = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > maxContours:
        maxContours = len(contours)

    for cnt in contours:
        if len(cnt) > biggestContour:
            biggestContour = len(cnt)

#    cv2.drawContours(frame, contours, -1, (255, 0, 0), 1)
    for i,cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > 1000:
            cv2.drawContours(frame, [cnt], 0, (0, 255, 0), 1)
            perim = cv2.arcLength(cnt, True)
            if k == ord('i'):
                print "frame", frameNumber, ": contour", i, "A=", area, "P=", perim
                cv2.imwrite("{}_{}_i.png".format(argv[1], frameNumber), frame)
#         approx = cv2.approxPolyDP(cnt, 0.05 * perim, True)
#         cv2.drawContours(frame, [approx], 0, (0, 255, 0), 1)

    if k == ord('m'):
        for cnt in contours:
            print cv2.moments(cnt)

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


# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()

print "Total frames =", frameNumber
print "Max contours =", maxContours
print "Longest one =", biggestContour