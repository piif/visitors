# Module to be called fromVideoSampler main
from VideoReader import moduleClass

import cv2, numpy, math

class extractSamplesMOG(moduleClass):
    sampleNumber = -1
    sampling = False

    bgThreshold = 50

    def firstFrameCallback(self, caller, frame):
        # initialize movement detector
        self.fgbg = cv2.BackgroundSubtractorMOG()
        fgmask = self.fgbg.apply(frame)

    def inputFrameCallback(self, caller, stepNumber, step):
        # detect movement, deduce to open new output file / append to it / close it
        step['output'] = self.fgbg.apply(step['output'])

    def infoCallback(self, caller, stepNumber, step):
        return self.sampleNumber if self.sampling else "-"


    def popCallback(self, caller, stepNumber, step):
        pass

    def endCallback(self, caller):
        pass
