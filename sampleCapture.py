# TODO :
# - movement detection => start in "play" mode. If movement, toggle in "step by step" mode
# - short cut 'r' to start recording => ask for out file name
#   /!\ in record mode, must save only "new" frames, but back/forward still available
#   => just write frames which are canceled from buffer, and 0..current when 'r' pressed again

import cv2, numpy
from sys import argv, exit
from sys import argv, exit
import argparse
from History import History

parser = argparse.ArgumentParser()

parser.add_argument('-i', '--input', dest = 'inputFile',
                    default = 0,
                    help = "input file path (default to camera)")
parser.add_argument('-s', '--skip', type = int, dest = 'skip',
                    default = 0,
                    help = "number of frame to skip at start")

args = parser.parse_args()

# max len of buffer # TODO : add argument
bufferMax = 25

# step by step mode # TODO : add argument
stepByStep = True

font = cv2.FONT_HERSHEY_SIMPLEX


def getNextFrame():
    ret, frame = cap.read()
    if not ret:
        return None
    return { "input": frame }

def lostFrameCallback(frameNumber, step):
    #  todo
    pass

def showInfo():
    print "Frame {0}".format(history.index())

# return (hours, minutes, seconds, hundredth) from frame number and frame rate 
def frameToTimestamp(frameNum, frameRate):
    c = frameNum * 100 / frameRate
    s = c / 100
    c = c % 100
    m = s / 60
    s = s % 60
    h = m / 60
    m = m % 60
    return (h, m, s, c)


cap = cv2.VideoCapture(args.inputFile)

# skip first frames if asked for
if args.skip != 0 :
    print "Skipping", args.skip, "frames ..."
    for i in range( 1 , args.skip ) :
        if not cap.grab():
            exit(1)

# read first frame, deduce size
ret, frame = cap.read()
if not ret:
    exit(1)

history = History(_next = getNextFrame, _first = { "input": frame },
                  _initialIndex = args.skip, _removeCallback = lostFrameCallback)

step = history.get()

width = step['input'].shape[1]
height = step['input'].shape[0]

# TODO : why 0 0 ??????
frameRate = cap.get(cv2.cv.CV_CAP_PROP_FPS)
if frameRate == 0:
    frameRate = 25
fcc = cap.get(cv2.cv.CV_CAP_PROP_FOURCC)
if fcc == 0:
    fcc = cv2.cv.CV_FOURCC(*'XVID')

cv2.imshow("raw", step['input'])

frame = step['input'].copy()

## TODO : here, insert your code about first frame

step['output'] = frame

legend = "input {3} {0}x{1}@{2}".format(width, height, frameRate, args.inputFile)
cv2.putText(step['output'], legend, (5, 20), font, 0.5, (255,255,255))

cv2.imshow("output", step['output'])

# out = cv2.VideoWriter(
#         "{}_stab".format(inputFile),
#         cv2.cv.CV_FOURCC(*'XVID'), #cap.get(cv2.cv.CV_CAP_PROP_FOURCC),
#         25, #cap.get(cv2.cv.CV_CAP_PROP_FPS),
#         (width, height)
# )

# read frames
while(True):
    isNew = False

    if stepByStep:
        k = cv2.waitKey(0)
    else:
        k = cv2.waitKey(1)

    if k & 0xFF == ord('i'):
        showInfo()
        continue
    elif k & 0xFF == ord('q'):
        break
    elif k & 0xFF == ord('s') or k & 0xFF == ord('p'):
        stepByStep = not stepByStep
        continue

    # left key => go backward
    elif k == 1113937:
        step = history.backward()
        #TODO: plante si backward a fond puis play
        if step is None:
            continue

    else:
        step, isNew = history.forward()

    cv2.imshow("raw", step['input'])

    if isNew:
        frame = step['input'].copy()

        ## TODO : here, insert your code about current frame

        step['output'] = frame

        legend = "{0:02}:{1:02}:{2:02}.{3:02}".format(*frameToTimestamp(history.index(), frameRate))
        cv2.putText(step['output'], legend, (5, 20), font, 0.5, (255,255,255))

    cv2.imshow("output", step['output'])

out.release()
