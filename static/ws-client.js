$(document).ready(function(){
   
    var WEBSOCKET_ROUTE = "/ws";
    if(window.location.protocol == "http:"){
	var ws = new WebSocket("ws://" + window.location.host + WEBSOCKET_ROUTE);
    }
    else if(window.location.protocol == "https:"){
	var ws = new WebSocket("wss://" + window.location.host + WEBSOCKET_ROUTE);
    }
	
    ws.onopen = function(e){
        $("#ws-status").html("Connected");
    };
    ws.onmessage = function(e){
        $("#ws-json").text(e.data);
        var parsedData = JSON.parse(e.data);
	$("#ws-timestamp").text(parsedData.timestamp);
	$("#ws-temperature").text(parsedData.temperature);
	$("#ws-temperatureF").text(parsedData.temperature * 9 / 5 + 32);
        $("#ws-humidity").text(parsedData.humidity);
        $("#ws-soilMoisture").text(parsedData.moisture);
        $("#ws-ledState").text(parsedData.ledState);
        $("#ws-pumpState").text(parsedData.pumpState);
        $("#ws-lastWatered").text(parsedData.lastWateredTime);
        $("#ws-fanState").text(parsedData.fanState);
        $("#ws-fanSpeed").text(parsedData.fanSpeed);
	
	$("#ws-targetTemperature").text(parsedData.targetTemperature);
	$("#ws-targetHumidity").text(parsedData.targetHumidity);
        $("#ws-targetSoilMoisture").text(parsedData.targetMoisture);
        $("#ws-ledStart").text(parsedData.startTime);
        $("#ws-ledStop").text(parsedData.endTime);
      
   };
   ws.onclose = function(e){
      $("#ws-status").html("Disconnected");
   };

   $("#refresh").click(function(){
      location.reload();
   });

});
