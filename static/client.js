$(document).ready(function(){

    var WEBSOCKET_ROUTE = "/ws";
    var IMG_WEBSOCKET_ROUTE = "/wsimg";

	var target_fps = 1;

	var request_start_time = performance.now();
	var start_time = performance.now();
	var time = 0;
	var request_time = 0;
	var time_smoothing = 0.9;
	var request_time_smoothing = 0.2;
	var target_time = 1000 / target_fps;


    if(window.location.protocol == "http:"){
	    var ws = new WebSocket("ws://" + window.location.host + WEBSOCKET_ROUTE);
	    var wsimg = new WebSocket("ws://" + window.location.host + IMG_WEBSOCKET_ROUTE);
    }
    else if(window.location.protocol == "https:"){
	    var ws = new WebSocket("wss://" + window.location.host + WEBSOCKET_ROUTE);
	    var wsimg = new WebSocket("wss://" + window.location.host + IMG_WEBSOCKET_ROUTE);
    }

//Image websocket stuff
    wsimg.binaryType = 'arraybuffer';

    function requestImage() {
        request_start_time = performance.now();
    	//console.log("send for more");
        wsimg.send('more')
	};

	wsimg.onopen = function() {
    	console.log("Image connection was established");
    	start_time = performance.now();
    	requestImage();
	};

	wsimg.onmessage = function(evt) {
    	//console.log("msg received");
    	var arrayBuffer = evt.data;
    	var imgBlob = new Blob([new Uint8Array(arrayBuffer)], {type: 'image/jpeg'});
    	//console.log(window.URL.createObjectURL(imgBlob));
    	//$("#ws-img-url").text(window.URL.createObjectURL(imgBlob));
    	$("#ws-img").attr("src", window.URL.createObjectURL(imgBlob));

    	var end_time = performance.now();
    	var current_time = end_time - start_time;
    	// smooth with moving average
    	time = (time * time_smoothing) + (current_time * (1.0 - time_smoothing));
    	start_time = end_time;
    	var fps = Math.round(1000 / time);
  	 	$("#ws-fps").text(fps);

		var current_request_time = performance.now() - request_start_time;
    	// smooth with moving average
	    request_time = (request_time * request_time_smoothing) + (current_request_time * (1.0 - request_time_smoothing));
    	var timeout = Math.max(0, target_time - request_time);

    	setTimeout(requestImage, timeout);
	};


//Json websocket stuff
    ws.onopen = function(){
    	console.log("Json connection was established");
        $("#ws-status").html("Connected");
    };

    ws.onmessage = function(evt){
        //$("#ws-json").text(evt.data);
        var parsedData = JSON.parse(evt.data);


		var tempF = parsedData.temperature * 9 / 5 + 32;
        tempF = Math.ceil(tempF * 100) / 100;

		$("#ws-temperature").text(parsedData.temperature);
		$("#ws-temperatureF").text(tempF);

		$("#ws-timestamp").text(parsedData.timestamp);
        $("#ws-humidity").text(parsedData.humidity);
        $("#ws-soilMoisture").text(parsedData.moisture);
        $("#ws-ledState").text(parsedData.ledState);
        $("#ws-pumpState").text(parsedData.pumpState);
        $("#ws-lastWatered").text(parsedData.lastWateredTime);
        $("#ws-fanState").text(parsedData.fanState);
        $("#ws-fanSpeed").text(parsedData.fanSpeed);

    	$("#ws-targetTemperature").text(parsedData.targetTemperature);
    	$("#ws-targetHumidity").text(parsedData.targetHumidity);
        $("#ws-startWaterThreshold").text(parsedData.startWaterThreshold);
        $("#ws-endWaterThreshold").text(parsedData.endWaterThreshold);
        $("#ws-ledStart").text(parsedData.startTime);
        $("#ws-ledStop").text(parsedData.endTime);

    };

    ws.onclose = function(evt){
        $("#ws-status").html("Disconnected");
    };

});
