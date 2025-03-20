document.addEventListener("DOMContentLoaded", function () {
    // Toggle Warranty Fields
    window.toggleWarrantyFields = function() {
        let warrantyFields = document.getElementById('warranty_fields');
        warrantyFields.style.display = (document.getElementById('warranty_exists').value === 'Yes') ? 'block' : 'none';
    };

    // Toggle Extended Warranty Fields
    window.toggleExtendedWarrantyFields = function() {
        let extendedWarrantyFields = document.getElementById('extended_warranty_fields');
        extendedWarrantyFields.style.display = (document.getElementById('extended_warranty_exists').value === 'Yes') ? 'block' : 'none';
    };

    // Generic function to calculate end date based on start date and period
    function calculateEndDate(startId, endId, yearsId, monthsId, daysId) {
        let startDate = new Date(document.getElementById(startId).value);
        let years = parseInt(document.getElementById(yearsId).value) || 0;
        let months = parseInt(document.getElementById(monthsId).value) || 0;
        let days = parseInt(document.getElementById(daysId).value) || 0;

        if (!isNaN(startDate.getTime())) {
            startDate.setFullYear(startDate.getFullYear() + years);
            startDate.setMonth(startDate.getMonth() + months);
            startDate.setDate(startDate.getDate() + days);
            document.getElementById(endId).value = startDate.toISOString().split('T')[0];
        }
    }

    // Calculate Warranty End Date
    function calculateWarrantyEndDate() {
        calculateEndDate('warranty_start', 'warranty_end', 'warranty_period_years', 'warranty_period_months', 'warranty_period_days');
        // Trigger extended warranty calculation if extended warranty exists
        if (document.getElementById('extended_warranty_exists').value === 'Yes') {
            calculateExtendedWarrantyEndDate();
        }
    }

    // Calculate Extended Warranty End Date
    function calculateExtendedWarrantyEndDate() {
        let warrantyEndDate = new Date(document.getElementById('warranty_end').value);
        let years = parseInt(document.getElementById('extended_warranty_period_years').value) || 0;
        let months = parseInt(document.getElementById('extended_warranty_period_months').value) || 0;
        let days = parseInt(document.getElementById('extended_warranty_period_days').value) || 0;

        if (!isNaN(warrantyEndDate.getTime())) {
            warrantyEndDate.setFullYear(warrantyEndDate.getFullYear() + years);
            warrantyEndDate.setMonth(warrantyEndDate.getMonth() + months);
            warrantyEndDate.setDate(warrantyEndDate.getDate() + days);
            document.getElementById('extended_warranty_end').value = warrantyEndDate.toISOString().split('T')[0];
        }
    }

    // Product Age Calculation
    document.getElementById('purchase_date')?.addEventListener('change', function () {
        let purchaseDate = new Date(this.value);
        let today = new Date();
        if (purchaseDate > today) {
            alert('Purchase date cannot be in the future.');
            this.value = '';
        } else {
            let diff = today - purchaseDate;
            let days = Math.floor(diff / (1000 * 60 * 60 * 24));
            document.getElementById('product_age').value = `${days} days`;
        }
    });

    // Warranty Start Date Validation
    document.getElementById('warranty_start')?.addEventListener('change', function () {
        let purchaseDate = new Date(document.getElementById('purchase_date').value);
        let warrantyStartDate = new Date(this.value);
        if (warrantyStartDate < purchaseDate) {
            alert('Warranty start date cannot be before purchase date.');
            this.value = '';
        } else {
            calculateWarrantyEndDate();
        }
    });

    // Event listeners for warranty period inputs
    document.querySelectorAll('#warranty_period_years, #warranty_period_months, #warranty_period_days').forEach(input => {
        input.addEventListener('input', calculateWarrantyEndDate);
    });

    // Event listeners for extended warranty period inputs
    document.querySelectorAll('#extended_warranty_period_years, #extended_warranty_period_months, #extended_warranty_period_days').forEach(input => {
        input.addEventListener('input', calculateExtendedWarrantyEndDate);
    });

    // Add event listener for warranty_end changes
    document.getElementById('warranty_end')?.addEventListener('change', function () {
        if (document.getElementById('extended_warranty_exists').value === 'Yes') {
            calculateExtendedWarrantyEndDate();
        }
    });

    // AMC Fields Toggle
    const amcSelect = document.getElementById("has_amc");
    const amcSection = document.getElementById("recurring-alert-section");
    const container = document.getElementById("recurring-alert-container");

    window.toggleAMCFields = function () {
        amcSection.style.display = amcSelect.value === "Yes" ? "block" : "none";
    };

    container?.addEventListener("click", function (event) {
        if (event.target.classList.contains("add-field")) {
            const newRow = document.createElement("div");
            newRow.classList.add("recurring-alert-row");
            newRow.innerHTML = `
                <input type="text" name="recurring_alert_key[]" placeholder="Event Type">
                <input type="number" name="recurring_alert_value[]" placeholder="Every X" min="1">
                <select name="recurring_alert_unit[]">
                    <option value="Days">Days</option>
                    <option value="Weeks">Weeks</option>
                    <option value="Months">Months</option>
                    <option value="Years">Years</option>
                </select>
                <button type="button" class="remove-field">-</button>
            `;
            container.appendChild(newRow);
        } else if (event.target.classList.contains("remove-field")) {
            event.target.parentElement.remove();
        }
    });

    // Dropdown with Add New Option
    window.handleSelection = function(select) {  
        if (select.value === "add_new") {
            document.getElementById("modal").style.display = "block";
            document.getElementById("new_option_input").dataset.targetSelect = select.id;
        }
    };

    document.querySelectorAll(".dropdown-with-add").forEach(select => {
        select.addEventListener("change", function () {
            handleSelection(this);
        });
    });

    document.getElementById("add_option_btn").addEventListener("click", function () {
        let newOption = document.getElementById("new_option_input").value;
        let targetSelectId = document.getElementById("new_option_input").dataset.targetSelect;
        let targetSelect = document.getElementById(targetSelectId);

        if (newOption.trim() === "" || !targetSelect) {
            alert("Please enter a valid option.");
            return;
        }

        fetch('/add_new_option', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: targetSelectId, newValue: newOption })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                let newOptionElement = document.createElement("option");
                newOptionElement.value = newOption;
                newOptionElement.text = newOption;
                targetSelect.insertBefore(newOptionElement, targetSelect.lastElementChild);
                targetSelect.value = newOption;
                document.getElementById("modal").style.display = "none";
                document.getElementById("new_option_input").value = "";
                alert(data.message);
            } else {
                alert("Error: " + data.error);
            }
        })
        .catch(error => console.error('Error:', error));
    });

    window.onclick = function(event) {
        let modal = document.getElementById("modal");
        if (event.target === modal) {
            modal.style.display = "none";
        }
    };

    document.getElementById("close_modal").addEventListener("click", function () {
        document.getElementById("modal").style.display = "none";
    });
	
	
	
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
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
});