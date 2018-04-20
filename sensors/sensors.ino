#include "Adafruit_Sensor.h"
#include "DHT.h"
#include "ArduinoJson.h"

#define DHT_PIN 2
#define DHT_TYPE DHT22 
#define MOISTURE_PIN 0

DHT myDHT(DHT_PIN, DHT_TYPE);

void setup(){
   Serial.begin(9600); 
   myDHT.begin();
}

void loop(){
   while(!Serial.available());
   Serial.readString();
   
   StaticJsonBuffer<200> jsonBuffer;
   JsonObject& sensorData= jsonBuffer.createObject(); 
   
   float humidity = myDHT.readHumidity();
   float temperature = myDHT.readTemperature();
   
   sensorData["humidity"] = isnan(humidity) ? -255 : humidity;
   sensorData["temperature"] = isnan(temperature) ? -255: temperature;
   sensorData["moisture"] = analogRead(MOISTURE_PIN);
   Serial.flush();
   sensorData.printTo(Serial);
   Serial.println();
}
