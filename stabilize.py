# specific code to try to stabilize video where an exit panel can be used
# as fixed point

import cv2
from sys import argv

inputFile = argv[1]
threshold = int(argv[2])

cap = cv2.VideoCapture(inputFile)

# read first frame
while(True):
    k = cv2.waitKey(1) & 0xFF;
    if k == ord('q'):
        break

    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    ret,colorTh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    cv2.imshow("colorTh", colorTh)
    
    contours,h = cv2.findContours(colorTh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for i,cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > 300:
            perim = cv2.arcLength(cnt, True)
            M = cv2.moments(cnt)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
    
            approx = cv2.approxPolyDP(cnt, 0.1 * cv2.arcLength(cnt, True), True)
            if len(approx)==4:
                cv2.drawContours(frame,[approx],0,(255,0,0),-1)
                # TODO : align img to center of this rectangle, if
                # position is coherent
            
            cv2.drawContours(frame, [cnt], 0, (0, 0, 0), 1)
            cv2.circle(frame, (cx, cy), 5, (0,0,255), -1)

    cv2.imshow("img", frame)