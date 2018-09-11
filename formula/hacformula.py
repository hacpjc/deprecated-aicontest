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
#     sys.stdout.write("...")
#     sys.stdout.write("".join(list(argv)) + "\n")
#     sys.stdout.flush()
    pass

from Hacjpg import Hacjpg
class Car(Hacjpg):
    """
    Output to control the client's car.
    { 
        'steering_angle': -45 ~ +45, 
        'throttle': -1 ~ 1 
    }
    """
    
    THROTTLE_MAX = 1.0
    THROTTLE_MIN = -1.0
    
    ANGLE_MAX = 45.0
    ANGLE_MIN = -45.0
    
    def __init__(self, emit_func, driver_object, is_debug=False, is_auto_reset=False, is_save_img=False):
        self._emit_func = emit_func
        self.hacjpg = Hacjpg()
        
        self.driver = driver_object
        self.is_debug = is_debug
        self.is_auto_reset = is_auto_reset
        self.is_save_img = is_save_img

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
        
        self.img = self.hacjpg.convert_bgr2rgb(self.img)
        if self.is_debug == True:
            self.hacjpg.show(self.img, name="source")
        
        if self.is_save_img == True:
            self.hacjpg.save2folder("log", self.img)
        
        steering_angle, throttle = self.driver.try2drive(self.img, dashboard)
        
        if throttle >= 995:
            msg("Driver bot sends request 995 to restart race.")
            self.tx_restart()
            return
        
        if throttle > self.THROTTLE_MAX or throttle < self.THROTTLE_MIN:
            errmsg("Invalid throttle value: " + str(throttle))
        
        if steering_angle > self.ANGLE_MAX or steering_angle < self.ANGLE_MIN:
            errmsg("Invalid steering angle: " + str(steering_angle))
        
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
        if self.is_auto_reset == True:
            msg("Auto reset...")
            self.tx_restart()
        
        data = { 'steering_angle': 0, 'throttle': 1.0 }
        
        output = { 
            'steering_angle': str(data['steering_angle']), 
            'throttle': str(data['throttle']) 
            }
        self._emit_func('steer', output, skip_sid=True)

        
    def tx_restart(self):
        """
        Send restart to reset the game.
        """
        self._emit_func('restart', data={}, skip_sid=True)

if __name__ == "__main__":
    import socketio
    import eventlet.wsgi
    from flask import Flask

    sio = socketio.Server()
    def my_emit_func(event_name, data, skip_sid=True):
        vbsmsg("emit: " + str(event_name) + ", data=" + str(json.dumps(data)) + ", skip_sid=" + str(skip_sid))
        sio.emit(event_name, data=data, skip_sid=skip_sid)

    """
    Select a driver to drive!
    """
    from HacDriverII import HacDriverII
    driver = HacDriverII(is_debug=True)
    car = Car(my_emit_func, driver, is_debug=True, is_auto_reset=True, is_save_img=False)

    @sio.on('telemetry')
    def telemetry(sid, dashboard):
        if dashboard:
            tmp = dict(dashboard)
            del tmp['image']
            vbsmsg("telemetry: " + format(json.dumps(tmp)))
        
        car.rx_telemetry(dashboard)

    @sio.on('connect')
    def connect(sid, environ):
        msg(" -> connect: " + str(sid) + format(environ))
        car.rx_connect(sid, environ)

    app = socketio.Middleware(sio, Flask(__name__))
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)


