#coding=UTF-8
#from pokereval.card import Card
#from deuces import Card, Evaluator
#from pokereval.hand_evaluator import HandEvaluator
from websocket import create_connection
import math
import random
import json
import numpy as np
import sys

from deuces import Card
from deuces import Evaluator

ws = 0

def event_bet(data):
    return "fold", 0

def event_action(data):
    return "fold", 0

def event_handler(event_name, data):
    global ws
    
    print ("...input event", event_name)
    
    if event_name == "__bet":
        action, amount = event_bet(data)
        msg = json.dumps({
            "eventName": "__action",
            "data": {
                "action": action,
                "playerName": name,
                "amount": amount
            }})
        print(format(msg))
        ws.send(msg)
        
    
    elif event_name == "__action":
        action, amount = event_action(data)
        msg = json.dumps({
            "eventName": "__action",
            "data": {
                "action": action,
                "playerName": name,
                "amount": amount
            }})
        print(format(msg))
        ws.send(msg)
    
    return 0
        

def wsloop(name, url):
    global ws
    
    try:
        ws = create_connection(connect_url)

        msg = json.dumps({
            "eventName": "__join",
            "data": {
                "playerName":  name
            }
        })
        print ("...Join game with name", name)
        ws.send(msg)
    
        while 1:
            result = ws.recv()
            
            msg = json.loads(result)
            
            event_name = msg["eventName"]
            data = msg["data"]
            print("->", event_name, ":", json.dumps(data))
            event_handler(event_name, data)
            
    except Exception, e:
        print(" * ERROR: Exception in main loop", e.message)
        ws.close()
        return

if __name__ == '__main__':
    if len(sys.argv) == 3:
        name = sys.argv[1]
    else:
        print (sys.argv[0], " <name> <url>")
        sys.exit()
    
    if len(sys.argv) == 3:
        connect_url = sys.argv[2]
    else:
        print (format(sys.argv[0]), " <name> <url>")
        sys.exit()
    
    print ("...Start game with name: ", name, "url: ", connect_url)
    
    while 1:
        wsloop(name, connect_url)

#;