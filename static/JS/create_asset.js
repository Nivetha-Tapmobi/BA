document.addEventListener("DOMContentLoaded", function () {
    // Toggle warranty fields
    function toggleWarrantyFields() {
        const warrantyExists = document.getElementById('warranty_exists');
        const warrantyFields = document.getElementById('warranty_fields');
        if (warrantyExists && warrantyFields) {
            warrantyFields.style.display = warrantyExists.value === 'Yes' ? 'block' : 'none';
        }
    }

    // Toggle extended warranty fields
    function toggleExtendedWarrantyFields() {
        const extendedWarrantyExists = document.getElementById('extended_warranty_exists');
        const extendedWarrantyFields = document.getElementById('extended_warranty_fields');
        if (extendedWarrantyExists && extendedWarrantyFields) {
            extendedWarrantyFields.style.display = extendedWarrantyExists.value === 'Yes' ? 'block' : 'none';
        }
    }

    // Toggle AMC fields
    function toggleAMCFields() {
        const hasAmc = document.getElementById('has_amc');
        const recurringAlertSection = document.getElementById('recurring-alert-section');
        if (hasAmc && recurringAlertSection) {
            recurringAlertSection.style.display = hasAmc.value === 'Yes' ? 'block' : 'none';
        }
    }

    // Vendor dropdown logic
const vendorDropdown = document.getElementById('vendor_name');
    const vendorIdInput = document.getElementById('vendor_id');
    const vendorIdDisplay = document.getElementById('vendor_id_display');
    const form = document.getElementById('assetForm');

    if (vendorDropdown && vendorIdInput && vendorIdDisplay && form) {
        // Set initial vendor_id
        const selectedOption = vendorDropdown.options[vendorDropdown.selectedIndex];
        if (selectedOption && selectedOption.value && selectedOption.value !== 'add_new_vendor') {
            const vendorId = selectedOption.getAttribute('data-vendor-id');
            vendorIdInput.value = vendorId || '';
            vendorIdDisplay.textContent = vendorId || 'None';
        }

        vendorDropdown.addEventListener('change', function (event) {
            event.preventDefault();
            if (this.value === 'add_new_vendor') {
                console.log('Redirecting to /save_form_state');
                form.action = '/save_form_state';  // Unified action for both pages
                form.submit();
            } else {
                const selectedOption = this.options[this.selectedIndex];
                const vendorId = selectedOption.getAttribute('data-vendor-id');
                console.log('Selected Vendor ID:', vendorId);
                vendorIdInput.value = vendorId || '';
                vendorIdDisplay.textContent = vendorId || 'None';
            }
        });
    } else {
        console.error('Vendor dropdown elements not found');
    }
    // Initialize toggle states on load
    toggleWarrantyFields();
    toggleExtendedWarrantyFields();
    toggleAMCFields();

    // Add event listeners for toggles
    const warrantyExists = document.getElementById('warranty_exists');
    const extendedWarrantyExists = document.getElementById('extended_warranty_exists');
    const hasAmc = document.getElementById('has_amc');

    if (warrantyExists) warrantyExists.addEventListener('change', toggleWarrantyFields);
    if (extendedWarrantyExists) extendedWarrantyExists.addEventListener('change', toggleExtendedWarrantyFields);
    if (hasAmc) hasAmc.addEventListener('change', toggleAMCFields);
});