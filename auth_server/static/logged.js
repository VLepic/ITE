
document.addEventListener("DOMContentLoaded", function () {
    const params = new URLSearchParams(window.location.search);
    var token = params.get("token");
    var firstname = "Firstname";
    var lastname = "Lastname";
    var username = "username";
    var userid = 999;
    var token_created_at = "";
    var token_expires_at = "";
    var last_logged_in_at = "";

    console.log(token);

    if (token) {
        console.log("if(token): true");
        console.log(`Token received: ${token}`);

    } else {
        console.log("if(token): false");
        console.error("No token found in URL.");
        document.getElementById("tokentext").textContent = "No token found.";
        window.location.href = "index.html";
    }

    function update_text() {
    console.log(`Logged in user: ${username} ( #${userid} )`);

    // Parse the UTC datetime string
    const utcDate = new Date(last_logged_in_at);

    // Automatically get the timezone offset in minutes and convert to milliseconds
    const timezoneOffsetMs = utcDate.getTimezoneOffset() * 60 * 1000;

    // Adjust the UTC time to the local timezone
    const localDate = new Date(utcDate.getTime() - timezoneOffsetMs);

    // Format the adjusted date
    const options = {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false, // Use 24-hour format
        timeZoneName: "short" // Include timezone abbreviation
    };
    const formattedDate = localDate.toLocaleString(undefined, options);

    // Update the UI
    document.getElementById("username").textContent = `Logged in as: ${username} ( #${userid} )`;
    document.getElementById("last_login_time").textContent = `Last logged in at: ${formattedDate}`;
}




    function get_user_info(){
    fetch("/user_info", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: new URLSearchParams({ token })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("User info retrieved:", data);
                userid = data.userid;
                username = data.username;
                firstname = data.first_name;
                lastname = data.last_name;
                token_created_at = data.token_created_at;
                token_expires_at = data.token_expires_at;
                last_logged_in_at = data.last_logged_in_at;
                update_text();

            } else {
                console.error("Error retrieving user info:", data.error);
            }
        })
        .catch(error => {
            console.error("Fetch error:", error);
            //window.location.href = "index.html";
        });
    }

    get_user_info();
    if (token) {
        const iframe = document.getElementById("embedded-site");
        iframe.src = `https://ite.vaclavlepic.com?token=${token}`;
    } else {
        console.error("No token found in URL.");
    }


    const changePasswordForm = document.getElementById("change-password-form");
    const changePasswordStatus = document.getElementById("change-password-status");

    changePasswordForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const oldPassword = document.getElementById("old-password").value;
        const newPassword = document.getElementById("new-password").value;

        try {
            const response = await fetch("/change_password", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: new URLSearchParams({ token, old_password: oldPassword, new_password: newPassword }),
            });

            const data = await response.json();

            if (data.success) {
                changePasswordStatus.style.color = "green";
                changePasswordStatus.textContent = "Password changed successfully!";
            } else {
                changePasswordStatus.style.color = "red";
                changePasswordStatus.textContent = `Error: ${data.error}`;
            }
        } catch (error) {
            console.error("Error changing password:", error);
            changePasswordStatus.style.color = "red";
            changePasswordStatus.textContent = "An error occurred. Please try again.";
        }
    });





});

