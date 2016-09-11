from VideoReader import VideoReaderProgram

import cv2, numpy, math

class extractSamplesDiff(VideoReaderProgram):
    sampleNumber = -1
    sampling = False

    # ratio of changing pixels to consider it's a movement
    moveThreshold = 0.05

    # threshold kind and level for moving forms detection
    thresholdKind = cv2.THRESH_BINARY
    bgThreshold = 50

    # how many frame to wait before considering there's no more move
    samplingTolerancy = 10
    # how many previous frame to keep as reference frame in move detection
    samplingHistory = 10

    def firstFrameCallback(self, caller, frame):
        # initialize movement detector
        self.prevFrame = frame
        self.refFrame = frame

    def inputFrameCallback(self, caller, stepNumber, step):
        # detect movement, deduce to open new output file / append to it / close it
        frame = step['input']

        # how many pixels are different
        img = cv2.absdiff(self.prevFrame, frame)
        step['move'] = float(cv2.countNonZero(cv2.inRange(img, GRAY_MIN, GRAY_MAX))) / caller.nbPixel

        # deduce if it starts / continues / stops to move
        if step['move'] > self.moveThreshold:
            if self.sampling == 0:
                self.sampleNumber += 1
                if program.thresholdKind == 'MOG':
                    self.refFrame = cv2.BackgroundSubtractorMOG()
                    self.refFrame.apply(frame)
                else:
                    self.refFrame = (caller.history.get(-self.samplingHistory))['input']
            self.sampling = self.samplingTolerancy
        elif self.sampling > 0:
            self.sampling -= 1


        if self.sampling > 0:
            if program.thresholdKind == 'MOG':
                img = self.refFrame.apply(frame)
            else:
                # diff with first frame
                img = cv2.absdiff(self.refFrame, frame)
                #- blur it
                img = cv2.blur(img, (15,15))
                #- convert to gray (needed by contour detection)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                #- enhance each color
                ret,img = cv2.threshold(img, self.bgThreshold, 255, self.thresholdKind)

        step['output'] = img

        self.prevFrame = step['input']

    def infoCallback(self, caller, stepNumber, step):
        return "{0:2.2%} : {1}".format(
            step['move'], (self.sampleNumber if self.sampling > 0 else "-"))


    def popCallback(self, caller, stepNumber, step):
        pass

    def endCallback(self, caller):
        pass

if __name__ == '__main__':
    program = extractSamplesDiff()
    program.parser.add_argument('-m', '--move-threshold', type = float, dest = 'moveThreshold',
                                default = 0.005,
                                help = "threshold (default to 0,5%)")
    program.parser.add_argument('-b', '--bg-threshold', type = int, dest = 'bgThreshold',
                                default = 50,
                                help = "threshold (default to 50)")
    program.parser.add_argument('-k', '--threshold-kind', dest = 'thresholdKind',
                                default = None,
                                help = "threshold type to use (default to BINARY)")

    program.parseArgs()
 
    program.moveThreshold = program.args.moveThreshold
    program.bgThreshold = program.args.bgThreshold
    GRAY_MIN = numpy.array(3 * [ program.bgThreshold ], numpy.uint8)
    GRAY_MAX = numpy.array(3 * [ 255 ], numpy.uint8)

    if program.args.thresholdKind == 'MOG':
        program.thresholdKind = 'MOG'
    if program.args.thresholdKind == 'BINARY':
        program.thresholdKind = cv2.THRESH_BINARY
    if program.args.thresholdKind == 'MASK':
        program.thresholdKind = cv2.THRESH_MASK
    if program.args.thresholdKind == 'OTSU':
        program.thresholdKind = cv2.THRESH_OTSU
    if program.args.thresholdKind == 'TOZERO':
        program.thresholdKind = cv2.THRESH_TOZERO
    if program.args.thresholdKind == 'TRUNC':
        program.thresholdKind = cv2.THRESH_TRUNC

    program.run()
