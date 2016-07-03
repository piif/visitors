# tests from http://www.pyimagesearch.com/2015/11/09/pedestrian-detection-opencv/

# import the necessary packages
from __future__ import print_function
from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import imutils
import cv2
from sys import argv, exit

inputFile = argv[1]
cap = cv2.VideoCapture(inputFile)

# initialize the HOG descriptor/person detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

frameNumber = 0
font = cv2.FONT_HERSHEY_SIMPLEX

# loop over the capture frames
while(True):
    ret, image = cap.read()
    if not ret:
        break
    frameNumber += 1

    # load the image and resize it to (1) reduce detection time
    # and (2) improve detection accuracy
    image = imutils.resize(image, width=min(400, image.shape[1]))
    orig = image.copy()
    cv2.putText(orig, "{0}".format(frameNumber), (5, 20), font, 0.3, (255,255,255))
    # detect people in the image
    (rects, weights) = hog.detectMultiScale(image, winStride=(4, 4),
        padding=(8, 8), scale=1.05)
 
    # draw the original bounding boxes
    for (x, y, w, h) in rects:
        cv2.rectangle(orig, (x, y), (x + w, y + h), (0, 0, 255), 2)
 
    # apply non-maxima suppression to the bounding boxes using a
    # fairly large overlap threshold to try to maintain overlapping
    # boxes that are still people
    rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
    pick = non_max_suppression(rects, probs=None, overlapThresh=0.65)
 
    # draw the final bounding boxes
    for (xA, yA, xB, yB) in pick:
        cv2.rectangle(image, (xA, yA), (xB, yB), (0, 255, 0), 2)
 
    # show the output images
    cv2.imshow("Before NMS", orig)
    cv2.imshow("After NMS", image)

    k = cv2.waitKey(1)
    if k & 0xFF == ord('q'):
        break
