import cv2, numpy, math
from sys import argv, exit
from sys import argv, exit
import argparse
from History import History
from time import time

def translateKey(k):
    if k == -1:
        return None
    k = k & 0xffff
    if k == 0xff51:
        return 'LEFT'
    if k == 0xff53:
        return 'RIGHT'
    if k == 0xff52:
        return 'UP'
    if k == 0xff54:
        return 'DOWN'
    return chr(k & 255)

class VideoReader:
    # max len of buffer # TODO : add argument
    bufferMax = 25

    # step by step mode # TODO : add argument
    stepByStep = True

    # where to insert legend in output image (to be overloaded by sub classes)
    legendLine = 1

    font = cv2.FONT_HERSHEY_SIMPLEX


    def getNextFrame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return { "input": frame }


    def showInfo(self):
        print "Frame {0}".format(self.history.index())


    # return (hours, minutes, seconds, hundredth) from frame number and frame rate 
    def frameToTimestamp(self, frameNum):
        c = frameNum * 100 / self.frameRate
        return self.toTimestamp(c)


     # return (hours, minutes, seconds, hundredth) from start time and "now" time 
    def getTimestamp(self, start, now):
        c = int((now - start)*100)
        return self.toTimestamp(c)

    def toTimestamp(self, c):
        s = int(math.floor(c / 100))
        c = c % 100
        m = int(math.floor(s / 60))
        s = s % 60
        h = int(math.floor(m / 60))
        m = m % 60
        return (h, m, s, c)


    def __init__(self,
                 _input,  # input capture
                 _maxBuffer = 25, # fifo max size
                 _firstFrameCallback = None, # callback for first read frame
                 _inputFrameCallback = None, # callback for next frames before changing anything
                 _outputFrameCallback = None, # callback for next frames just before displaying it
                 _infoCallback = None, # callback to get informations to display in legend
                 _detailsCallback = None, # callback to get detailled informations to display when 'i' pressed
                 _popCallback = None, # callback when a frame is popped from history
                 _stepByStep = True, # play/pause mode at startup
                 _showInput = True, # show input in a window
                 _showOutput = True, # show output in a window
                 _skip = 0, # frames to skip at startup
                 _frameRate = None # give framerate
    ):
        self.inputFile = _input
        self.bufferMax = _maxBuffer

        self.inputFrameCallback = _inputFrameCallback
        self.outputFrameCallback= _outputFrameCallback
        self.infoCallback  = _infoCallback
        self.detailsCallback  = _detailsCallback
        self.popCallback = _popCallback

        self.stepByStep = _stepByStep

        self.showInput = _showInput
        if (self.showInput):
            cv2.namedWindow("raw")
        self.showOutput = _showOutput
        if (self.showOutput):
            cv2.namedWindow("output")

        self.cap = cv2.VideoCapture(self.inputFile)

        # skip first frames if asked for
        if _skip != 0 :
            print "Skipping", _skip, "frames ..."
            for i in range( 1 , _skip ) :
                if not self.cap.grab():
                    exit(1)

        # read first frame, deduce size
        ret, frame = self.cap.read()
        if not ret:
            exit(1)

        self.history = History(_next = self.getNextFrame, _first = { "input": frame },
                          _maxSize = _maxBuffer, _initialIndex = _skip,
                          _removeCallback = self.innerPopCallback)

        step = self.history.get()

        self.width = step['input'].shape[1]
        self.height = step['input'].shape[0]
        self.nbPixel = self.width * self.height


        if type(self.inputFile) is int:
            self.frameRate = None
            self.start = time()
            if _frameRate is None:
                raise Exception("capture from cam must specify framerate")

            elif _frameRate == 'auto':
                # read some frame to evaluate framerate
                for f in range(1,50):
                    ret, frame = self.cap.read()
                    if not ret:
                        print "End of capture during framerate calculation ..."
                        return None
                self.frameRate = 50 / (time() - self.start)

            else:
                self.frameRate = _frameRate
                print "force cam to frame rate", _frameRate
                if not self.cap.set(cv2.cv.CV_CAP_PROP_FPS, _frameRate):
                    print "Failed to force framerate"
                    # TODO : look a v4l compilation options to enable fps set ?
#             self.cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 320)
#             self.cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 200)

        else:
            self.frameRate = self.cap.get(cv2.cv.CV_CAP_PROP_FPS)
            if self.frameRate <= 0:
                if _frameRate is None:
                    print "Can't get frame rate ({0}), defaults to 25".format(self.frameRate)
                    self.frameRate = 25
                else:
                    self.frameRate = _frameRate

        self.fcc = self.cap.get(cv2.cv.CV_CAP_PROP_FOURCC)
        if self.fcc <= 0:
            print "Can't get fcc, defaults to XVID"
            self.fcc = cv2.cv.CV_FOURCC(*'XVID')

        if self.showInput:
            cv2.imshow("raw", step['input'])

        frame = step['input'].copy()

        if _firstFrameCallback is not None:
            _firstFrameCallback(self, frame)

        step['output'] = frame

        legend = "input '{3}' {0}x{1}@{2}".format(self.width, self.height, self.frameRate, self.inputFile)
        print legend
        cv2.putText(step['output'], legend, (5, self.legendLine*20), self.font, 0.5, (255,255,255))

        if self.showOutput:
            cv2.imshow("output", step['output'])


    def run(self):
        try:
            if not self.showOutput and not self.showInput:
                import keys
                self.keys = keys.single_keypress()
    
            # read frames
            while(True):
                isNew = False
    
                if self.showOutput or self.showInput:
                    # force redraw + handle keys
                    if self.stepByStep:
                        kc = translateKey(cv2.waitKey(0))
                    else:
                        kc = translateKey(cv2.waitKey(1))
                else:
                    # no window -> use stdin
                    if self.stepByStep:
                        kc = self.keys.read(True)
                    else:
                        kc = self.keys.read()
    
                if kc == 'i':
                    print "Frame {0}".format(self.history.index())
                    if self.detailsCallback is not None:
                        print "  ", self.detailsCallback(self, index, step)
                    continue

                elif kc == 'q':
                    break

                elif kc == 's' or kc == 'p':
                    self.stepByStep = not self.stepByStep
                    continue
    
                # left key => go backward
                elif kc == 'LEFT':
                    step = self.history.backward()
                    if step is None:
                        continue
    
                else:
                    step, isNew = self.history.forward()
    
                if self.showInput:
                    cv2.imshow("raw", step['input'])
    
                if isNew:
                    step['output'] = step['input'].copy()
                    self.frameNumber = self.history.index()
    
                    if self.inputFrameCallback is not None:
                        self.inputFrameCallback(self, self.frameNumber, step)
    
                    if type(self.inputFile) is int:
                        legend = "{0:02}:{1:02}:{2:02}.{3:02}".format(*self.getTimestamp(self.start, time()))
                    else:
                        legend = "{0:02}:{1:02}:{2:02}.{3:02}".format(*self.frameToTimestamp(self.frameNumber))
                    if self.infoCallback is not None:
                        legend = legend + ": " + self.infoCallback(self, self.frameNumber, step)
                    cv2.putText(step['output'], legend, (5, self.legendLine*20), self.font, 0.5, (255,255,255))
                    print self.legendLine
                    if self.outputFrameCallback is not None:
                        self.outputFrameCallback(self, self.frameNumber, step)
    
                if self.showOutput:
                    cv2.imshow("output", step['output'])

   
            # We're at end of video input => force output of last frames in history
            if len(self.history.buffer) != 0 and self.popCallback is not None:
                print "popping queue {1} frames from {0}".format(self.history.iter0, len(self.history.buffer))
    
                while self.history.pop() is not None:
                    # pop() will call its callback -> nothing to do in loop
                    pass

        finally:
            if not self.showOutput and not self.showInput:
                self.keys.stop()

    def innerPopCallback(self, stepNumber, step):
        if self.popCallback is not None:
            self.popCallback(self, stepNumber, step)



# default class defining user callbacks
class VideoReaderProgram:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('-i', '--input', dest = 'inputFile',
                            default = None,
                            help = "input file path (default to None)")
        self.parser.add_argument('-c', '--camera', type = int, dest = 'inputCam',
                            default = 0,
                            help = "input camera number (default to 0)")
        self.parser.add_argument('-o', '--output', dest = 'outputFile',
                            default = None,
                            help = "output file path (default to input + '_out')")
        self.parser.add_argument('-s', '--skip', type = int, dest = 'skip',
                            default = 0,
                            help = "number of frame to skip at start")
        self.parser.add_argument('-f', '--framerate', type = float, dest = 'framerate',
                            default = None,
                            help = "force input and output framerate")
        self.parser.add_argument('-a', '--autorate', dest = 'autorate',
                            default = False, action='store_true',
                            help = "compute framerate from input (for cam only)")
        self.parser.add_argument('-I', '--hideinput', dest = 'showinput',
                            default = True, action='store_false',
                            help = "don't display input window")
        self.parser.add_argument('-O', '--hideoutput', dest = 'showoutput',
                            default = True, action='store_false',
                            help = "don't display output window")
        self.parser.add_argument('-p', '--paused', dest = 'paused',
                            default = False, action='store_true',
                            help = "start in step by step mode")


    def parseArgs(self):
        self.args = self.parser.parse_args()
    
        if self.args.inputFile is None:
            self.args.inputFile = args.inputCam
    
        if self.args.outputFile is None:
            self.args.outputFile = "{}_out".format(self.args.inputFile)
    
        if self.args.autorate:
            self.args.framerate = 'auto'

        self.outputFile = self.args.outputFile


    def run(self):
        print "self is", self
        capture = VideoReader(
             _input = self.args.inputFile,
             _firstFrameCallback = self.firstFrameCallback,
             _inputFrameCallback = self.inputFrameCallback,
             _outputFrameCallback = self.outputFrameCallback,
             _infoCallback = self.infoCallback,
             _detailsCallback = self.detailsCallback,
             _popCallback = self.popCallback,
             _showInput = self.args.showinput,
             _showOutput = self.args.showoutput,
             _skip = self.args.skip,
             _frameRate = self.args.framerate,
             _stepByStep = self.args.paused
        )
    
        capture.run()

    def firstFrameCallback(self, caller, frame):
        print "open", self.outputFile, "for", caller.width, 'x', caller.height, '@', caller.frameRate
        self.out = cv2.VideoWriter(
                self.outputFile,
                cv2.cv.CV_FOURCC(*'XVID'),
                caller.frameRate,
                (caller.width, caller.height)
        )

    def inputFrameCallback(self, caller, stepNumber, step):
        # TODO
        pass

    def outputFrameCallback(self, caller, stepNumber, step):
        # TODO
        pass

    def infoCallback(self, caller, stepNumber, step):
        # TODO : job to do with first frame (stored in step['input'])
        return "TODO"

    def detailsCallback(self, caller, stepNumber, step):
        # TODO
        return None

    def popCallback(self, caller, stepNumber, step):
        try:
            self.out.write(step['output'])
        except AttributeError:
            pass

    def endCallback(self, caller):
        self.out.release()


if __name__ == '__main__':
    program = VideoReaderProgram()

    # user programs can't add argument parsing here

    program.parseArgs()

    # user programs can't add initialization stuffs here
    # or override run method to surround code on it
    program.run()
    # user programs can't add finalization stuffs here
