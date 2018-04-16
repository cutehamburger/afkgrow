import serial
import json

HUMIDITY_HIGH = 55
HUMIDITY_LOW = 45
TEMP_HIGH = 80
TEMP_LOW = 70
MOIST_LOW = 10
MOIST_HIGH = 60

try:
    ser = serial.Serial('/dev/ttyUSB0', 9600)
except serial.SerialException as e:
    print("Caught exeption opening serial connection: " + e)

#{"humidity":41.2,"celsius":23.7,"fahrenheit":74.66,"moisture":-2}

while True:
    try:
        (sensorJson = ser.readline().decode("utf-8").strip())
        print(sensorJson)
    except serial.SerialException as e:
        print("Caught exeption reading from serial: " + e)
    
    try:
        parsedJson = json.loads(sensorJson)
    except json.JSONDecodeError as e:
        print("Error parsing  sensor json: " + e)

    humidity = parsedJson["humidity"]
    celsius = parsedJson["celsius"]
    fahrenheit = parsedJson["fahrenheit"]
    moisture = parsedJson["moisture"]
    
    #try:
    #    saveFile = open("./save","r+w")
    #except IOError as e:
    #    print("Error opening ./save: " + e)

    

    #if humidity > HUMIDITY_HIGH:
        #speed up fans
    #elif humidity < HUMIDITY_LOW:
        #slow down fans

    #if moisture < MOIST_LOW:
        #pump water
    #elif moisture > MOIST_HIGH:
        #alert




