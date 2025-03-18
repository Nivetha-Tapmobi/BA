document.addEventListener("DOMContentLoaded", function() {
    // Auto-hide flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(message => {
                message.style.display = 'none';
            });
        }, 3000);
    }

    // Return to previous page button
    const previousPage = localStorage.getItem('previousPage') || '/create_asset'; // Fallback to create_asset
    document.getElementById('return-to-previous').onclick = function() {
        window.location.href = previousPage;
    };

    // Toggle menu visibility
    function headertoggleMenu() {
        const menu = document.getElementById('menuDropdown');
        menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
    }

    // Close dropdown menu when clicking outside
    document.addEventListener('click', function(event) {
        const dropdown = document.getElementById('menuDropdown');
        const menuButton = document.querySelector('.menu');
        if (!dropdown.contains(event.target) && !menuButton.contains(event.target)) {
            dropdown.style.display = 'none';
        }
    });

    // Handle form submission
    const form = document.querySelector("form");
    form.addEventListener("submit", function(event) {
        // Prevent default submission briefly to handle redirection
        event.preventDefault();

        // Save form data (optional, if you want to persist vendor form state too)
        const formData = {};
        document.querySelectorAll("input, textarea").forEach(field => {
            if (field.name) {
                formData[field.name] = field.value;
            }
        });
        localStorage.setItem("vendorFormState", JSON.stringify(formData)); // Optional

        // Submit the form programmatically
        fetch(form.action, {
            method: form.method,
            body: new FormData(form),
        })
        .then(response => {
            if (response.ok) {
                // Redirect back to create_asset after successful submission
                window.location.href = '/create_asset';
            } else {
                console.error("Form submission failed");
            }
        })
        .catch(error => {
            console.error("Error submitting form:", error);
        });
    });
});