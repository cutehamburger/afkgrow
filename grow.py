import tornado.web
import tornado.websocket
import tornado.ioloop
from tornado.ioloop import PeriodicCallback
import os.path
import threading
from threading import Timer
import signal
import sys
import serial
import json
import time
import datetime
import RPi.GPIO as GPIO

#9p-1pm (veg)
#9p-9a (flower)
startTime = datetime.time(hour=21, minute=0, second=0)
endTime = datetime.time(hour=13, minute=0, second=0)

LOWER_MOIST = 550
UPPER_MOIST = 280

#RPi Pins
RELAY_1 = 26
RELAY_2 = 20
RELAY_3 = 21
RELAY_4 = 16

#Initialize RPi GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_1,GPIO.OUT)
GPIO.setup(RELAY_2,GPIO.OUT)
GPIO.setup(RELAY_3,GPIO.OUT)
GPIO.setup(RELAY_4,GPIO.OUT)

ledState = GPIO.input(RELAY_4)
fanState = GPIO.input(RELAY_1)
pumpState = GPIO.input(RELAY_2)
lastWateredTime = 0;
fanSpeed = 50;

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout = 5)

WORK_INTERVAL = 0.5
SITE_POLL_SECONDS = 5


def getSensorJson():
    ser.write(b'1')
    sensorJson = ser.readline().decode('utf-8')
    print("[SERIAL] " + sensorJson)
    return sensorJson


def worker():
    global ledState, pumpState, fanState, fanspeed, lastWateredTime
    
    jsonDict = json.loads(getSensorJson())

    #handle LED
    if startTime < datetime.time() < endTime and not ledState:
        ledState = True
        GPIO.output(RELAY_4, GPIO.HIGH)
    if startTime > datetime.time() > endTime and ledState:
        ledState = False
        GPIO.output(RELAY_4, GPIO.LOW)
    
    #handle pump
    if LOWER_MOIST < jsonDict["moisture"] < UPPER_MOIST and pumpState:
        pumpState = False
        GPIO.output(RELAY_2, GPIO.LOW)
        lastWateredTime = datetime.time()
    if LOWER_MOIST > jsonDict["moisture"] > UPPER_MOIST and not pumpState:
        pumpState = True
        GPIO.output(RELAY_2, GPIO.High)
    
    jsonDict["ledState"] = ledState
    jsonDict["startTime"] = str(startTime)
    jsonDict["endTime"] = str(endTime)
    jsonDict["pumpState"] = pumpState
    jsonDict["lastWateredTime"] = str(lastWateredTime)
    jsonDict["fanState"] = fanState
    jsonDict["fanSpeed"] = fanSpeed
    jsonDict["sysTime"] = str(datetime.datetime.now().time())


    with open("data.json", 'w') as f:
        json.dump(jsonDict, f)

class setInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = threading.Event()
        thread = threading.Thread(target = self.__setInterval)
        thread.start()

    def __setInterval(self):
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()):
            nextTime += self.interval
            self.action()
    
    def cancel(self):
        self.stopEvent.set()

#Catch Ctrl+C
def signal_handler(signal, frame):
   print("...Ctrl+C caught")
   GPIO.cleanup()
   sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        print("[HTTP] User connected.")
        self.render("index.html")

class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("[WS] Connection was opened.")
        self.callback = PeriodicCallback(self.sendData, SITE_POLL_SECONDS * 1000)
        self.callback.start();

    def on_message(self, message):
        print("[WS] Incoming message:", message)
        if message == "fan_off" and fanState:
            fanState = False
            GPIO.output(RELAY_1, GPIO.HIGH)
        if message == "fan_on" and not fanState:
            fanState = True
            GPIO.output(RELAY_1, GPIO.LOW)

    def on_close(self):
        self.callback.stop()
        print ("[WS] Closed connection.")

    def sendData(self):
        with open("data.json", 'r') as f:
            siteJson = json.load(f)
            print("[WS] " + json.dumps(siteJson))
        self.write_message(siteJson)

app = tornado.web.Application(
    [
        (r'/', MainHandler),
        (r'/ws', WSHandler),
    ],
    template_path = os.path.join(os.path.dirname(__file__), "templates"),
    static_path = os.path.join(os.path.dirname(__file__), "static")
)

if __name__ == "__main__":
    try:
        app.listen(80)
        inter = setInterval(WORK_INTERVAL, worker)
        tornado.ioloop.IOLoop.instance().start()
    except:
        print("Tornado server stopped. ")
        GPIO.cleanup()
