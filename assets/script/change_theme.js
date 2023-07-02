// Change background color theme
function switchTheme() {
    var pageBody = document.querySelector("body");
    var themeBtn = document.getElementById("color-theme");


    if (pageBody.style.backgroundColor === "rgb(84, 138, 144)") {
        pageBody.style.backgroundColor = "#122527";
        themeBtn.innerHTML = '<i class="fa-solid fa-moon" style="color: #f0e894;"></i>';
    } else {
        pageBody.style.backgroundColor = "#548a90";
        themeBtn.innerHTML = '<i class="fa-solid fa-sun" style="color: #f0e894;"></i>';
    }
}