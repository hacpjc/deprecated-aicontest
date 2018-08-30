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
    def __init__(self):
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
    
    def show(self, img, name = "image", scale = 1.0):
        cv2.namedWindow(name, cv2.WINDOW_AUTOSIZE)
        cv2.imshow(name, img)
        cv2.waitKey(1)

class Car(hacjpg):
    def __init__(self, emit_func):
        self._emit_func = emit_func
        self.hacjpg = hacjpg()

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
        
        vbsmsg('manual mode')
        
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
        data = { 'steering_angle': 0.0, 'throttle': 0 }
        
        #
        # Display car's vanilla camera 'source'
        #        
        self.img = self.hacjpg.open_base64tojpg(dashboard['image'])
        del dashboard['image']
        self.hacjpg.show(self.img, name="source")
        
        #
        # Send control command to car
        #
        output = { 
            'steering_angle': str(data['steering_angle']), 
            'throttle': str(data['throttle']),
            }
        self._emit_func('steer', output, skip_sid=True)
        
    def rx_connect(self, sid, environ):
        """
        Time to send commands to the client. Output:
        {
            'steering_angle': -45 ~ +45,
            'throttle': 0.0 ~ 1.0,
            'brakes': ?
        }
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

