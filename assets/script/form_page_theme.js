function switchTheme() {
    var formContainer = document.querySelector(".form-container");
    var pageName = document.getElementById("page-name");
    var inputBox = document.querySelectorAll(".input-box input");
    var inputIcon = document.querySelectorAll(".pass-hide");
    var registerLogin = document.querySelector(".signup-login");
    var buttons = document.querySelectorAll(".login-btn, .register-btn, .reset-password-btn");
    var themeBtn = document.getElementById("color-theme");
    var guide = document.querySelector(".reset-guide");

    var currentColor = formContainer.style.backgroundColor;

    if (currentColor === "" || currentColor === "rgb(255, 255, 255)") {
        formContainer.style.backgroundColor = "#122527";
        pageName.style.color = "#fff";
        registerLogin.style.color = "#707070";
        themeBtn.innerHTML = '<i class="fa-solid fa-sun" style="color: #f0e894;"></i>';
        inputBox.forEach(function(i) {
            i.style.backgroundColor = "#122527";
            i.style.color = "#fff";
        });
        inputIcon.forEach(function(i) {
            i.style.color = "#59878B";
        });
        buttons.forEach(function(i) {
            i.style.boxShadow = "0 0 0 2px #fff";
            i.style.color = "#fff";
        });
        guide.style.color = "#b5b5b5";
    } else {
        formContainer.style.backgroundColor = "rgb(255, 255, 255)";
        pageName.style.color = "#122527";
        registerLogin.style.color = "#122527";
        themeBtn.innerHTML = '<i class="fa-solid fa-moon" style="color: #f0e894;"></i>';
        inputBox.forEach(function(i) {
            i.style.backgroundColor = "#fff";
            i.style.color = "#333";
        });
        inputIcon.forEach(function(i) {
            i.style.color = "#122527";
        });
        buttons.forEach(function(i) {
            i.style.boxShadow = "0 0 0 2px #122527";
            i.style.color = "#122527";
        });
        guide.style.color = "#333";
    }
}