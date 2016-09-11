from VideoReader import VideoReaderProgram

import cv2, numpy, math

class extractSamplesDiff(VideoReaderProgram):
    sampleNumber = -1
    sampleFrameStart = -1
    sampleFrameEnd = -1
    sampling = 0

    # ratio of changing pixels to consider it's a movement
    moveThreshold = 0.05

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
                self.sampleFrameStart = caller.frameNumber - self.samplingHistory
                print "start sample at", self.sampleFrameStart
                if self.sampleFrameStart < 0: self.sampleFrameStart = 0
                # open out file
                outputFile = "{0}_out{1:04d}".format(self.args.inputFile, self.sampleNumber)
                print "open", outputFile, "for", caller.width, 'x', caller.height, '@', caller.frameRate
                self.out = cv2.VideoWriter(
                        outputFile,
                        cv2.cv.CV_FOURCC(*'XVID'),
                        caller.frameRate,
                        (caller.width, caller.height)
                )
            self.sampling = self.samplingTolerancy

        elif self.sampling > 0:
            self.sampling -= 1
            if self.sampling == 0:
                self.sampleFrameStart = -1
                self.sampleFrameEnd = caller.frameNumber + self.samplingHistory
                print "stop sample at", self.sampleFrameEnd

        self.prevFrame = step['input']

    def infoCallback(self, caller, stepNumber, step):
        return "{2:05d} : {0:2.2%} {1}".format(
            step['move'], (self.sampleNumber if self.sampling > 0 else "-"), caller.frameNumber)


    def popCallback(self, caller, stepNumber, step):
        if (self.sampleFrameStart >= 0 and self.sampleFrameStart <= stepNumber) \
                or (self.sampleFrameEnd > 0 and stepNumber <= self.sampleFrameEnd):
            self.out.write(step['output'])
            if self.sampleFrameEnd == stepNumber and self.sampleFrameStart < 0:
                self.sampleFrameEnd = -1
                self.out.release()
                self.out = None

    def endCallback(self, caller):
        if self.out is not None:
            self.out.release()

if __name__ == '__main__':
    program = extractSamplesDiff()
    program.parser.add_argument('-m', '--move-threshold', type = float, dest = 'moveThreshold',
                                default = 0.005,
                                help = "threshold (default to 0,5%)")
    program.parser.add_argument('-b', '--bg-threshold', type = int, dest = 'bgThreshold',
                                default = 50,
                                help = "threshold (default to 0,5%)")

    program.parseArgs()
 
    program.moveThreshold = program.args.moveThreshold
    program.bgThreshold = program.args.bgThreshold
    GRAY_MIN = numpy.array(3 * [ program.bgThreshold ], numpy.uint8)
    GRAY_MAX = numpy.array(3 * [ 255 ], numpy.uint8)

    program.run()
