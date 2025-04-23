document.addEventListener("DOMContentLoaded", function () {
    const menuButton = document.querySelector(".menu");
    const dropdown = document.getElementById("menuDropdown");

    if (menuButton && dropdown) {
        menuButton.addEventListener("click", function () {
            dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
        });

        document.addEventListener("click", function (event) {
            if (!dropdown.contains(event.target) && !menuButton.contains(event.target)) {
                dropdown.style.display = "none";
            }
        });
    } else {
        console.error("Menu button or dropdown not found!");
    }
});