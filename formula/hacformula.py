#!env python
#
# Auto-driving Bot
#
# Revision:      v1.2
# Released Date: Aug 20, 2018
#

import sys, traceback, os, random, math
import json

def bt():
    try:   
        raise Exception("Manually raise an exception.")
    except Exception:
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        
def msg(*argv):
    sys.stderr.write("...")
    sys.stderr.write("".join(list(argv)) + "\n")
    sys.stderr.flush()

def errmsg(*argv):
    sys.stderr.write(" *** ERROR: ")
    sys.stderr.write("".join(list(argv)) + "\n")
    sys.stderr.flush()
    bt()
    
def vbsmsg(*argv):
    sys.stderr.write("...")
    sys.stderr.write("".join(list(argv)) + "\n")
    sys.stderr.flush()
    
import cv2, base64, numpy
from PIL  import Image
from io   import BytesIO
class hacjpg():
    """
    Use this abstract jpg class to simplify image (jpeg) processing by using cv2 module.
    OpenCV tutorial: https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_tutorials.html
    
    Depend: cv2, base64
    """
    """
            width (x)
          /       \
        +---------+
        |         | \
        |.        |  height (y)
        |         | /
        +---------+
        
        The dot in the pic is: width, height = (1, 2)
    """
    def __init__(self):
        self._debug_mode = False
        pass
    
    def open_base64tojpg(self, base64img):
        """
        Input: Convert a base64 input into a opencv img object, e.g.
        
        Output: A list of RGB array: [255 255 255] [255 255 255] ...
        """
        jpg = base64.b64decode(base64img)
        nparray = numpy.asarray(Image.open(BytesIO(jpg)))
        
        return nparray
    
    def close(self, jpg):
        if jpg:
            del jpg
    
    def show(self, img, name = "image", scale = 1.0, waitkey = 10):
        """
        Display the img in a standalone window.
        """
        cv2.namedWindow(name, cv2.WINDOW_AUTOSIZE)
        cv2.imshow(name, img)
        
        if self._debug_mode == True:
            cv2.waitKey(0)
        else:
            cv2.waitKey(waitkey)
            
    def rgb2uint(self, tup):
        """
        Simplify rgb tuple into a unsigned number
        """
        r, g, b = tup
        return (r * 256 * 256) + (g * 256) + b
    
    def uint2rgb(self, uint):
        r, g, b = uint / (256 * 256), uint / (256), uint % 256
        return r, g, b
    
    def get_pixel(self, img, x, y):
        """
            width (x)
          /       \
        +---------+
        |         | \
        |.        |  height (y)
        |         | /
        +---------+
        """
        b, g, r = (img.item(y, x, 0), img.item(y, x, 1), img.item(y, x, 2))
        return r, g, b
        
    def print_geometry(self, img):
        """
        Print the pixel data of input img. Print a lot of xxx (trash?)...
        But, this function helps me to know how to read the pixel of img.
        """
        width, height = self.get_resolution(img)
        
        for x in range(0, width):
            for y in range(0, height):
                r, g, b = self.get_pixel(img, x, y)
                uint = self.rgb2uint((r, g, b))
                uint2hex = hex(uint)
                sys.stdout.write(str(uint2hex) + ",") 
            
            sys.stdout.write("\n")
            
    def _createdir(self, folder):
        if os.path.exists(folder) == False:
            os.mkdir(folder)
        
    def save2folder(self, folder, img, prefix = "img", suffix = ""):
        """
        Save input image into specified folder. Create the folder automatically.
        """
        from datetime import datetime
        filename = "%s-%s%s.jpg" % (prefix, datetime.now().strftime('%Y%m%d-%H%M%S-%f'), suffix)
        
        self._createdir(folder)
        res = cv2.imwrite(os.path.join(folder, filename), img, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
        if res == False:
            errmsg("Cannot write file " + os.path.join(folder, filename))
            
    def draw_line(self, img, st=(0, 0), ed=(320, 240), bgr=(0, 0, 255), thick=1):
        """
         width (x)
        /   \
        +----+
        |\   | \
        | \  |  height (y)
        |  \ | /
        +----+
        """
        width, height = self.get_resolution(img)
        
        x, y = st
        if x <= width and y <= height:
            pass
        else:
            errmsg("Invalid start point: " + str(x) + "," + str(y))
            
        x, y = ed
        if x <= width and y <= height:
            pass
        else:
            errmsg("Invalid end point: " + str(x) + "," + str(y))
            
        return cv2.line(img, st, ed, bgr, thick)
    
    def get_resolution(self, img):
        """
            width (x)
          /       \
        +---------+
        |         | \
        |         |  height (y)
        |         | /
        +---------+
        """

        # If image is grayscale, tuple returned contains only number of rows and columns.        
        height, width, channel = img.shape
        
        return width, height
    
    def bgr2rgb(self, img):
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    def rgb2bgr(self, img):
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
class Driver(hacjpg):
    """
    This is the main class to drive the car. See try2drive method.
    """
    
    def __init__(self):
        self.hacjpg = hacjpg()
        
    def try2drive(self, img, dashboard):
        #
        # output data
        # 
        out_steering_angle = 0.0
        out_throttle = 0.0
        
        #
        # local algorithm
        #
        
        self.hacjpg.show(img, "input", waitkey = 0)
        
        return out_steering_angle, out_throttle

class Car(hacjpg, Driver):
    """
    Output to control the client's car.
    { 
        'steering_angle': -45 ~ +45, 
        'throttle': -1 ~ 1 
    }
    """
    
    def __init__(self, emit_func):
        self._emit_func = emit_func
        self.hacjpg = hacjpg()
        
        self.driver = Driver()
        
        self._save_source_img = True

    def rx_telemetry(self, dashboard):
        self._dashboard = dashboard
        
        if dashboard:
            self.rx_telemetry_try2drive(dashboard)
        else:
            self.rx_telemetry_manual()

    def rx_telemetry_manual(self):
        """
        The client is manually driving. Send this data, but I don't know the reason.
        Possibly just an ack.
        
        Output: 'manual'
        """
        self._emit_func('manual', data={}, skip_sid=True)

    def rx_telemetry_try2drive(self, dashboard):
        """
        Recv client telemetry data and plz try to 'steer'.
        
        Input:
        {
            "steering_angle": 20.123,
            "throttle": 0.7,
            "brakes": 0.0,
            "speed": 1.3,
            "image": "VGhlIGNvbW11bmljYXRpb2",
            "lap": 1,
            "time": 95.355,
            "status": 0
        }
        
        Output: 'steer'
        """
        #
        # Display car's vanilla camera 'source'
        #        
        self.img = self.hacjpg.open_base64tojpg(dashboard['image'])
        del dashboard['image']
        
        self.hacjpg.bgr2rgb(self.img)
        self.hacjpg.show(self.img, name="source")
        
        if self._save_source_img == True:
            self.hacjpg.save2folder("log", self.img)
        
        steering_angle, throttle = self.driver.try2drive(self.img, dashboard)
        
        #
        # Send control command to car
        #
        output = { 
            'steering_angle': str(steering_angle), 
            'throttle': str(throttle),
            }
        self._emit_func('steer', output, skip_sid=True)
        
    def rx_connect(self, sid, environ):
        """
        Client's connected. Time to start the tour.
        """
        data = { 'steering_angle': 0, 'throttle': 1.0 }
        
        vbsmsg("sid: ", sid, "environ: ", format(environ))
        
        output = { 
            'steering_angle': str(data['steering_angle']), 
            'throttle': str(data['throttle']) 
            }
        self._emit_func('steer', output, skip_sid=True)

if __name__ == "__main__":
    import socketio
    import eventlet.wsgi
    from flask import Flask

    sio = socketio.Server()
    def my_emit_func(event_name, data, skip_sid=True):
        vbsmsg("emit: " + str(event_name) + ", data=" + str(json.dumps(data)) + ", skip_sid=" + str(skip_sid))
        sio.emit(event_name, data=data, skip_sid=skip_sid)

    car = Car(emit_func = my_emit_func)

    @sio.on('telemetry')
    def telemetry(sid, dashboard):
        if dashboard:
            vbsmsg("recv: " + str(sid) + format(json.dumps(dashboard)))
        
        car.rx_telemetry(dashboard)

    @sio.on('connect')
    def connect(sid, environ):
        car.rx_connect(sid, environ)

    app = socketio.Middleware(sio, Flask(__name__))
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)

# vim: set sw=4 ts=4 et :

