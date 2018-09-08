import sys, traceback, os, random, math, json

from Hacjpg import Hacjpg

def bt():
    try:   
        raise Exception("Manually raise an exception.")
    except Exception:
        traceback.print_stack(file=sys.stderr)
        sys.stderr.flush()
        
def msg(*argv):
    sys.stdout.write("".join(list(argv)) + "\n")
    sys.stdout.flush()

def errmsg(*argv):
    sys.stderr.write(" *** ERROR: ")
    sys.stderr.write("".join(list(argv)) + "\n")
    sys.stderr.flush()
    bt()
    
def vbsmsg(*argv):
    sys.stdout.write("...")
    sys.stdout.write("".join(list(argv)) + "\n")
    sys.stdout.flush()

class HacDriver(Hacjpg):
    """
    This is the main class to drive the car. See try2drive method.
    """
    
    def __init__(self, is_debug=False):
        self.hacjpg = Hacjpg()
        
        self.spec = {}
        
        # throttle spec
        self.spec['tho_max'] = 0.5
        self.spec['tho_min'] = 0.01
        
        # steering angle spec 
        self.spec['sta_max'] = 45
        self.spec['sta_min'] = -45
        
    def try2drive(self, img, dashboard):
        """
        (sta, tho)
        """ 
        out_sta, out_tho = (0.0, 0.02)
        
        self.hacjpg.show(img, "input", waitkey=1)
        
        return out_sta, out_tho
    
