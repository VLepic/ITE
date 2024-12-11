// Connect to the WebSocket server
const alert_socket = io.connect('https://ite-alerts.vaclavlepic.com/'); // Replace with your WebSocket server URL if needed

// Handle temperature alerts
alert_socket.on('temperature_alert', function (data) {
    // const tempParagraph = document.getElementById('temperature');
    // tempParagraph.textContent = `Temperature: ${data.value} °C (Alert: ${data.alert})`;
    
    add_alert("_temperature")
    console.log('Temperature Alert:', data);
});

// Handle humidity alerts
alert_socket.on('humidity_alert', function (data) {
    // const humidityParagraph = document.getElementById('humidity');
    // humidityParagraph.textContent = `Humidity: ${data.value} % (Alert: ${data.alert})`;
    // document.querySelector("_humidity").classList.add("alert")
    add_alert("_humidity")
    console.log('Humidity Alert:', data);
});

// Handle illumination alerts
alert_socket.on('illumination_alert', function (data) {
    // const illuminationParagraph = document.getElementById('illumination');
    // illuminationParagraph.textContent = `Illumination: ${data.value} lux (Alert: ${data.alert})`;
    // document.querySelector("_illumination").classList.add("alert")
    add_alert("_illumination")
    console.log('Illumination Alert:', data);
});

// Handle connection
alert_socket.on('connect', function () {
    console.log('Connected to WebSocket server');
});

// Handle disconnection
alert_socket.on('disconnect', function () {
    console.log('Disconnected from WebSocket server');
});

// Handle server errors
alert_socket.on('error', function (error) {
    console.error('Server error:', error);
});



function add_alert(element_id){
    let e = document.getElementById(element_id)
    if( e !== null ){
        e.classList.add("alert")
        if(e.classList.contains("broken")){
            e.style.cssText += alarms["alert_broken"]
        }else{
            e.style.cssText += alarms["alert"]
        }


        
    }
    
}

function add_broken_alert(element){
    element.classList.add("broken")
    if(e.classList.contains("alert")){
        e.style.cssText += alarms["alert_broken"]
    }else{
        e.style.cssText += alarms["broken"]
    }
}