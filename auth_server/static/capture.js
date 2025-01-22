document.addEventListener("DOMContentLoaded", function () {
    startup();
});

let video = null;
let canvas = null;
let startbutton = null;
let recognizebutton = null;
let loginbutton = null;
let submitLoginButton = null;
let results = null;
let streaming = false;
let width = 320; // Default width of the canvas
let height = 0; // Height will be calculated based on the aspect ratio

function startup() {
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    startbutton = document.getElementById('startbutton');
    recognizebutton = document.getElementById('recognizebutton');
    loginbutton = document.getElementById('loginbutton');
    submitLoginButton = document.getElementById('submit-login');
    results = document.getElementById('results');

    console.log("Startup initialized.");
    console.log("Elements fetched:", { video, canvas, recognizebutton, loginbutton, submitLoginButton, results });

    if (!video || !canvas || !recognizebutton || !loginbutton || !submitLoginButton || !results) {
        console.error("One or more elements could not be found in the DOM.");
        return;
    }

    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        .then(function (stream) {
            video.srcObject = stream;
            video.play();
        })
        .catch(function (err) {
            console.error("An error occurred while accessing the camera:", err);
        });

    video.addEventListener('canplay', function (ev) {
        if (!streaming) {
            height = video.videoHeight / (video.videoWidth / width);
            video.setAttribute('width', width);
            video.setAttribute('height', height);
            canvas.setAttribute('width', width);
            canvas.setAttribute('height', height);
            streaming = true;
        }
    }, false);

    recognizebutton.addEventListener('click', function (ev) {
        console.log("Recognize using FaceID triggered.");
        takepicture();
        recognize();
        ev.preventDefault();
    }, false);


    loginbutton.addEventListener('click', function (ev) {
        const loginForm = document.getElementById('login-form');
        loginForm.style.display = 'block';
        ev.preventDefault();
    }, false);

    submitLoginButton.addEventListener('click', function (ev) {
        loginUsingCredentials();
        ev.preventDefault();
    }, false);
}

function takepicture() {
    if (width && height) {
        canvas.width = width;
        canvas.height = height;
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, width, height);
    } else {
        console.error("Canvas width or height is not set properly.");
    }
}

function recognize() {
    if (canvas) {
        const data = canvas.toDataURL('image/png');
        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/recognize", true);

        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.response);
                    console.log(response);

                    // Access the `faces` array in the response
                    const users = response.faces;

                    if (users && users.length > 1) {
                        displayUserSelection(users);
                    } else if (users && users.length === 1) {
                        authenticateUser(users[0]);
                    } else {
                        results.textContent = "No matches found.";
                        results.style.color = "orange";
                    }
                } else {
                    console.error("Error during recognition:", xhr.responseText);
                }
            }
        };

        xhr.setRequestHeader('Content-Type', 'text/plain');
        xhr.send(data);
    } else {
        console.error("Canvas is not initialized for face recognition.");
    }
}


function displayUserSelection(users) {
    results.innerHTML = "<h3>Select a user:</h3>";
    const list = document.createElement("ul");

    users.forEach(user => {
        const listItem = document.createElement("li");
        listItem.textContent = `${user.name} (${Math.round(user.prob * 100)}%)`;
        listItem.style.cursor = "pointer";
        listItem.style.margin = "10px";
        listItem.style.color = "white";
        listItem.style.padding = "1rem";
        listItem.style.borderRadius = "10px";
        listItem.style.backgroundColor = "black";
        listItem.addEventListener("click", () => {
            authenticateUser(user);
        });
        list.appendChild(listItem);
    });

    results.appendChild(list);
}

function authenticateUser(user) {
    if (user.logintoken) {
        console.log(`Authenticating as ${user.name} with token:`, user.logintoken);
        results.textContent = `Authenticated as ${user.name}`;
        results.style.color = "green";
        const token = user.logintoken; // Retrieve the token from sessionStorage

                if (token) {
                    const redirectURL = `logged.html?token=${encodeURIComponent(token)}`; // Append token as query parameter
                    console.log(`Redirecting to: ${redirectURL}`);
                    window.location.href = redirectURL; // Redirect to logged.html
                } else {
                    console.error("No token found. Cannot redirect.");
                    alert("Authentication token is missing. Please log in.");
                }
    } else {
        results.textContent = `User ${user.name} does not have a valid token.`;
        results.style.color = "red";
    }
}

function loginUsingCredentials() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    if (!username || !password) {
        results.textContent = "Please fill in both fields.";
        results.style.color = "orange";
        return;
    }

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/login", true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.response);
                console.log("Login successful:", response);
                results.textContent = "Login successful!";
                results.style.color = "green";

                const token = response.logintoken; // Retrieve the token from sessionStorage

                if (token) {
                    const redirectURL = `logged.html?token=${encodeURIComponent(token)}`; // Append token as query parameter
                    console.log(`Redirecting to: ${redirectURL}`);
                    window.location.href = redirectURL; // Redirect to logged.html
                } else {
                    console.error("No token found. Cannot redirect.");
                    alert("Authentication token is missing. Please log in.");
                }
            } else {
                console.error("Login failed:", xhr.responseText);
                results.textContent = "Login failed. Please try again.";
                results.style.color = "red";
            }
        }
    };

    xhr.send(JSON.stringify({ username, password }));
}





