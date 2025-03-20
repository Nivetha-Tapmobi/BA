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
    if (form) {
        form.addEventListener("submit", function(event) {
            event.preventDefault();

            // Save form data to localStorage (optional)
            const formData = {};
            document.querySelectorAll("input, textarea").forEach(field => {
                if (field.name) {
                    formData[field.name] = field.value;
                }
            });
            localStorage.setItem("vendorFormState", JSON.stringify(formData));

            // Submit form via fetch with session cookies
            fetch(form.action, {
                method: form.method,
                body: new FormData(form),
                credentials: 'include'  // Include session cookies
            })
            .then(response => {
                if (response.redirected) {
                    // Follow Flask's redirect
                    window.location.href = response.url;
                } else if (response.ok) {
                    // If no redirect but success, manually go to create_asset
                    window.location.href = '/create_asset';
                } else {
                    return response.text().then(text => {
                        throw new Error(`Form submission failed: ${text}`);
                    });
                }
            })
            .catch(error => {
                console.error("Error submitting form:", error);
            });
        });
    }
});