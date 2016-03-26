TODO 
- revoir init de green et red si pas en argument
- dégager les 200 pemière frames de 14_3, ou trouver comment skip des frames sans y passer du temps
python lineFilter.py -i  samples/raw/WP_20160319_004.mp4 
python lineFilter.py -i samples/ldn1_14_3.avi --green 80 540 680 545 --red 80 500 680 500 -s 200


"""
- let user draw lines in video window :
  left click , drag , release => draw green line
  right click , drag , release => draw red line
- look at changes over these lines to detect movement from green to red, which
  is outgoing movement / from red to green which is ingoing movement
  
  Pixels cutting the lines will draw segments in it. A growing segment is a
  person which is crossing the line. A shrinking segment is the same person
  "leaving" the line.
  Approximately same segments must appear in other line. The order of appearance
  decides the direction of the person.
  
  The idea is to handle 2 cases :
  - horizontal kind, for camera on top of gate :
    2 segments cutting the line are 2 persons. If they merge, consider it's
    because people are closed to each other
  - vertical kind, for camera on side of gate :
    2 segments must be considered as 2 part of same people (leg and body for example)
    if they merge (and they should), it's still the same person.

"""

# EXAMPLE :
# lineFilter.py -i samples/ldn1_14_3.avi --green 80 540 680 540 --red 80 500 680 500

import cv2, numpy
from sys import argv, exit
import argparse
from symbol import argument

parser = argparse.ArgumentParser()
parser.add_argument('--red', nargs = 4, type = int,
                    dest = 'redLine', default = (0, 0, 0, 0),
                    help = "(x,y)->(x,y) for red line")
parser.add_argument('--green', nargs = 4, type = int,
                    dest = 'greenLine', default = (0, 0, 0, 0),
                    help = "(x,y)->(x,y) for green line")
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
step = True

# any color of any pixel varying of more than this value is considered
# has covering background
colorThreshold = 50 # TODO : add argument

cap = cv2.VideoCapture(args.inputFile)

def redraw():
    frame = buffer[bufferPos].copy()
    cv2.line(frame, tuple(greenLine[0:2]), tuple(greenLine[2:4]), (0, 255, 0), 2)
    cv2.line(frame, tuple(redLine[0:2]), tuple(redLine[2:4]), (0, 0, 255), 2)
    for (s0, s1) in greenSegments:
        cv2.line(frame, s0, s1, (255, 255, 255), 2)
    for (s0, s1) in redSegments:
        cv2.line(frame, s0, s1, (255, 255, 255), 2)

    cv2.imshow("video", frame)

cv2.namedWindow("video")

# read first frame
ret, frame = cap.read()
if not ret:
    exit(1)
buffer = [ frame ]
bufferPos = 0
bg = frame.copy()

# prepare red and green pixels
def prepareLine(bg, x0, y0, x1, y1):
    result = []
    # if x delta > y delta, enumerate delta x pixels else y ones
    pix=lambda x,y : {
        'x': x, 'y': y, 'bg': numpy.array(bg[y][x], dtype=numpy.int16)
    }
    if x0 == x1:
        if y0 == y1:
            return None
        for y in range(y0 , y1):
            result.append(pix(x0, y))
    elif y0 == y1:
        for x in range(x0, x1):
            result.append(pix(x, y0))
    elif abs(x1 - x0) > abs(y1 - y0):
        a = float(y1 - y0) / float(x1 - x0)
        b = y0 - a * x0
        #print "line y = ", a, "x +", b, " for x in", x0, "..", x1
        for x in range(x0, x1):
            y = int(a * x + b)
            result.append(pix(x, y))
    else:
        a = float(x1 - x0) / float(y1 - y0)
        b = x0 - a * y0
        #print "line x = ", a, "y +", b, " for y in", y0, "..", y1
        for y in range(y0 , y1):
            x = int(a * y + b)
            result.append(pix(x, y))

    print "prepareLine ->", result[0:3]
    return result


greenLine = args.greenLine
greenPixels = prepareLine(bg, *greenLine)
greenSegments = []

redLine = args.redLine
redPixels = prepareLine(bg, *redLine)
redSegments = []

redraw()

# skip start ones if asked for
if args.skip != 0 :
    print "Skipping", args.skip, "frames ..."
    for i in range( 1 , args.skip ) :
        if not cap.grab():
            exit(1)

frameNumber = args.skip


# handle mouse to redraw red and green lines
drawing = None
def mouseHandler(event, x, y, flags, param):
    global drawing, greenLine, greenPixels, redLine, redPixels

    if event == cv2.EVENT_MBUTTONUP:
        intersectPix(x, y)
    elif event == cv2.EVENT_LBUTTONDOWN:
        greenLine[0:2] = (x, y)
        drawing = 'g'
    elif event == cv2.EVENT_LBUTTONUP:
        greenLine[2:4] = (x, y)
        greenPixels = prepareLine(bg, *greenLine)
        drawing = None
        print "Green line @ (%d,%d)->(%d,%d)" % tuple(greenLine)
    elif event == cv2.EVENT_RBUTTONDOWN:
        redLine[0:2] = (x, y)
        drawing = 'r'
    elif event == cv2.EVENT_RBUTTONUP:
        redLine[2:4] = (x, y)
        redPixels = prepareLine(bg, *redLine)
        drawing = None
        print "Red line @ (%d,%d)->(%d,%d)" % tuple(redLine)
    elif event == cv2.EVENT_MOUSEMOVE and drawing is not None:
        if drawing == 'g':
            greenLine[2:4] = (x, y)
        else:
            redLine[2:4] = (x, y)
    else:
        return
    redraw()


def intersectPix(x, y):
    delta = max(abs(numpy.array(bg[y][x], dtype=numpy.int16)
               - numpy.array(frame[y][x], dtype=numpy.int16)))
    print x, "x", y, ":", delta

# compute intersection current frame and background, along pixel list
def intersect(pixels, frame):
    start = None
    end = None
    result = []
    for p in pixels:
        fg = frame[p['y']][p['x']]
        delta = max(abs(p['bg'] - numpy.array(fg, dtype=numpy.int16)))
        #print p['x'], "x", p['y'], " : ", fg, "/", p['bg'], "->", delta
        if delta > colorThreshold:
            if start is None:
                start = (p['x'],p['y'])
            else:
                end = (p['x'],p['y'])
        elif start is not None:
            result.append((start, (p['x'],p['y'])))
            start = None

    # close last segment if any
    if start is not None:
        result.append((start, (pixels[-1]['x'],pixels[-1]['y'])))
    return result


def showInfo():
    print "Frame number", frameNumber


cv2.setMouseCallback("video", mouseHandler)

while(True):
    if step:
        k = cv2.waitKey(0)
    else:
        k = cv2.waitKey(1)

    if k & 0xFF == ord('i'):
        showInfo()
    elif k & 0xFF == ord('q'):
        break
    elif k & 0xFF == ord('s') or k & 0xFF == ord('p'):
        step = not step

    # left key => go backward
    elif k == 1113937 and bufferPos > 0:
        bufferPos = bufferPos - 1
        frameNumber = frameNumber - 1
        
    else:
        if bufferPos >= 0 and bufferPos < len(buffer) - 1:
            bufferPos = bufferPos + 1
        else:
            ret, frame = cap.read()
            if not ret:
                break
    
            buffer.append(frame)
            
            if len(buffer) > bufferMax:
                del buffer[0]
            else:
                bufferPos = bufferPos + 1

        frameNumber = frameNumber + 1

    """
    TODO
    * enumerer les points des 2 lignes dans 2 listes
    - diff entre 1ere frame et courante comme dans diffThreshold
    - parcourir chaque point des lignes : en deduire des listes de segments (paires d'index)
    - afficher les segments obtenus (en blanc) + marquer les "taches"
    - les historiser + comparer l'historique des 2 lignes
      comment reperer les croisements en mode horiz ? proximite des centres ?
      en mode vert ? compter combien de taches il y a entre les lignes en
      partant du principe qu'il y en a 0 au depart ?
      a creuser sur des exemples ...
    """

    greenSegments = intersect(greenPixels, buffer[bufferPos])
    redSegments = intersect(redPixels, buffer[bufferPos])

    # Display the resulting frame
    redraw()


# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
