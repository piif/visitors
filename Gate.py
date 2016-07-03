# a small toolbox to handle "gateway lines" in images

from numpy import array, int16
import cv2

class Line:
    x0 = 0
    y0 = 0
    x1 = 0
    y1 = 0
    name = "??"
    background = None

    maxLen = 0
    segments = []
    bgPixels = None

    # abstraction of a line into an image, where movement
    # have to be detected
    def __init__(self, _name, _coords):
        self.name = _name
        (self.x0, self.y0, self.x1, self.y1) = tuple(_coords)
        self.compute()


    def setBackground(self, frame):
        self.background = frame


    def setStart(self, x, y):
        (self.x0, self.y0) = (x, y)
        self.compute()


    def setEnd(self, x, y):
        (self.x1, self.y1) = (x, y)
        self.compute()


    def compute(self):
        self.maxLen = max ( abs(self.x0 - self.x1), abs(self.y0 - self.y1) )
        # let to be computed when asked for
        bgPixels = None


    def computeBgPixels(self):
        self.bgPixels = [ array(self.background[y][x], dtype=int16) \
                     for x, y in self.getPixels() ]


    def __len__(self):
        return self.maxLen


    def redraw(self, image, color):
        cv2.line(image, (self.x0, self.y0), (self.x1, self.y1), color, 2)
        for (s0, s1) in self.segments:
            cv2.line(image, s0, s1, (255, 255, 255), 2)

    def getPixels(self, nbIteration = -1):
        if (nbIteration == -1):
            nbIteration = self.maxLen
        if nbIteration == 0:
            raise StopIteration()

        dx = (self.x1 - self.x0)
        dy = (self.y1 - self.y0)
        for t in range(0, nbIteration):
            x = dx * t / nbIteration + self.x0
            y = dy * t / nbIteration + self.y0
            yield (x, y)


    # compute intersection between current frame and background, along pixel list
    def intersect(self, frame, colorThreshold):
        start = None
        end = None
        self.segments = []
        if self.bgPixels is None:
            self.computeBgPixels()
        over = 0
        for i, (x, y) in enumerate(self.getPixels()):
            fg = frame[y][x]
            delta = max(abs(self.bgPixels[i] - array(fg, dtype=int16)))
            #print x, "x", y, " : ", fg, "/", self.bgPixels[i], "->", delta
            if delta > colorThreshold:
                over += 1
                if start is None:
                    start = (x, y)
                else:
                    end = (x, y)
            elif start is not None:
                self.segments.append( (start, (x, y)) )
                start = None
    
        # close last segment if any
        if start is not None:
            self.segments.append((start, (self.x1, self.y1)))

        return over * 100.0 / (i+1)


    def __str__(self):
        return "%s line @ (%d,%d)->(%d,%d) -> maxLen %d" % (
            self.name, self.x0, self.y0, self.x1, self.y1, self.maxLen)


class CountingGate:
    # abstraction of 2 lines on which detected movements
    # are counted

    # red and green line objects
    green = None
    red = None
    # number of iterations to do in longest line 
    width = 0

    def __init__(self, _green, _red):
        self.green = Line("green", _green)
        self.red = Line("red", _red)
        self.width = max(len(self.red), len(self.green))


    def setRed(self, _red):
        self.red = -red
        self.width = max(len(self.red), len(self.green))


    def setGreen(self, _green):
        self.green = _green
        self.width = max(len(self.red), len(self.green))


    def setBackground(self, frame):
        self.green.setBackground(frame)
        self.red.setBackground(frame)

    def intersect(self, frame, colorThreshold):
        return self.green.intersect(frame, colorThreshold), self.red.intersect(frame, colorThreshold)

    # bounding box of gate
    def bbox(self, margin = 0):
        if self.red is None or self.green is None:
            return None
        x0 = min(self.red.x0, self.red.x1, self.green.x0, self.green.x1)
        x1 = max(self.red.x0, self.red.x1, self.green.x0, self.green.x1)
        y0 = min(self.red.y0, self.red.y1, self.green.y0, self.green.y1)
        y1 = max(self.red.y0, self.red.y1, self.green.y0, self.green.y1)
        return ((x0 - margin, y0 - margin), (x1 + margin, y1 + margin))


    def redraw(self, image):
        if self.green is not None:
            self.green.redraw(image, (0, 255, 0))
        if self.red is not None:
            self.red.redraw(image, (0, 0, 255))
