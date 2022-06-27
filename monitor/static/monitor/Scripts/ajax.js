function getData() {
    $.ajax({
        dataType: 'json',
        type: 'GET',
        url: 'send.php',
        cache: false,
        success: function (result) {
            $('#data-table tbody').children().remove();
            var timeArray = [];
            var tempArray = [];
            var humidArray = [];
            var maxArray = [];
            var minArray = [];
            var maxH = [];
            var minH = [];
            for(var i=0; i<result.length; i++){
                var timestamp = result[i].timestamp;
                var temp = result[i].temperature;
                temp = parseFloat(temp);
                temp = temp.toFixed(2);
                var humidity = result[i].humidity;
                var timeOfDay = dateFormat(timestamp)+" "+timeFormat(timestamp);
                addData(timeOfDay, temp, humidity);
                timeArray.push(timeFormat(timestamp));
                tempArray.push(temp);
                humidArray.push(humidity);
                maxArray.push(27);
                minArray.push(18);
                maxH.push(60);
                minH.push(40);
            }
            drawGraph(timeArray,tempArray,humidArray,maxArray, minArray, maxH, minH);
        },
        error: function (jq,status,message) {
            alert(message);
        }
    });
}
//setInterval(getData, 2000);
//getData();
function addData(timeOfDay,temperature, humidity) {
    var table = $('#data-table');
    table.append("<tr><td>"+timeOfDay+"</td><td>"+temperature+"</td><td>"+humidity+"</td></tr>");
}

/*
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

function drawGraph(timeArray, tempArray, humidArray, maxArray, minArray, maxH, minH) {
    var graph = document.getElementById('graph');
    var trace1 = {
        x: timeArray,
        y: tempArray,
        mode: 'lines+markers',
        name: 'temperature'
    };

    var trace2 = {
        x: timeArray,
        y: humidArray,
        mode: 'lines+markers',
        name: 'humidity'
    };

    var trace3 = {
        x: timeArray,
        y: maxArray,
        mode: 'lines',
        name: 'max T threshold'
    };
    var trace4 = {
        x: timeArray,
        y: minArray,
        mode: 'lines',
        name: 'Min T threshold'
    };

    var trace5 = {
        x: timeArray,
        y: maxH,
        mode: 'lines',
        name: 'Max H threshold'
    };

    var trace6 = {
        x: timeArray,
        y: minH,
        mode: 'lines',
        name: 'Min H threshold'
    };

    var data = [trace1, trace2, trace3, trace4, trace5, trace6];

    var layout = {
        title: 'Graph of Temperature and Humidity against Time',
        xaxis: {
            title: 'Time'
        },
        yaxis: {
            title: 'Temperature (0C), Humidity (%)'
        }
    };
    Plotly.newPlot(graph, data, layout);
}
*/

function updateMain() {
    $.ajax({
        dataType: 'html',
        type: 'GET',
        url: 'mains_update',
        cache: false,
        success: function (result) {
            var mains_table = $('#mains_table');
            mains_table.children().remove();
            mains_table.append(result);
            //alert("Succeeded update");
        },
        error: function (jq,status,message) {
            alert(message);
        }
    });
}


function updateGen() {
    $.ajax({
        dataType: 'html',
        type: 'GET',
        url: 'gen_update',
        cache: false,
        success: function (result) {
            var mains_table = $('#gen_table');
            mains_table.children().remove();
            mains_table.append(result);
            //alert("Succeeded update");
        },
        error: function (jq,status,message) {
            alert(message);
        }
    });
}

function updateStatus() {
    $.ajax({
        dataType: 'html',
        type: 'GET',
        url: 'status_update',
        cache: false,
        success: function (result) {
            var status_table = $('#status-info');
            status_table.children().remove();
            status_table.append(result);
            //alert("Succeeded update");
        },
        error: function (jq,status,message) {
            alert(message);
        }
    });
}

function updateAlarms() {
    $.ajax({
        dataType: 'html',
        type: 'GET',
        url: 'alarms_update',
        cache: false,
        success: function (result) {
            var status_table = $('#alarms_table');
            status_table.children().remove();
            status_table.append(result);
            //alert("Succeeded alarms update");
        },
        error: function (jq,status,message) {
            alert(message);
        }
    });
}

setInterval(updateMain, 2000);
setInterval(updateGen, 2000);
setInterval(updateStatus, 2000);
setInterval(updateAlarms, 2000);