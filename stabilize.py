# specific code to try to stabilize video where
# (an exit panel can be used as fixed point)
# a red circle on door can be used as fixed point

import cv2, numpy
from sys import argv, exit

inputFile = argv[1]

cap = cv2.VideoCapture(inputFile)

def mouseHandler(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONUP:
        print x, "x", y, " = ", frame[y][x]
cv2.namedWindow("img")
cv2.setMouseCallback("img", mouseHandler)


def findRef(frame):
    ret,b = cv2.threshold(frame[:,:,0], 30, 80, cv2.THRESH_BINARY_INV)
    ret,g = cv2.threshold(frame[:,:,1], 30, 80, cv2.THRESH_BINARY_INV)
    ret,r = cv2.threshold(frame[:,:,2], 100, 80, cv2.THRESH_BINARY)
    ret,colorTh = cv2.threshold(b+g+r, 200, 255, cv2.THRESH_BINARY)

#     cv2.imshow("colorTh", colorTh)
    
    contours,h = cv2.findContours(colorTh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for i,cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > 300 and area < 500:
            approx = cv2.approxPolyDP(cnt, 0.1 * cv2.arcLength(cnt, True), True)
            cv2.drawContours(frame, [approx], 0, (255,0,0), -1)
            if len(approx)==4:
                M = cv2.moments(cnt)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                return (cx, cy)
    return None

# read first frame, deduce size
ret, frame = cap.read()
print frame.shape
frameCount = 1
width = frame.shape[1]
height = frame.shape[0]

out = cv2.VideoWriter(
        "{}_stab".format(inputFile),
        cv2.cv.CV_FOURCC(*'XVID'), #cap.get(cv2.cv.CV_CAP_PROP_FOURCC),
        25, #cap.get(cv2.cv.CV_CAP_PROP_FPS),
        (width, height)
)

# find first reference
res = None
findRef(frame)
cv2.imshow("img", frame)
while res is None:
#     if cv2.waitKey(0) & 0xFF == ord('q'):
#         exit(0)
    ret, frame = cap.read()
    res = findRef(frame)
    cv2.imshow("img", frame)
    frameCount += 1
(refX, refY) = res

print "reference found @", refX, "x", refY, "in frame n", frameCount
out.write(frame)

dx = refX
dy = refY

# read first frame
while(True):
    k = cv2.waitKey(1) & 0xFF;
    if k == ord('q'):
        break

    ret, frame = cap.read()
    if not ret:
        break

    res = findRef(frame)
    if res is not None:
        (dx, dy) = res

    M = numpy.float32([ [1, 0, refX - dx] , [0, 1, refY - dy] ])
    frame = cv2.warpAffine(frame, M, (width, height))
   
    cv2.imshow("img", frame)
    out.write(frame)

out.release()
