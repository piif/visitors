import termios, fcntl, sys, os
from pango import AttrScale

# hacked from http://stackoverflow.com/questions/983354/how-do-i-make-python-to-wait-for-a-pressed-key
class single_keypress:
    def __init__(self):
        """Waits for a single keypress on stdin.

        Returns the character of the key that was pressed (zero on
        KeyboardInterrupt which can happen when a signal gets handled)
    
        """
        self.fd = sys.stdin.fileno()
        # save old state
        self.flags_save = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        self.attrs_save = termios.tcgetattr(self.fd)
    
        # make raw - the way to do this comes from the termios(3) man page.
        attrs = list(self.attrs_save) # copy the stored version to update

        # iflag
        attrs[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK 
                      | termios.ISTRIP  | termios.INLCR | termios.IGNCR
                      | termios.IXON )
        attrs[0] |= termios.ICRNL

        # oflag
#         attrs[1] &= ~(termios.OPOST | termios.OCRNL)
#         attrs[1] |= termios.ONLCR | termios.ONOCR

        # cflag
        attrs[2] &= ~(termios.CSIZE | termios. PARENB)
        attrs[2] |= termios.CS8
        # lflag
        attrs[3] &= ~(termios.ECHONL | termios.ECHO | termios.ICANON | termios.ISIG | termios.IEXTEN)

        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        
    def stop(self):
        # restore old state
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.attrs_save)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.flags_save)

    def read(self, blocking = False):
        if blocking:
            # turn off non-blocking
            fcntl.fcntl(self.fd, fcntl.F_SETFL, self.flags_save & ~os.O_NONBLOCK)
        else:
            fcntl.fcntl(self.fd, fcntl.F_SETFL, self.flags_save | os.O_NONBLOCK)

        try:
            ret = sys.stdin.read(1) # returns a single character
        except KeyboardInterrupt: 
            return '\0'
        except IOError: 
            return '\0'
        if ret == '\x1B':
            ret = sys.stdin.read(1)
            if ret == '[':
                ret = sys.stdin.read(1)
                if ret == 'A':
                    return 'UP'
                elif ret == 'B':
                    return 'DOWN'
                elif ret == 'C':
                    return 'RIGHT'
                elif ret == 'D':
                    return 'LEFT'
                else:
                    return 'ESC-[-' + ret
            else:
                return 'ESC-' + ret
        return ret

if __name__ == '__main__':
    k = single_keypress()
     
    print "Blocking"
    c = k.read(True)
    print c
     
    import time
     
    print "Non blocking"
    for i in range(1,10):
        print "."
        c = k.read()
        print c
        time.sleep(0.5)
     
    k.stop()