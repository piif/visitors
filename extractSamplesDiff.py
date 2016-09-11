# Module to be called fromVideoSampler main
from VideoReader import moduleClass

import cv2, numpy, math

class extractSamplesDiff(moduleClass):
    sampleNumber = -1
    sampling = False

    bgThreshold = 50

    def firstFrameCallback(self, caller, frame):
        # initialize movement detector
        self.prevFrame = frame

    def inputFrameCallback(self, caller, stepNumber, step):
        # detect movement, deduce to open new output file / append to it / close it
        frame = step['output']

        # get "movement part" of image
        #- make diff with bg
        img = cv2.absdiff(self.prevFrame, frame)
        #- blur it
#         img = cv2.blur(img, (25,25))
        #- convert to gray (needed by contour detection)
#         img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        #- enhance each color
        ret,img = cv2.threshold(img, self.bgThreshold, 255, cv2.THRESH_BINARY)

        step['output'] = img
#         if (self.modeNm1):
#             self.prevFrame = step['input']

    def infoCallback(self, caller, stepNumber, step):
        return self.sampleNumber if self.sampling else "-"


    def popCallback(self, caller, stepNumber, step):
        pass

    def endCallback(self, caller):
        pass
