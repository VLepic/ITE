const socket = io.connect("https://ite-api.vaclavlepic.com/");
// const socket = io.connect('147.228.173.86:5000');

// const alertSocket = io.connect('https://ite-alerts.vaclavlepic.com/')

// Přihlásit se k odběru teploty pro specifický tým
let teamName = 'pink';

let colorthemes = {
    'pink' : 'pink',
    'yellow': 'yellow',
    'green' : 'greenyellow',
    'red' : 'red',
    'blue' : 'blue',
    'black' : 'darkslateblue'
}

let checker
let dark = false

window.onload = async function () {
    checker = document.getElementById("switch")


    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        // dark mode
        dark = true
    }

    document.getElementById("teams").addEventListener("change" , async function(){

        await team_change();

    });

    checker.addEventListener("click" , function () {
        // console.log("l")
        dark = !dark;

        update();
    } );

    document.querySelectorAll(".data").forEach(p => {
        p.addEventListener("click" , async function(){
            let parent = p.parentElement

            if ( parent.querySelector(".dataframe").childElementCount > 0 ){
                // exists -> delete it

                parent.querySelector(".dataframe").innerHTML = ''
                
            }else{
                // doesnt exist -> create it

                await make_chart( parent.querySelector(".dataframe") , p.id.substring(1) )

            }
        })
    });

    // const tree = document.getElementById("tree")
    // tree.getElementById("board").addEventListener("click" , function(){

    // })

    await team_change();
}




function update(){
    // console.log("update")
    // console.log(dark)
    // update color theme

    document.querySelectorAll('.dataframe').forEach(el => {
        el.innerHTML = ''
    })

    document.querySelector(":root").style.setProperty('--team_col' , colorthemes[teamName])
    
    
    if( dark == true){
        document.documentElement.setAttribute("data-theme", "dark")
        document.querySelector("#sun").style.display = "none"
        document.querySelector("#moon").style.display = "block"
    }else{
        document.documentElement.setAttribute("data-theme", "light")
        document.querySelector("#sun").style.display = "block"
        document.querySelector("#moon").style.display = "none"
    }

    function add_broken_alert(element){
        element.classList.add("broken")
    }

    // Přihlášení k odběru teploty
    socket.emit('subscribe', { measurement: 'temperature', team: teamName });
    socket.on('temperature_update', function(data) {
        // console.log(data)
        if (data.team === teamName) {
            const tempParagraph = document.getElementById('temperature');
            tempParagraph.textContent = `Teplota: ${data.measurement_values[0]} ${units["temperature"]}`;
            document.getElementById("timestamp").textContent = data.time_values[0]  

            // pokud neprijde nova hodnota behem 12 hodin - indikace poskozeneho senzoru
            if ( time_since(data.time_values[0]  ) >= 12 ){
                add_broken_alert( document.getElementById("_temperature") )

                const panel = document.getElementById("tree")

                //img
                panel.getElementById("temperature_img").style.filter = "grayscale(1)"
                panel.getElementById("temp").style.backgroundColor = "orange"
            
            
            }

        }
    });




    // Přihlášení k odběru vlhkosti
    socket.emit('subscribe', { measurement: 'humidity', team: teamName });
    socket.on('humidity_update', function(data) {
        // console.log(data)
        if (data.team === teamName) {
            const humidityParagraph = document.getElementById('humidity');
            humidityParagraph.textContent = `Vlhkost: ${data.measurement_values[0]} ${units["humidity"]}`;
            document.getElementById("timestamp").textContent = data.time_values[0]  


            // pokud neprijde nova hodnota behem 12 hodin - indikace poskozeneho senzoru
            if ( time_since(data.time_values[0]  ) >= 1 ){
                add_broken_alert( document.getElementById("_humidity") )

                const panel = document.getElementById("tree")

                //img
                panel.getElementById("humidity_img").style.filter = "grayscale(1)"
                panel.getElementById("hum").style.backgroundColor = "crimson"
            
            
            }
        }
    });



    socket.emit('subscribe', { measurement: 'illumination', team: teamName });
    socket.on('illumination_update', function(data) {
        // console.log(data)
        if (data.team === teamName) {
            const humidityParagraph = document.getElementById('illumination');
            humidityParagraph.textContent = `Osvětlení: ${data.measurement_values[0]} ${units["illumination"]}`;
            document.getElementById("timestamp").textContent = data.time_values[0]  
        
            
            // pokud neprijde nova hodnota behem 12 hodin - indikace poskozeneho senzoru
            if ( time_since(data.time_values[0]  ) >= 12 ){
                add_broken_alert( document.getElementById("_illumination") )

                const panel = document.getElementById("tree")

                //img
                panel.getElementById("illumination_img").style.filter = "grayscale(1)"
                panel.getElementById("illum").style.backgroundColor = "crimson"
            
            
            }
        
        }
    });



    
}

// time passed since "time" in hours
function time_since(time){
    const tstamp = new Date(time);
    const currentTime = new Date().toISOString();

    const timeSince_mili = currentTime - tstamp;
    
    return timeSince_mili / ( 1000 * 60 * 60 )

}



let metadata = {}
// const keys = ["humidity","illumination","temperature"]
async function team_change() {
    teamName = document.getElementById("teams").value;

    url = `https://ite-api.vaclavlepic.com/${teamName}/metadata`

    // metadata = {}

    await fetch(url).then(function(response) {
        return response.json();
    }).then(function(data) {
        // console.log(data);
        return data
    }).then( async function(meta){
        // console.log(meta)

        const sensorInfo = document.getElementById("sensor_info")



        if(teamName == "pink"){

            url = "https://ite-api.vaclavlepic.com/static_info"

            await fetch(url).then(function(response) {
                // console.log(response.json())
                return response.json();
            }).then(function(data) {
                // console.log(data)
                // console.log(Object.keys(data))
                // console.log(Object.values(data))

                const keys = Object.keys(data)
                const dates = Object.values(data)

                sensorInfo.innerHTML = `
                    <div id="board">
                        <p>Základní deska: ${keys[2]}</p>
                        <li>Datum instalace: ${dates[2]}</li>
                    </div>
                    <div id="temp">
                        <p >Synchronizace reálného času: ${keys[3]}</p>
                        <li>Datum instalace: ${dates[3]}</li>
                    </div>
                `


                if( meta.temperature == true && meta.humidity == true){
                    document.getElementById("infotab_temperature").display = "block"
                    metadata["temperature"] = meta.num_of_temperature_datapoints

                    document.getElementById("temperature_img").display = "block"
                    // document.getElementById("temp").display = "block"

                    document.getElementById("infotab_humidity").display = "block"
                    metadata["humidity"] = meta.num_of_humidity_datapoints


                    document.getElementById("humidity_img").display = "block"



                    sensorInfo.innerHTML = sensorInfo.innerHTML.concat(`
                            <div id="hum">
                                <p>Senzor vlhkosti a teploty: ${keys[1]}</p>
                                <li>Datum instalace: ${dates[1]}</li>
                            </div>
                        `)

                }else{
                    document.getElementById("infotab_temperature").display = "none"

                    document.getElementById("temperature_img").display = "none"

                    document.getElementById("infotab_humidity").display = "none"

                    document.getElementById("humidity_img").display = "none"
                    // document.getElementById("temp").display = "none"

                }
                if( meta.illumination == true ){
                    document.getElementById("infotab_illumination").display = "block"
                    metadata["illumination"] = meta.num_of_illumination_datapoints

                    document.getElementById("illumination_img").display = "block"
                    // document.getElementById("illum").display = "block"

                    sensorInfo.innerHTML = sensorInfo.innerHTML.concat(`
                        <div id="illum">
                            <p >Senzor intenzity osvětlení: ${keys[0]}</p>
                            <li>Datum instalace: ${dates[0]}</li>
                        </div>
                    `)

                }else{
                    document.getElementById("infotab_illumination").display = "none"


                    document.getElementById("illumination_img").display = "none"
                    // document.getElementById("illum").display = "none"

                }


            })


        }else{

            sensorInfo.innerHTML = `
                <div id="board">
                    <p>Základní deska</p>
                    
                </div>
            `


            if( meta.temperature == true ){
                document.getElementById("infotab_temperature").display = "block"
                metadata["temperature"] = meta.num_of_temperature_datapoints

                document.getElementById("temperature_img").display = "block"
                // document.getElementById("temp").display = "block"

                sensorInfo.innerHTML = sensorInfo.innerHTML.concat(`
                        <div id="temp">
                            <p >Senzor teploty</p>
                        </div>
                    `)

            }else{
                document.getElementById("infotab_temperature").display = "none"

                document.getElementById("temperature_img").display = "none"
                // document.getElementById("temp").display = "none"

            }
            if( meta.humidity == true ){
                document.getElementById("infotab_humidity").display = "block"
                metadata["humidity"] = meta.num_of_humidity_datapoints


                document.getElementById("humidity_img").display = "block"
                // document.getElementById("hum").display = "block"

                sensorInfo.innerHTML = sensorInfo.innerHTML.concat(`
                    <div id="hum">
                        <p>Senzor vlhkosti</p>
                    </div>
                `)

            }else{
                document.getElementById("infotab_humidity").display = "none"

                document.getElementById("humidity_img").display = "none"
                // document.getElementById("hum").display = "none"
            }
            if( meta.illumination == true ){
                document.getElementById("infotab_illumination").display = "block"
                metadata["illumination"] = meta.num_of_illumination_datapoints

                document.getElementById("illumination_img").display = "block"
                // document.getElementById("illum").display = "block"

                sensorInfo.innerHTML = sensorInfo.innerHTML.concat(`
                    <div id="illum">
                        <p >Senzor intenzity osvětlení</p>
                    </div>
                `)

            }else{
                document.getElementById("infotab_illumination").display = "none"


                document.getElementById("illumination_img").display = "none"
                // document.getElementById("illum").display = "none"

            }
        }


    })

    // meta = await get_data(url).then( function(){



    // } )






    update();
}



// function getGraphData(){

// }

const units = {
    "temperature" : "°C",
    "humidity" : "%",
    "illumination" : "lux"
}


const backlook = 12 //12 hours

// let data
let canv
async function make_chart(wrapper , type = "temperature"){


    let dataDict

    // additional info
    // -> total measurements
    // let url = `https://ite-api.vaclavlepic.com/${teamName}/${type}?start_time=2024-10-25T00:00:00Z&end_time=2025-10-25T23:59:59Z`

    // // -> mean for past 24 hours
    // url = `https://ite-api.vaclavlepic.com/${teamName}/${type}?start_time=2024-10-25T00:00:00Z&end_time=2025-10-25T23:59:59Z`
    // dataDictAll = get_data(url)




    const currentTime = new Date().toISOString(); // Current time in ISO8601 format

    // Calculate the time 24 hours ago
    const beginTime = new Date(new Date().getTime() - 24 * 60 * 60 * 1000).toISOString();

    let url = `https://ite-api.vaclavlepic.com/${teamName}/${type}?start_time=${beginTime}&end_time=${currentTime}`

    await fetch(url).then(function(response) {
        return response.json();
    }).then(function(data) {
        // console.log(data);
        dataDict = data
    }).catch(function(err) {
        console.log('Fetch Error :-S', err);
    });

    // Convert data to a format usable by Chart.js
    const labels = dataDict.time_values.map(time => new Date(time)); // Convert ISO8601 to Date objects
    const data = dataDict.measurement_values;

    const mean = (data.reduce((partialSum, a) => partialSum + a, 0))/data.length;


    wrapper.innerHTML = `
        <br>
        <p>Průměrná hodnota za posledních 24h: ${mean.toFixed(2)} ${units[type]}</p>
        <br>
        <p>Počet měření celkem: ${metadata[type]}</p>
        <br>
    `



    if(teamName == "pink"){

        async function get_alerts(){
            url = `https://ite-alerts.vaclavlepic.com/aimtecapi/alerts/getboundaries/${type}`
            let alerts
            await fetch(url).then(function(response) {
                return response.json();
            }).then(function(data) {
                // console.log(data);
                alerts = data
            }).catch(function(err) {
                console.log('Fetch Error :-S', err);
            });
            return alerts
        }

        await get_alerts().then( function(alerts) {


            wrapper.innerHTML = wrapper.innerHTML.concat(`
                <p>Limity upozornění:</p>
                <span style="display : inline-block;" >
                    <p>Max: <input class="dial" type="number" id="max" value="${alerts.highValue}"> </p>
                    <p>Min: <input class="dial" type="number" id="min" value="${alerts.lowValue}"> </p>
                    <p>Heslo: <input class="dial" type="password" id="pass" value=""> </p>
                    <button style="margin-top:10px; margin-left:10px" id="submit" >Nastavit</button>
                </span>
                
                <br>
                `)

            wrapper.querySelector("#submit").addEventListener("click" , async function(){

                // console.log("press")
                const high = wrapper.querySelector("#max").value
                const low = wrapper.querySelector("#min").value
                const pass = wrapper.querySelector("#pass").value

                await fetch(`https://ite-alerts.vaclavlepic.com/aimtecapi/alerts/changeboundaries/${type}?login=pink&password=${pass}&min_value=${low}&max_value=${high}`, {
                    method: 'PUT',
                    headers: {
                      'Content-type': 'application/json'
                    },
                  }).then( function (response) {
                    // console.log(response)

                    if( response.ok == true ){
                        window.alert(`Meze pro ${type} byly změněny.`)
                        wrapper.innerHTML = ""
                        make_chart(wrapper , type)
                    }else{
                        window.alert(`Nesprávný vstup.`)
                    }

                  } );



            } )


        } )




    }



    // dataDict = await get_data(url)





    // chart itself
    canv = document.createElement("canvas")
    wrapper.appendChild(canv)
    const ctx = canv.getContext("2d")

    // Gradient fill for the line
    // const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    // gradient.addColorStop(0, 'rgba(75, 192, 192, 0.5)');
    // gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');


    // Chart.js configuration
    // const ctx = document.getElementById('timeChart').getContext('2d');
    new Chart(ctx, {
        type: 'line', // Line chart for time series
        data: {
            // borderColor: 'red',
            // backgroundColor: gradient,
            // borderWidth: 2,
            // tension: 0.4,
            // fill: true,
            // pointRadius: 5,
            // pointHoverRadius: 7,
            labels: labels, // Time values
            datasets: [{
                label: 'Measurement Values',
                data: data, // Measurement values
                borderColor: 'rgba(75, 192, 192, 1)', // Line color
                backgroundColor: 'rgba(75, 192, 192, 0.2)', // Fill color under the line
                borderWidth: 2,
                tension: 0.3 // Smooth line
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    type: 'time', // Use time scale
                    time: {
                        parser: 'ISO8601', // ISO8601 parsing for time strings
                        tooltipFormat: 'MMM dd, yyyy HH:mm:ss', // Tooltip format
                        displayFormats: {
                            minute: 'HH:mm:ss' // Format for x-axis ticks
                        }
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Measurement'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        title: (tooltipItems) => {
                            // Customize tooltip title to display a formatted date
                            const date = tooltipItems[0].label;
                            return new Date(date).toLocaleString();
                        }
                    }
                }
            }
        }
    });


}


async function get_data(url) {
    await fetch(url).then(function(response) {
        return response.json();
    }).then(function(data) {
        // console.log(data);
        return data
    }).catch(function(err) {
        console.log('Fetch Error :-S', err);
        return null
    });
}