# Module to be called fromVideoSampler main

from VideoReader import moduleClass

class extractSamples(moduleClass):
    sampleNumber = -1
    sampling = False

    def firstFrameCallback(self, caller, frame):
        # TODO : don't call parent, initialize movement detector
        moduleClass.firstFrameCallback(self, caller, frame)

    def inputFrameCallback(self, caller, stepNumber, step):
        # detect movement, deduce to open new output file / append to it / close it 
        pass

    def infoCallback(self, caller, stepNumber, step):
        return self.sampleNumber if self.sampling else "-"


    def endCallback(self, caller):
        self.out.release()
