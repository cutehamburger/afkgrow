import tornado.web
import tornado.websocket
import tornado.ioloop
from tornado.ioloop import PeriodicCallback
import os.path
import signal
import sys
import serial
import json
import time

#Periodic Callback Frequency
POLL_FREQ = 1000

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout = 2)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        print("[HTTP]User Connected.")
        self.render("index.html")

class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        self.callback = PeriodicCallback(self.sendData, POLL_FREQ)
        print("[WS] Connection was opened with callback frequency " + str(POLL_FREQ) + " ms")
        self.callback.start()

    def on_message(self, message):
        print("[WS] Incoming message:", message)

    def on_close(self):
        self.callback.stop()
        print ("[WS] Closed Connection")

    def sendData(self):
        ser.write(b'1')
        sensorJson = ser.readline().decode("utf-8").strip()
        f = open("sensorOutput.json", 'w')
        json.dump(sensorJson, f)
        print(sensorJson)
        f.close()
        parsedJson = json.loads(sensorJson)
        self.write_message(sensorJson)

app = tornado.web.Application(
   [
      (r'/', MainHandler),
      (r'/ws', WSHandler),
      (r'/favicon.ico', tornado.web.StaticFileHandler,{"path": ""})
   ],
   template_path = os.path.join(os.path.dirname(__file__), "templates"),
   static_path = os.path.join(os.path.dirname(__file__), "static")
   )

if __name__ == "__main__":
    app.listen(80)
    tornado.ioloop.IOLoop.instance().start()
