var dnparm = document.getElementById("dnparm");
var dntrigger = document.getElementById("dntriger");

function request_notification(){
   if (!window.Notification){
       alert("Sorry, yor brower does not support notifications");
   }
   else {
       Notification.requestPermission(function (p) {
           if (p === "granted"){
               alert('You will receive notifications');
           }
       });
   }
}

function testValue(test_val, param) {
   var notify;
   var makeNotification = false;
  if(param === "temperature" && (test_val < 18 || test_val > 30))
    makeNotification = true;
  else if(param === "humidity" && (test_val < 40 || test_val > 70))
    makeNotification = true;

   if(makeNotification){
      notify = new Notification("Warning!", {
          body: "The Temperature or humidity has reached a critical value.",
          icon: '/server/images/warning.png'
       });
       notify.onclick = function () {
           console.log(this);
       }
   }    
}
localStorage.lastID = 0; //allow any value other than first one in database to be updated
function getLatest() {
    $.ajax({
        dataType: 'json',
        type: 'GET',
        url: 'load_latest.php',
        cache: false,
        success: function (result) {
          var id = result[0].id;
          var timestamp = result[0].timestamp;
          var temp = result[0].temperature;
          var humidity = result[0].humidity;
          if (id > localStorage.lastID) {
            testValue(temp, "temperature");
            testValue(humidity, "humidity");
            localStorage.lastID = id;
            getData();
            //alert("new value received");
          }

        },
        error: function (jq,status,message) {
            alert("notify error");
        }
    });
}

setInterval(getLatest, 2000);