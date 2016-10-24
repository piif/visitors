from collada import lineset

#python lineFilter.py -i samples/portique/portique_4.mp4 --green 521 195 521 270 --red 554 192 554 272 --lineThreshold 40
# = simple case, no encounter nor glued people possible (but ...)

#python lineFilter.py -i samples/raw/WP_20160319_005.stab.avi --green 330 109) 361 472 --red 489 112 498 468
# = side view, vertical lines

#python lineFilter.py -i samples/porteA/porteA_raw1_0025.avi --green 80 540 680 545 --red 80 500 680 500
#python lineFilter.py -i samples/porteA/porteA_raw1_0039.avi --green 80 540 680 540 --red 80 500 680 500
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
    # line computation results
    greenRate = 0
    redRate = 0

    # crosses counts
    ingoing = 0
    outgoing = 0

    # when green/red rate if over threshold, first/second char passes to G/R
    # third flag is i or o indicating ingoing/outgoing person
    # __ means "nothing"
    # G_ = someone begins to cut in "in" direction -> G_ , i
    # then, we must have GR, then _R, then __ back -> +1 in
    # any other combination means the person went back, or there was several persons crossing in opposite directions
    # _R = someone begins to cut in "out" direction -> _R, o
    # then, we must have GR, then G_, then __ back -> +1 out
    lineState = "__"
    dirState = "_"

    # try to summarize various possibilities in a matrix
    stateMachine = {
        # "line,dir,newState" -> (new dirState, counter to update) (0=none, -1 = out, +1 = in)
        "__,_,G_": ("i", 0), # start cross in
        "__,_,_R": ("o", 0), # start cross out
        "__,_,GR": ("?", 0), # start cross quickly => can't say in which direction
        
        "G_,i,__": ("_", 0), # someone went back just before the door
        "G_,i,GR": ("i", 0), # continue to cross "in"
        "G_,i,_R": ("i", 1), # a mouse crosses in ?
        "GR,i,G_": ("i", 0), # someone went back while thru the door
        "GR,i,_R": ("i", 1), # someone ending to cross in
        "GR,i,__": ("_", 1), # someone ending to cross in quickly
        "_R,i,__": ("_", 0), # someone ended to cross in (already counted)

        "_R,o,__": ("_", 0), # someone went back just before the door
        "_R,o,GR": ("o", 0), # continue to cross "out"
        "_R,o,G_": ("o",-1), # a mouse crosses out ?
        "GR,o,_R": ("o", 0), # someone went back while thru the door
        "GR,o,G_": ("o",-1), # someone ending to cross out
        "GR,o,__": ("_",-1), # someone ending to cross out quickly
        "G_,o,__": ("_", 0), # someone ended to cross out (already counted)

        # approximation : if someone crosses the 2 lines quick then go back, we count it as crossing
        "GR,?,G_": ("o",-1), # started cross quickly, but we detected he's going out
        "GR,?,_R": ("i", 1), # started cross quickly, but we detected he's going in
    }
    # any color of any pixel varying of more than this value is considered as covering background
    colorThreshold = 50 # TODO : add argument

    # if ratio of "covering" pixels in a line is more than this threshold, we consider
    # than someone is crossing it
    lineThreshold = 10 # TODO : add argument


    # handle mouse to redraw red and green lines
    drawing = None
    def mouseHandler(self, event, x, y, flags, param):
    
        if event == cv2.EVENT_MBUTTONUP:
            self.intersectPix(x, y)
        elif event == cv2.EVENT_LBUTTONDOWN:
            self.gate.green.setStart(x, y)
            self.drawing = 'g'
        elif event == cv2.EVENT_LBUTTONUP:
            self.gate.green.setEnd(x, y)
            self.drawing = None
            print self.gate.green
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.gate.red.setStart(x, y)
            self.drawing = 'r'
        elif event == cv2.EVENT_RBUTTONUP:
            self.gate.red.setEnd(x, y)
            self.drawing = None
            print self.gate.red
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing is not None:
            if self.drawing == 'g':
                self.gate.green.setEnd(x, y)
            else:
                self.gate.red.setEnd(x, y)
        else:
            return
        toDraw = self.gate.background.copy()
        self.gate.redraw(toDraw)
        cv2.imshow("output", toDraw)


    def initialize(self):
        self.gate = CountingGate(self.greenLine, self.redLine)


    def firstFrameCallback(self, caller, frame):
        self.gate.setBackground(frame.copy())
        self.gate.redraw(frame)
        caller.legendLine = 2
        cv2.setMouseCallback("output", self.mouseHandler)


    def intersectPix(x, y):
        delta = max(abs(numpy.array(bg[y][x], dtype=numpy.int16)
                   - numpy.array(frame[y][x], dtype=numpy.int16)))
        print x, "x", y, ":", delta


    def infoCallback(self, caller, stepNumber, step):
        return "{0:05d} : {1:3.0f} {2:3.0f} / i={3} o={4}".format(
            caller.frameNumber,
            self.greenRate, self.redRate,
            self.ingoing, self.outgoing)


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
        newState = (
            ("G" if self.greenRate > self.lineThreshold else "_") +
            ("R" if self.redRate > self.lineThreshold else "_") )

        if self.lineState != newState:
            testCase = self.lineState + "," + self.dirState + "," + newState
            if self.stateMachine.has_key(testCase):
                (self.dirState, action) = self.stateMachine[testCase]
                if action == 1:
                    self.ingoing += 1
                elif action == -1:
                    self.outgoing += 1
            else:
                print "Unknown state", testCase
            self.lineState = newState 
        self.gate.redraw(step['output'])



if __name__ == '__main__':

    program = lineFilter()
    program.parser.add_argument('--red', nargs = 4, type = int,
                    dest = 'redLine', default = [ 0, 0, 0, 0 ],
                    help = "(x,y)->(x,y) for red line")
    program.parser.add_argument('--green', nargs = 4, type = int,
                    dest = 'greenLine', default = [ 0, 0, 0, 0 ],
                    help = "(x,y)->(x,y) for green line")
    program.parser.add_argument('--lineThreshold', type = int,
                    dest = 'lineThreshold', default = 10,
                    help = "percentage of covered line to consider it 'crossed'")
    program.parser.add_argument('--colorThreshold', type = int,
                    dest = 'colorThreshold', default = 50,
                    help = "percentage of color change to consider pixl covered")

    program.parseArgs()
    program.redLine = program.args.redLine
    program.greenLine = program.args.greenLine
    program.lineThreshold = program.args.lineThreshold
    program.colorThreshold = program.args.colorThreshold
    program.initialize()

    program.run()

    print "END : in =", program.ingoing, "out =", program.outgoing
