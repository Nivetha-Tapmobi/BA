// static/script.js

function headertoggleMenu() {
    const menu = document.getElementById("menuDropdown");
    menu.style.display = menu.style.display === "block" ? "none" : "block";
}

// Close the dropdown if clicked outside
document.addEventListener("click", function (event) {
    const dropdown = document.getElementById("menuDropdown");
    const menuButton = document.querySelector(".menu");

    if (dropdown && !dropdown.contains(event.target) && !menuButton.contains(event.target)) {
        dropdown.style.display = "none";
    }
});
