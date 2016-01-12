import numpy as np
import cv2
from sys import argv

inputFile = argv[1]

cap = cv2.VideoCapture(inputFile)
fgbg = cv2.BackgroundSubtractorMOG()
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)) #np.ones((5,5),np.uint8)

while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow('frame',gray)

    # Our operations on the frame come here
    fgmask = fgbg.apply(gray)
#     cv2.imshow('frame',fgmask)

    erosion = cv2.erode(fgmask,kernel,iterations = 1)
#     cv2.imshow('erosion',erosion)
    dilation = cv2.dilate(erosion,kernel,iterations = 1)
    cv2.imshow('dilation',dilation)

    # Display the resulting frame
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
