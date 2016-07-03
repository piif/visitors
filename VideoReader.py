# TODO : add options displayInput and displayOutput

import cv2, numpy
from sys import argv, exit
from sys import argv, exit
import argparse
from History import History

class VideoCapture:
    # max len of buffer # TODO : add argument
    bufferMax = 25

    # step by step mode # TODO : add argument
    stepByStep = True

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
        s = c / 100
        c = c % 100
        m = s / 60
        s = s % 60
        h = m / 60
        m = m % 60
        return (h, m, s, c)

    def __init__(self,
                 _input,  # input capture
                 _maxBuffer = 25, # fifo max size
                 _firstFrameCallback = None, # callback for first read frame
                 _inputFrameCallback = None, # callback for next frames before changing anything
                 _infoCallback = None, # callback to get informations to display in legend
                 _detailsCallback = None, # callback to get detailled informations to display when 'i' pressed
                 _outputFrameCallback = None, # callback for next frames just before displaying it
                 _popCallback = None, # callback when a frame is popped from history
                 _stepByStep = True, # play/pause mode at startup
                 _skip = 0 # frames to skip at startup
    ):
        self.inputFile = _input
        self.infoCallback  = _infoCallback
        self.detailsCallback  = _detailsCallback
        self.inputFrameCallback = _inputFrameCallback
        self.outputFrameCallback= _outputFrameCallback
        self.popCallback = _popCallback
        self.stepByStep = _stepByStep

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
                          _removeCallback = self.popCallback)

        step = self.history.get()

        self.width = step['input'].shape[1]
        self.height = step['input'].shape[0]
        self.frameRate = self.cap.get(cv2.cv.CV_CAP_PROP_FPS)
        if self.frameRate == 0:
            self.frameRate = 25
        self.fcc = self.cap.get(cv2.cv.CV_CAP_PROP_FOURCC)
        if self.fcc == 0:
            self.fcc = cv2.cv.CV_FOURCC(*'XVID')

        cv2.imshow("raw", step['input'])

        frame = step['input'].copy()

        if _firstFrameCallback is not None:
            _firstFrameCallback(frame)

        step['output'] = frame

        legend = "input {3} {0}x{1}@{2}".format(self.width, self.height, self.frameRate, self.inputFile)
        cv2.putText(step['output'], legend, (5, 20), self.font, 0.5, (255,255,255))

        cv2.imshow("output", step['output'])

    def run(self):
        # read frames
        while(True):
            isNew = False

            if self.stepByStep:
                k = cv2.waitKey(0)
            else:
                k = cv2.waitKey(1)

            if k & 0xFF == ord('i'):
                print "Frame {0}".format(self.history.index())
                if self.detailsCallback is not None:
                    print "  ", self.detailsCallback(index, step)
                continue
            elif k & 0xFF == ord('q'):
                break
            elif k & 0xFF == ord('s') or k & 0xFF == ord('p'):
                self.stepByStep = not self.stepByStep
                continue

            # left key => go backward
            elif k == 1113937:
                step = self.history.backward()
                #TODO: plante si backward a fond puis play
                if step is None:
                    continue

            else:
                step, isNew = self.history.forward()

            cv2.imshow("raw", step['input'])

            if isNew:
                step['output'] = step['input'].copy()
                index = self.history.index()

                if self.inputFrameCallback is not None:
                    self.inputFrameCallback(index, step)

                legend = "{0:02}:{1:02}:{2:02}.{3:02}".format(*self.frameToTimestamp(index))
                if self.infoCallback is not None:
                    legend = legend + ": " + self.infoCallback(index, step)
                cv2.putText(step['output'], legend, (5, 20), self.font, 0.5, (255,255,255))

                if self.outputFrameCallback is not None:
                    self.outputFrameCallback(index, step)

            cv2.imshow("output", step['output'])

        # at end of video input => output last frames in history
        if self.popCallback is not None:
            print "popping queue", self.history.iter0, self.history.bufferPos, len(self.history.buffer)

            while self.history.pop() is not None:
                pass
        

if __name__ == '__main__':

    def firstFrameCallback(step):
        # TODO : job to do with first frame (stored in step['input'])
        pass

    def infoCallback(stepNumber, step):
        # TODO : job to do with first frame (stored in step['input'])
        return "TODO"

    def inputFrameCallback(stepNumber, step):
        # TODO : job to do with input frame (stored in step['input'])
        # step['output'] is a copy of step['input'] where to store final output
        pass

    def outputFrameCallback(stepNumber, step):
        # TODO : job to do on modified frame, with timestamp on it, just before displaying it
        # out.write(step['output'])
        pass

    def popCallback(stepNumber, step):
        # TODO : job to do with first frame (stored in step['input'])
        print "popped frame", stepNumber

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest = 'inputFile',
                        default = 0,
                        help = "input file path (default to camera)")
    parser.add_argument('-s', '--skip', type = int, dest = 'skip',
                        default = 0,
                        help = "number of frame to skip at start")
    args = parser.parse_args()

    capture = VideoCapture(
         _input = args.inputFile,
         _firstFrameCallback = firstFrameCallback,
         _inputFrameCallback = inputFrameCallback,
         _infoCallback = infoCallback,
         _popCallback = popCallback,
         _outputFrameCallback = outputFrameCallback,
         _skip = args.skip
    )

    # out = cv2.VideoWriter(
    #         "{}_stab".format(inputFile),
    #         cv2.cv.CV_FOURCC(*'XVID'), #cap.get(cv2.cv.CV_CAP_PROP_FOURCC),
    #         25, #cap.get(cv2.cv.CV_CAP_PROP_FPS),
    #         (capture.width, capture.height)
    # )

    capture.run()

    #out.release()
