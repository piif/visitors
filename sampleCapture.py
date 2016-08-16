# TODO :
# - movement detection => start in "play" mode. If movement, toggle in "step by step" mode
# - short cut 'r' to start recording => ask for out file name
#   /!\ in record mode, must save only "new" frames, but back/forward still available
#   => just write frames which are canceled from buffer, and 0..current when 'r' pressed again

import cv2, numpy
from sys import argv, exit
import argparse
from VideoReader import VideoReader

def firstFrameCallback(caller, step):
    global out, args

    out = cv2.VideoWriter(
            args.outputFile,
            cv2.cv.CV_FOURCC(*'XVID'),
            args.framerate,
            (caller.width, caller.height)
    )


def infoCallback(caller, stepNumber, step):
    # TODO : job to do with first frame (stored in step['input'])
    return "TODO"


def popCallback(caller, stepNumber, step):
    global out
    out.write(step['output'])


parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', dest = 'inputFile',
                    default = None,
                    help = "input file path (default to None)")
parser.add_argument('-c', '--camera', type = int, dest = 'inputCam',
                    default = 0,
                    help = "input camera number (default to 0)")
parser.add_argument('-o', '--output', dest = 'outputFile',
                    default = None,
                    help = "output file path (default to input + '_out')")
parser.add_argument('-s', '--skip', type = int, dest = 'skip',
                    default = 0,
                    help = "number of frame to skip at start")
parser.add_argument('-f', '--framerate', type = int, dest = 'framerate',
                    default = None,
                    help = "force input and output framerate")
parser.add_argument('-I', '--hideinput', dest = 'showinput',
                    default = True, action='store_false',
                    help = "don't display input window")
parser.add_argument('-O', '--hideoutput', dest = 'showoutput',
                    default = True, action='store_false',
                    help = "don't display output window")
args = parser.parse_args()

if args.inputFile is None:
    args.inputFile = args.inputCam

if args.outputFile is None:
    args.outputFile = "{}_out".format(args.inputFile)

capture = VideoReader(
     _input = args.inputFile,
     _firstFrameCallback = firstFrameCallback,
     _infoCallback = infoCallback,
     _popCallback = popCallback,
     _frameRate = args.framerate,
     _showInput = args.showinput,
     _showOutput = args.showoutput,
     _skip = args.skip,
     _stepByStep = False
)

capture.run()

out.release()
