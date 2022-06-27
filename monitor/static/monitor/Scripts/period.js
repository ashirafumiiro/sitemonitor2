function getData(date1, date2) {
    if(date1 == "undefined")
        date1 = "";
    if (date2 == "undefined")
        date2 = "";
    $.ajax({
        dataType: 'json',
        type: 'POST',
        url: 'load.php',
        data: {
            from_date: date1,
            to_date: date2
        },
        cache: false,
        success: function (result) {
            var display = $('#display-area');
            var message = $('#message');
            if (result.length ==0){
                display.hide();
                message.show();
            }
            else {
                message.hide();
                display.show();
                var timeArray = [];
                var tempArray = [];
                var humidArray = [];
                var maxH =[];
                var minH = [];
                var maxT =[];
                var minT = [];
                var highestTemperature = 0.0;
                var highestHumidity = 0.0;
                var minTemp = 70.0;
                var minHumidity = 70.0;
                var count = 0;
                var humiditySum = 0.0;
                var max_temp_time = "";
                var min_temp_time = "";
                var max_humid_time = "";
                var min_humid_time = "";
                var temperatureSum = 0.0;
                for(var i=0; i<result.length; i++){
                    var timestamp = result[i].timestamp;
                    var temp = result[i].temperature;
                    temp = parseFloat(temp);
                    temp = temp.toFixed(2);
                    var humidity = result[i].humidity;
                    var timeOfDay = dateFormat(timestamp)+" "+timeFormat(timestamp);
                    timeArray.push(timeFormat(timestamp));
                    tempArray.push(temp);
                    maxH.push(60);
                    minH.push(40);
                    minT.push(18);
                    maxT.push(27);

                    humidArray.push(humidity);
                    if (temp > highestTemperature){
                        highestTemperature = temp;
                        max_temp_time = timeOfDay;
                    }
                    if (humidity > highestHumidity){
                        highestHumidity = humidity;
                        max_humid_time = timeOfDay;
                    }
                    if(minTemp > temp){
                        minTemp = temp;
                        min_temp_time = timeOfDay;
                    }
                    if(minHumidity > humidity){
                        minHumidity = humidity;
                        min_humid_time = timeOfDay;
                    }
                    temperatureSum += parseFloat(temp);
                    humiditySum += parseFloat(humidity);
                    count++;
                }
                //Update the page
                $('#min-humidity').html(minHumidity);
                $('#min-temp').html(minTemp);
                $('#max-temp').html(highestTemperature);
                $('#max-humidity').html(highestHumidity);
                $('#max-humidity-time').html(max_humid_time);
                $('#min-humidity-time').html(min_humid_time);
                $('#min-temp-time').html(min_temp_time);
                $('#max-temp-time').html(max_temp_time);
                var average_temp = temperatureSum / count;
                var average_humidity = humiditySum / count;
                $('#temp-avg').html(average_temp);
                $('#humidity-avg').html(average_humidity);
                plotTemp(timeArray, tempArray, maxT, minT);
                plotHumidity(timeArray, humidArray, maxH, minH);
            }

        },
        error: function (jq,status,message) {
            alert(message);
        }
    });
}
getData("undefined", "undefined");

function timeFormat(timestamp) {
// Create a date object with the current time
    var now = new Date(timestamp*1000);
// Create an array with the current hour, minute and second
    var time = [ now.getHours(), now.getMinutes(), now.getSeconds()];
// Determine AM or PM suffix based on the hour
    var suffix = ( time[0] < 12 ) ? "AM" : "PM";
// Convert hour from military time
    time[0] = ( time[0] < 12 ) ? time[0] : time[0] - 12;
// If hour is 0, set it to 12
    time[0] = time[0] || 12;
// If seconds and minutes are less than 10, add a zero
    for ( var i = 1; i < 3; i++ ) {
        if ( time[i] < 10 ) {
            time[i] = "0" + time[i];
        }
    }
// Return the formatted string
    return time.join(":") + " " + suffix;
}

function dateFormat(timestamp) {
    var now = new Date(timestamp*1000);
    // Create an array with the current month, day and time
    var date = [ now.getMonth() + 1, now.getDate(), now.getFullYear() ];
    return date.join("/")
}

function plotTemp(timeArray, tempArray, maxT, minT) {
    var graph = document.getElementById('temp-graph');
    var trace1 = {
        x: timeArray,
        y: tempArray,
        mode: 'lines+markers',
        name: 'temperature'
    };

    var trace2 = {
        x: timeArray,
        y: maxT,
        mode: 'lines',
        name: 'max T threshold'
    };
    var trace3 = {
        x: timeArray,
        y: minT,
        mode: 'lines',
        name: 'Min T threshold'
    };

    var data = [trace1, trace2, trace3];

    var layout = {
        title: 'Temperature against Time',
        xaxis: {
            title: 'Time'
        },
        yaxis: {
            title: 'Temperature'
        }
    };
    Plotly.newPlot(graph, data, layout);


}

function plotHumidity(timeArray, humidArray, maxH, minH) {
    var graph = document.getElementById('humidity-graph');
    var trace1 = {
        x: timeArray,
        y: humidArray,
        mode: 'lines+markers',
        name: 'Humidity'
    };

    var trace2 = {
        x: timeArray,
        y: maxH,
        mode: 'lines',
        name: 'Max H threshold'
    };

    var trace3 = {
        x: timeArray,
        y: minH,
        mode: 'lines',
        name: 'Min H threshold'
    };

    var data = [trace1, trace2, trace3];

    var layout = {
        title: 'Graph Humidity against Time',
        xaxis: {
            title: 'Time'
        },
        yaxis: {
            title: 'Humidity (%)'
        }
    };
    Plotly.newPlot(graph, data, layout);
}

var button = document.getElementById('submit-date');
button.onclick = function (e) {
    e.preventDefault();
    var date1 = $('#datepicker').val();
    var date2 = $('#datepicker2').val();
    getData(date1, date2);
};

var timeButton = document.getElementById('submit-time');
timeButton.onclick = function (e) {
    e.preventDefault();
    var time1 = $('#time-picker1').val();
    var time2 = $('#time-picker2').val();
    var date = $('#datepicker').val();
    if (time1 == "" || time2 == "" || date == ""){
        alert('please fill in all required fields as directed in the help menu');
    }
    else {
        getData2(time1, time2, date);
    }
};

function getData2(time1, time2, date) {
    $.ajax({
        dataType: 'json',
        type: 'POST',
        url: 'load.php',
        data: {
            from_time: time1,
            to_time: time2,
            date: date
        },
        cache: false,
        success: function (result) {
            var display = $('#display-area');
            var message = $('#message');
            if (result.length ==0){
                display.hide();
                message.show();
            }
            else {
                message.hide();
                display.show();
                var timeArray = [];
                var tempArray = [];
                var humidArray = [];
                var maxH =[];
                var minH = [];
                var maxT =[];
                var minT = [];
                var highestTemperature = 0;
                var highestHumidity = 0;
                var minTemp = 70;
                var minHumidity = 70;
                var count = 0;
                var humiditySum = 0;
                var max_temp_time = "";
                var min_temp_time = "";
                var max_humid_time = "";
                var min_humid_time = "";
                var temperatureSum = 0;
                for(var i=0; i<result.length; i++){
                    var timestamp = result[i].timestamp;
                    var temp = result[i].temperature;
                    var humidity = result[i].humidity;
                    temp = parseFloat(temp);
                    temp = temp.toFixed(2);
                    var timeOfDay = dateFormat(timestamp)+" "+timeFormat(timestamp);
                    timeArray.push(timeFormat(timestamp));
                    tempArray.push(temp);
                    humidArray.push(humidity);
                    maxH.push(60);
                    minH.push(40);
                    minT.push(18);
                    maxT.push(27);
                    if (temp > highestTemperature){
                        highestTemperature = temp;
                        max_temp_time = timeOfDay;
                    }
                    if (humidity > highestHumidity){
                        highestHumidity = humidity;
                        max_humid_time = timeOfDay;
                    }
                    if(minTemp > temp){
                        minTemp = temp;
                        min_temp_time = timeOfDay;
                    }
                    if(minHumidity > humidity){
                        minHumidity = humidity;
                        min_humid_time = timeOfDay;
                    }
                    temperatureSum += parseFloat(temp);
                    humiditySum += parseFloat(humidity);
                    count++;
                }
                //Update the page
                $('#min-humidity').html(minHumidity);
                $('#min-temp').html(minTemp);
                $('#max-temp').html(highestTemperature);
                $('#max-humidity').html(highestHumidity);
                $('#max-humidity-time').html(max_humid_time);
                $('#min-humidity-time').html(min_humid_time);
                $('#min-temp-time').html(min_temp_time);
                $('#max-temp-time').html(max_temp_time);
                var average_temp = temperatureSum / count;
                var average_humidity = humiditySum / count;
                $('#temp-avg').html(average_temp);
                $('#humidity-avg').html(average_humidity);
                plotTemp(timeArray, tempArray, maxT, minT);
                plotHumidity(timeArray, humidArray, maxH, minH);
            }

        },
        error: function (jq,status,message) {
            alert(message);
        }
    });
}