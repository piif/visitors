"""
TODO :
- User must implement a class/hash/list/something and append them to this class
- Class stores a fixed size fifo of them
- User can go forward/backward
A callback can be called for removed item
A "main loop" allow to run forward/backward
"""

class History:
    buffer = [ ]
    # current position in buffer
    bufferPos = 0
    # absolute position of first buffer item
    iter0 = 0

    def __init__(self,
                 _next,  # callback to get a new item
                 _maxSize = 25, # fifo max size
                 _removeCallback = None, # callback for removed item
                 _first = None, # initialize fifo with this item
                 _initialIndex = 0 # force first item having this index
    ): 
        # TODO max must be > 1
        self.bufferMax = _maxSize
        self.nextCallback = _next
        self.removeCallback = _removeCallback
        self.iter0 = _initialIndex
        if _first is not None:
            self.buffer.append(_first)

    def forward(self):
        if self.bufferPos >= 0 and self.bufferPos < len(self.buffer) - 1:
            self.bufferPos += 1
            return self.buffer[self.bufferPos], False
        else:
            nextOne = self.nextCallback()
            if nextOne is None:
                return None, True
    
            self.buffer.append(nextOne)
            
            if len(self.buffer) > self.bufferMax:
                if self.removeCallback is not None:
                    self.removeCallback(self.iter0, self.buffer[0])
                del self.buffer[0]
                self.iter0 += 1
            else:
               self. bufferPos += 1

            return self.buffer[self.bufferPos], True

    def backward(self):
        if self.bufferPos > 0:
            self.bufferPos -= 1
            return self.buffer[self.bufferPos]
        return None

    # return current item
    def get(self):
        if len(self.buffer) > 0:
            return self.buffer[self.bufferPos]
        return None

    # return index of current item
    def index(self):
        return self.iter0 + self.bufferPos