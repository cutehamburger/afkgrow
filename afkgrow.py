import tornado.web
import tornado.websocket
import tornado.httpserver
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

#CONSTANTS
SENSOR_DRY = 550
SENSOR_WET = 280
WORK_INTERVAL = 0.5
SITE_POLL_SECONDS = 5
PUMP_RELAY_1= 26
FAN_RELAY_2 = 20
#FAN_RELAY_3 = 21
LED_RELAY = 16
FAN_PWM_PIN = 19
PWM_FREQ = 200

#LED TIMER
startTime = datetime.time(hour=21, minute=0, second=0)
endTime = datetime.time(hour=13, minute=0, second=0)

#DHT
targetTemperature = (23, 26)
targetHumidity = (48, 52)

#WATERING
startWaterThreshold = 50
endWaterThreshold = 90
lastWateredTime = None

#GPIO SETUP
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_RELAY, GPIO.OUT)
GPIO.setup(PUMP_RELAY_1, GPIO.OUT)
GPIO.setup(FAN_RELAY_2, GPIO.OUT)
#GPIO.setup(FAN_RELAY_3, GPIO.OUT)
GPIO.setup(FAN_PWM_PIN, GPIO.OUT)

#COMPONENT STATES
ledState = False
pumpState = False
fanState = GPIO.input(FAN_RELAY_2)

fanSpeed = 30
fanSpeedSignal = GPIO.PWM(FAN_PWM_PIN, PWM_FREQ)
fanSpeedSignal.start(fanSpeed)

print("[start] ledState: " + str(ledState) +
      "\n[start] pumpState: " + str(pumpState) +
      "\n[start] fanState: " + str(fanState) +
      "\n[start] fanSpeed: " + str(fanSpeed))

#Catch Ctrl+C
def signal_handler(signal, frame):
   print("\n[Ctrl+C caught]")
   GPIO.cleanup()
   workerThread.stopEvent.set()
   sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def getSensorJson():
    ser.write(b'123')
    sensorJson = ser.readline().decode('utf-8')
    #print("[SERIAL] " + sensorJson)
    return sensorJson

def translate(value, leftMin, leftMax, rightMin, rightMax):
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    valueScaled = float(value - leftMin) / float(leftSpan)
    return rightMin + (valueScaled * rightSpan)

def ledOn():
    global ledState
    ledState = True
    print("[state] LED on")
    GPIO.output(LED_RELAY, GPIO.HIGH)

def ledOff():
    global ledState
    ledState = False
    print("[state] LED off")
    GPIO.output(LED_RELAY, GPIO.LOW)

def saturate(howMoist, timeStamp):
    global startWaterThreshold, endWaterThreshold, pumpState, lastWateredTime
    if  howMoist <= startWaterThreshold and not pumpState:
        pumpState = True
        print("[state] Pump Start. Moist:" + str(howMoist) + "  Thresh:" + str(startWaterThreshold) + " Last:" + str(lastWateredTime))
        GPIO.output(PUMP_RELAY_1, GPIO.LOW)
    elif howMoist >= endWaterThreshold and pumpState:
        pumpState = False
        lastWateredTime = timeStamp
        print("[state] Pump Stop. Moist:" + str(howMoist) + "  Thresh:" + str(endWaterThreshold) + " Last:" + str(lastWateredTime))
        GPIO.output(PUMP_RELAY_1, GPIO.HIGH)
    else:
        return

def work():
    global ledState, pumpState, fanState, fanSpeed, fanSpeedSignal

    now = datetime.datetime.now().time().replace(microsecond=0)
    jsonDict = json.loads(getSensorJson())
    jsonDict["moisture"] = translate(jsonDict["moisture"], SENSOR_DRY, SENSOR_WET, 0, 100)

    #handle LED (active high, normally off)
    if startTime < endTime:
        if startTime <= now <= endTime and not ledState:
            ledOn()
        elif (now >= endTime or now <= startTime) and ledState:
            ledOff()
    else:
        if (now >= startTime or now <= endTime) and not ledState:
            ledOn()
        elif startTime >= now >= endTime and ledState:
            ledOff()

    #handle pump (active low, normally off)
    saturate(jsonDict["moisture"], now)

    #handle fan (active low, normally on)
    pauseCondition = False;
    if  pauseCondition and fanState:
        fanState = False
        fanSpeedSignal.Stop()
        print("[state] Fans stopped")
        GPIO.output(FAN_RELAY_2, GPIO.LOW)
    if  not pauseCondition and not fanState:
        fanState = True
        fanSpeedSignal.start(fanSpeed)
        print("[state] Fans started")
        GPIO.output(FAN_RELAY_2, GPIO.HIGH)

    #handle fan speed (function of temperature)
    if jsonDict["temperature"] < targetTemperature[0] and fanState:
        fanSpeed = 35
        fanSpeedSignal.ChangeDutyCycle(fanSpeed)
    elif jsonDict["temperature"] > targetTemperature[1] and fanState:
        fanSpeed = 100
        fanSpeedSignal.ChangeDutyCycle(fanSpeed)
    elif fanState:
        fanSpeed = 60
        fanSpeedSignal.ChangeDutyCycle(fanSpeed)

    jsonDict["ledState"] = ledState
    jsonDict["startTime"] = str(startTime)
    jsonDict["endTime"] = str(endTime)
    jsonDict["pumpState"] = pumpState
    jsonDict["lastWateredTime"] = str(lastWateredTime)
    jsonDict["fanState"] = fanState
    jsonDict["fanSpeed"] = fanSpeed
    jsonDict["timestamp"] = str(now)
    jsonDict["targetTemperature"] = targetTemperature
    jsonDict["targetHumidity"] = targetHumidity
    jsonDict["targetMoisture"] = endWaterThreshold

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
        if message == "fan_on" and not fanState:
            fanState = True

    def on_close(self):
        self.callback.stop()
        print ("[WS] Closed connection.")

    def sendData(self):
        with open("data.json", 'r') as f:
            siteJson = json.load(f)
            #print("[WS] " + json.dumps(siteJson))
            self.write_message(siteJson)

app = tornado.web.Application(
    [
        (r'/', MainHandler),
        (r'/ws', WSHandler),
    ],
    template_path = os.path.join(os.path.dirname(__file__), "templates"),
    static_path = os.path.join(os.path.dirname(__file__), "static"),
)


server = tornado.httpserver.HTTPServer(app,
    ssl_options = {
        "certfile": os.path.join(os.path.dirname(__file__),"ssl/cert.pem"),
        "keyfile": os.path.join(os.path.dirname(__file__), "ssl/key.pem")
    }
)

ser = serial.Serial('/dev/ttyUSB0', 4800, timeout = 5)

workerThread = None

if __name__ == "__main__":
    try:
        server.listen(443)
        workerThread = setInterval(WORK_INTERVAL, work)
        print("Tornado server starting.")
        tornado.ioloop.IOLoop.instance().start()
    except:
        print("Tornado server stopped.")
        #GPIO.cleanup()
