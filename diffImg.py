import cv2
import numpy
from sys import argv, exit

if len(argv) != 4:
    print "usage", argv[0], "imgBg imgCurr [ - | imgOut ]"
    exit(1)

bg = cv2.imread(argv[1], cv2.IMREAD_COLOR)
curr = cv2.imread(argv[2], cv2.IMREAD_COLOR)

# fgbg = cv2.BackgroundSubtractorMOG()
# 
# fgmask = fgbg.apply(bg)
# cv2.imshow('fgmask', fgmask)
# k = cv2.waitKey(0)
# 
# fgmask = fgbg.apply(curr)
# cv2.imshow('fgmask', fgmask)
# k = cv2.waitKey(0)

result = cv2.absdiff(bg, curr)
if argv[3] == '-':
    cv2.imshow('diff',result)
    k = cv2.waitKey(0)

    blur = cv2.blur(result, (25,25))
    cv2.imshow('diff blured',result)

    ret,colorTh = cv2.threshold(blur, 50, 255, cv2.THRESH_BINARY)
    cv2.imshow('color threshold',colorTh)
    gray = cv2.cvtColor(colorTh, cv2.COLOR_BGR2GRAY)
    cv2.imshow('color threshold gray',gray)
    ret,result = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY)
    cv2.imshow('color threshold gray threshold',result)
    k = cv2.waitKey(0)

#     kSize = 15
#     kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kSize, kSize)) #np.ones((5,5),np.uint8)
#     erosion = cv2.erode(result, kernel, iterations = 1)
#     result = cv2.dilate(erosion, kernel, iterations = 1)
# 
#     cv2.imshow('image',result)
#     k = cv2.waitKey(0)

    contours,h = cv2.findContours(result, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    print "found", len(contours), "contours"
    for i,cnt in enumerate(contours):
        print cnt
        area = cv2.contourArea(cnt)
        #if area > 100:
        perim = cv2.arcLength(cnt, True)
        M = cv2.moments(cnt)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])
        
        cv2.drawContours(result, [cnt], 0, (0, 255, 0), 1)
        cv2.circle(result, (cx, cy), 5, (0,0,255), -1)

    cv2.imshow('image',result)
    k = cv2.waitKey(0)

else:
    cv2.imwrite(argv[3], result)
