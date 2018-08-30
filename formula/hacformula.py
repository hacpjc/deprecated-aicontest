#!env python
#
# Auto-driving Bot
#
# Revision:      v1.2
# Released Date: Aug 20, 2018
#

import random
import shutil
import argparse
from datetime import datetime

from time import time
from PIL  import Image
from io   import BytesIO

import os
import cv2
import math
import numpy as np
import base64
import logging

import json

# base64.b64decode(dashboard["image"]))


class IP(object):
    def __init__(self):
        pass
    

class Car(object):
    MAX_STEERING_ANGLE = 40.0

    def __init__(self, emit_func):
        self._emit_func = emit_func

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
        
        print('manual mode')
        
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
        
        
        output = { 
            'steering_angle': str(data['steering_angle']), 
            'throttle': str(data['throttle']) 
            }
        self._emit_func('steer', output, skip_sid=True)
        
    def rx_connect(self, sid, environ):
        """
        Time to send commands to the client. Output:
        {
            'steering_angle', 
        }
        """
        data = { 'steering_angle': 0, 'throttle': 1.0 }
        
        print("sid: ", sid, "environ: ", format(environ))
        
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
        print (" -> emit: " + str(event_name) + ", data=" + str(json.dumps(data)) + ", skip_sid=" + str(skip_sid))
        sio.emit(event_name, data=data, skip_sid=skip_sid)

    car = Car(emit_func = my_emit_func)

    @sio.on('telemetry')
    def telemetry(sid, dashboard):
        print (" <- rx: " + str(sid))
        if dashboard:
            print (format(json.dumps(dashboard)))
        
        car.rx_telemetry(dashboard)

    @sio.on('connect')
    def connect(sid, environ):
        car.rx_connect(sid, environ)

    app = socketio.Middleware(sio, Flask(__name__))
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)

# vim: set sw=4 ts=4 et :

