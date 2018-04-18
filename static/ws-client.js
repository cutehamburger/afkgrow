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
      $("#ws-temperature").text(parsedData.temperature);
      $("#ws-humidity").text(parsedData.humidity);
      $("#ws-soil-moisture").text(parsedData.moisture);
   };
   ws.onclose = function(e){
      $("#ws-status").html("Disconnected");
   };

   $("#refresh").click(function(){
      location.reload();
   });

});
