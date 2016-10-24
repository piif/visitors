
#python lineFilter.py -i samples/portique_4.mp4 --green 521 195 521 270 --red 554 192 554 272
# = simple case, no encounter nor glued people possible (but ...)

#python lineFilter.py -i samples/raw/WP_20160319_005.stab.avi --green 330 109) 361 472 --red 489 112 498 468
# = side view, vertical lines

#python lineFilter.py -i samples/porteA/porteA_raw1_0025.avi --green 80 540 680 545 --red 80 500 680 500
# = top view, horizontal lines

"""
- roll video from keyboard :
  - go 1 frame forward with right arrow
  - backward (limited to 10 frames) with left arrow
  - get frame number with 'i'
  - play/pause with 'p' or 's'
  - quit with 'q'
  
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

from VideoReader import VideoReaderProgram
from Gate import CountingGate, Line

import cv2, numpy, math

class lineFilter(VideoReaderProgram):

    # class instance for 2 counting gates
    gate = None
    # computation results
    greenRate = 0
    redRate = 0

    # any color of any pixel varying of more than this value is considered as covering background
    colorThreshold = 50 # TODO : add argument


    def parseArgs(self):
        VideoReaderProgram.parseArgs(self)
        self.gate = CountingGate(self.args.greenLine, self.args.redLine)


    def firstFrameCallback(self, caller, frame):
        self.gate.setBackground(frame.copy())
        self.gate.redraw(frame)
        caller.legendLine = 2


    def intersectPix(x, y):
        delta = max(abs(numpy.array(bg[y][x], dtype=numpy.int16)
                   - numpy.array(frame[y][x], dtype=numpy.int16)))
        print x, "x", y, ":", delta
    
    
    def infoCallback(self, caller, stepNumber, step):
        return "{0:05d} : {1:3.0f} {2:3.0f}".format(caller.frameNumber, self.greenRate, self.redRate)


    def inputFrameCallback(self, caller, stepNumber, step):
        """
        TODO
        * enumerer les points des 2 lignes dans 2 listes
        - diff entre 1ere frame et courante comme dans diffThreshold
        - parcourir chaque point des lignes : en deduire des listes de segments (paires d'index)
        - afficher les segments obtenus (en blanc) + marquer les "taches"
        - les historiser + comparer l'historique des 2 lignes
          comment reperer les croisements :
          - en mode horizontal (vue dessus) ? proximite des centres ?
          - en mode vertical (vue de cote) ? compter combien de taches il y a entre les lignes en
            partant du principe qu'il y en a 0 au depart ?
          a creuser sur des exemples ...
        """

        self.greenRate, self.redRate = self.gate.intersect(step['input'], self.colorThreshold)
        self.gate.redraw(step['output'])



if __name__ == '__main__':

    program = lineFilter()
    program.parser.add_argument('--red', nargs = 4, type = int,
                    dest = 'redLine', default = [ 0, 0, 0, 0 ],
                    help = "(x,y)->(x,y) for red line")
    program.parser.add_argument('--green', nargs = 4, type = int,
                    dest = 'greenLine', default = [ 0, 0, 0, 0 ],
                    help = "(x,y)->(x,y) for green line")

    program.parseArgs()
 
    program.redLine = program.args.redLine
    program.greenLine = program.args.greenLine

    # handle mouse to redraw red and green lines
    drawing = None
    def mouseHandler(event, x, y, flags, param):
        global drawing, gate
    
        if event == cv2.EVENT_MBUTTONUP:
            program.intersectPix(x, y)
        elif event == cv2.EVENT_LBUTTONDOWN:
            program.gate.green.setStart(x, y)
            drawing = 'g'
        elif event == cv2.EVENT_LBUTTONUP:
            program.gate.green.setEnd(x, y)
            drawing = None
            print program.gate.green
        elif event == cv2.EVENT_RBUTTONDOWN:
            program.gate.red.setStart(x, y)
            drawing = 'r'
        elif event == cv2.EVENT_RBUTTONUP:
            program.gate.red.setEnd(x, y)
            drawing = None
            print program.gate.red
        elif event == cv2.EVENT_MOUSEMOVE and drawing is not None:
            if drawing == 'g':
                program.gate.green.setEnd(x, y)
            else:
                program.gate.red.setEnd(x, y)
        else:
            return
        program.gate.redraw(step['output'])

    cv2.setMouseCallback("output", mouseHandler)

    program.run()
