// Function to handle search input
function handleSearch() {
    const searchInput = document.getElementById('search-input');
    const searchQuery = searchInput.value.trim();
    const urlParams = new URLSearchParams(window.location.search);

    // Update the search query in the URL
    if (searchQuery) {
        urlParams.set('search', searchQuery);
    } else {
        urlParams.delete('search');
    }

    // Reset to page 1 when searching
    urlParams.set('page', '1');

    // Update the URL without reloading the page
    window.location.search = urlParams.toString();
}

// Function to initialize search functionality
function initSearch() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        // Trigger search on Enter key
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                handleSearch();
            }
        });

        // Trigger search on button click
        const searchButton = document.getElementById('search-button');
        if (searchButton) {
            searchButton.addEventListener('click', handleSearch);
        }
    }
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', initSearch);