document.addEventListener("DOMContentLoaded", function () {
    // Toggle Warranty Fields
    window.toggleWarrantyFields = function () {
        const warrantyExists = document.getElementById('warranty_exists');
        const warrantyFields = document.getElementById('warranty_fields');
        if (warrantyExists && warrantyFields) {
            warrantyFields.style.display = warrantyExists.value === 'Yes' ? 'block' : 'none';
        }
    };

    // Toggle Extended Warranty Fields
    window.toggleExtendedWarrantyFields = function () {
        const extendedWarrantyExists = document.getElementById('extended_warranty_exists');
        const extendedWarrantyFields = document.getElementById('extended_warranty_fields');
        if (extendedWarrantyExists && extendedWarrantyFields) {
            extendedWarrantyFields.style.display = extendedWarrantyExists.value === 'Yes' ? 'block' : 'none';
        }
    };

    // Generic function to calculate end date based on start date and period
    function calculateEndDate(startId, endId, yearsId, monthsId, daysId) {
        const startInput = document.getElementById(startId);
        const endInput = document.getElementById(endId);
        if (!startInput || !endInput) return;

        const startDate = new Date(startInput.value);
        const years = parseInt(document.getElementById(yearsId)?.value || 0);
        const months = parseInt(document.getElementById(monthsId)?.value || 0);
        const days = parseInt(document.getElementById(daysId)?.value || 0);

        if (!isNaN(startDate.getTime())) {
            startDate.setFullYear(startDate.getFullYear() + years);
            startDate.setMonth(startDate.getMonth() + months);
            startDate.setDate(startDate.getDate() + days);
            endInput.value = startDate.toISOString().split('T')[0];
        }
    }

    // Calculate Warranty End Date
    function calculateWarrantyEndDate() {
        calculateEndDate('warranty_start', 'warranty_end', 'warranty_period_years', 'warranty_period_months', 'warranty_period_days');
        if (document.getElementById('extended_warranty_exists')?.value === 'Yes') {
            calculateExtendedWarrantyEndDate();
        }
    }

    // Calculate Extended Warranty End Date
    function calculateExtendedWarrantyEndDate() {
        const warrantyEndInput = document.getElementById('warranty_end');
        const extendedEndInput = document.getElementById('extended_warranty_end');
        if (!warrantyEndInput || !extendedEndInput) return;

        const warrantyEndDate = new Date(warrantyEndInput.value);
        const years = parseInt(document.getElementById('extended_warranty_period_years')?.value || 0);
        const months = parseInt(document.getElementById('extended_warranty_period_months')?.value || 0);
        const days = parseInt(document.getElementById('extended_warranty_period_days')?.value || 0);

        if (!isNaN(warrantyEndDate.getTime())) {
            warrantyEndDate.setFullYear(warrantyEndDate.getFullYear() + years);
            warrantyEndDate.setMonth(warrantyEndDate.getMonth() + months);
            warrantyEndDate.setDate(warrantyEndDate.getDate() + days);
            extendedEndInput.value = warrantyEndDate.toISOString().split('T')[0];
        }
    }

    // Product Age Calculation
    const purchaseDateInput = document.getElementById('purchase_date');
    if (purchaseDateInput) {
        purchaseDateInput.addEventListener('change', function () {
            const purchaseDate = new Date(this.value);
            const today = new Date();
            if (purchaseDate > today) {
                alert('Purchase date cannot be in the future.');
                this.value = '';
            } else {
                const diff = today - purchaseDate;
                const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                const productAgeInput = document.getElementById('product_age');
                if (productAgeInput) {
                    productAgeInput.value = `${days} days`;
                }
            }
        });
    }

    // Warranty Start Date Validation
    const warrantyStartInput = document.getElementById('warranty_start');
    if (warrantyStartInput) {
        warrantyStartInput.addEventListener('change', function () {
            const purchaseDate = new Date(document.getElementById('purchase_date')?.value);
            const warrantyStartDate = new Date(this.value);
            if (!isNaN(purchaseDate.getTime()) && warrantyStartDate < purchaseDate) {
                alert('Warranty start date cannot be before purchase date.');
                this.value = '';
            } else {
                calculateWarrantyEndDate();
            }
        });
    }

    // Event listeners for warranty period inputs
    ['warranty_period_years', 'warranty_period_months', 'warranty_period_days'].forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('input', calculateWarrantyEndDate);
        }
    });

    // Event listeners for extended warranty period inputs
    ['extended_warranty_period_years', 'extended_warranty_period_months', 'extended_warranty_period_days'].forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('input', calculateExtendedWarrantyEndDate);
        }
    });

    // Add event listener for warranty_end changes
    const warrantyEndInput = document.getElementById('warranty_end');
    if (warrantyEndInput) {
        warrantyEndInput.addEventListener('change', function () {
            if (document.getElementById('extended_warranty_exists')?.value === 'Yes') {
                calculateExtendedWarrantyEndDate();
            }
        });
    }

    // AMC Fields Toggle
    const amcSelect = document.getElementById('has_amc');
    const amcSection = document.getElementById('recurring-alert-section');
    const container = document.getElementById('recurring-alert-container');

    window.toggleAMCFields = function () {
        if (amcSelect && amcSection) {
            amcSection.style.display = amcSelect.value === 'Yes' ? 'block' : 'none';
        }
    };

    if (container) {
        container.addEventListener('click', function (event) {
            if (event.target.classList.contains('add-field')) {
                const newRow = document.createElement('div');
                newRow.classList.add('recurring-alert-row');
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
            } else if (event.target.classList.contains('remove-field')) {
                const rows = container.querySelectorAll('.recurring-alert-row');
                if (rows.length > 1) {
                    event.target.parentElement.remove();
                } else {
                    alert('At least one recurring alert is required.');
                }
            }
        });
    }

    // Dropdown with Add New Option
    window.handleSelection = function (select) {
        if (select.value === 'add_new') {
            const modal = document.getElementById('modal');
            const input = document.getElementById('new_option_input');
            if (modal && input) {
                modal.style.display = 'block';
                input.dataset.targetSelect = select.id;
            }
        }
    };

    document.querySelectorAll('.dropdown-with-add').forEach(select => {
        select.addEventListener('change', function () {
            handleSelection(this);
        });
    });

    const addOptionBtn = document.getElementById('add_option_btn');
    if (addOptionBtn) {
        addOptionBtn.addEventListener('click', function () {
            const input = document.getElementById('new_option_input');
            const targetSelectId = input?.dataset.targetSelect;
            const targetSelect = document.getElementById(targetSelectId);
            const newOption = input?.value.trim();

            if (!newOption || !targetSelect) {
                alert('Please enter a valid option.');
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
                    const newOptionElement = document.createElement('option');
                    newOptionElement.value = newOption;
                    newOptionElement.text = newOption;
                    targetSelect.insertBefore(newOptionElement, targetSelect.lastElementChild);
                    targetSelect.value = newOption;
                    document.getElementById('modal').style.display = 'none';
                    input.value = '';
                    alert(data.message);
                } else {
                    alert('Error: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to add new option. Please try again.');
            });
        });
    }

    const modal = document.getElementById('modal');
    if (modal) {
        window.onclick = function (event) {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        };

        const closeModal = document.getElementById('close_modal');
        if (closeModal) {
            closeModal.addEventListener('click', function () {
                modal.style.display = 'none';
            });
        }
    }

    // Vendor Dropdown Handling
   const vendorDropdown = document.getElementById('vendor_name');
    const vendorIdInput = document.getElementById('vendor_id');
    const vendorIdDisplay = document.getElementById('vendor_id_display');
    const form = document.getElementById('assetForm');

    if (vendorDropdown && vendorIdInput && vendorIdDisplay && form) {
        // Set initial vendor_id based on pre-filled form_state
        const selectedOption = vendorDropdown.options[vendorDropdown.selectedIndex];
        if (selectedOption && selectedOption.value !== 'add_new_vendor' && selectedOption.value !== '') {
            const vendorId = selectedOption.getAttribute('data-vendor-id');
            vendorIdInput.value = vendorId || '';
            vendorIdDisplay.textContent = vendorId || 'None';
        }

        vendorDropdown.addEventListener('change', function (event) {
            event.preventDefault();
            if (this.value === 'add_new_vendor') {
                console.log('Redirecting to /save_form_state');
                form.action = '/save_form_state';
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