document.addEventListener("DOMContentLoaded", function () {
    // Initialize Select2 for searchable dropdowns
    $('.searchable-dropdown').select2({
        width: '100%',
        placeholder: 'Select an option',
        allowClear: true
    });

    // Vendor Dropdown Handling
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

        // Handle vendor dropdown change with Select2
        $(vendorDropdown).on('select2:select', function (e) {
            const selectedValue = e.params.data.id;
            if (selectedValue === 'add_new_vendor') {
                console.log('Redirecting to /save_form_state for new vendor');
                form.action = '/save_form_state';
                form.submit();
            } else {
                const selectedOption = vendorDropdown.options[vendorDropdown.selectedIndex];
                const vendorId = selectedOption.getAttribute('data-vendor-id');
                console.log('Selected Vendor ID:', vendorId);
                vendorIdInput.value = vendorId || '';
                vendorIdDisplay.textContent = vendorId || 'None';
            }
        });
    } else {
        console.error('Vendor dropdown elements not found');
    }

    // Modal for adding new options (for other dropdowns, not vendor)
    const modal = document.getElementById('modal');
    const newOptionInput = document.getElementById('new_option_input');
    const addOptionBtn = document.getElementById('add_option_btn');
    const closeModalBtn = document.getElementById('close_modal');

    if (modal && newOptionInput && addOptionBtn && closeModalBtn) {
        $('.dropdown-with-add').not('#vendor_name').on('select2:select', function (e) {
            const selectedValue = e.params.data.id;
            const selectId = $(this).attr('id');
            if (selectedValue === 'add_new') {
                modal.style.display = 'block';
                newOptionInput.dataset.targetSelect = selectId;
                $(this).val(null).trigger('change');
            }
        });

        addOptionBtn.addEventListener('click', function () {
            const newOption = newOptionInput.value.trim();
            const targetSelectId = newOptionInput.dataset.targetSelect;
            const targetSelect = document.getElementById(targetSelectId);

            if (newOption === '' || !targetSelect) {
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
                    const newOptionElement = new Option(newOption, newOption, false, true);
                    $(targetSelect).append(newOptionElement).trigger('change');
                    modal.style.display = 'none';
                    newOptionInput.value = '';
                    alert(data.message);
                } else {
                    alert('Error: ' + (data.error || 'Failed to add option'));
                }
            })
            .catch(error => {
                console.error('Error adding option:', error);
                alert('Failed to add option due to a network error.');
            });
        });

        closeModalBtn.addEventListener('click', function () {
            modal.style.display = 'none';
            newOptionInput.value = '';
        });

        window.addEventListener('click', function (event) {
            if (event.target === modal) {
                modal.style.display = 'none';
                newOptionInput.value = '';
            }
        });
    } else {
        console.error('Modal elements not found');
    }

    // Warranty Fields Toggle
    window.toggleWarrantyFields = function () {
        const warrantyFields = document.getElementById('warranty_fields');
        warrantyFields.style.display = document.getElementById('warranty_exists').value === 'Yes' ? 'block' : 'none';
    };

    // Extended Warranty Fields Toggle
    window.toggleExtendedWarrantyFields = function () {
        const extendedWarrantyFields = document.getElementById('extended_warranty_fields');
        extendedWarrantyFields.style.display = document.getElementById('extended_warranty_exists').value === 'Yes' ? 'block' : 'none';
    };

    // Generic function to calculate end date
    function calculateEndDate(startId, endId, yearsId, monthsId, daysId) {
        const startDate = new Date(document.getElementById(startId).value);
        const years = parseInt(document.getElementById(yearsId).value) || 0;
        const months = parseInt(document.getElementById(monthsId).value) || 0;
        const days = parseInt(document.getElementById(daysId).value) || 0;

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
        if (document.getElementById('extended_warranty_exists').value === 'Yes') {
            calculateExtendedWarrantyEndDate();
        }
    }

    // Calculate Extended Warranty End Date
    function calculateExtendedWarrantyEndDate() {
        const warrantyEndDate = new Date(document.getElementById('warranty_end').value);
        const years = parseInt(document.getElementById('extended_warranty_period_years').value) || 0;
        const months = parseInt(document.getElementById('extended_warranty_period_months').value) || 0;
        const days = parseInt(document.getElementById('extended_warranty_period_days').value) || 0;

        if (!isNaN(warrantyEndDate.getTime())) {
            warrantyEndDate.setFullYear(warrantyEndDate.getFullYear() + years);
            warrantyEndDate.setMonth(warrantyEndDate.getMonth() + months);
            warrantyEndDate.setDate(warrantyEndDate.getDate() + days);
            document.getElementById('extended_warranty_end').value = warrantyEndDate.toISOString().split('T')[0];
        }
    }

    // Product Age Calculation
    document.getElementById('purchase_date')?.addEventListener('change', function () {
        const purchaseDate = new Date(this.value);
        const today = new Date();
        if (purchaseDate > today) {
            alert('Purchase date cannot be in the future.');
            this.value = '';
        } else {
            const diff = today - purchaseDate;
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            document.getElementById('product_age').value = `${days} days`;
        }
    });

    // Warranty Start Date Validation
    document.getElementById('warranty_start')?.addEventListener('change', function () {
        const purchaseDate = new Date(document.getElementById('purchase_date').value);
        const warrantyStartDate = new Date(this.value);
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
        if (document.getElementById('extended_warranty_exists').value === 'Ys') {
            calculateExtendedWarrantyEndDate();
        }
    });

    // AMC Fields Toggle
    const amcSelect = document.getElementById('has_amc');
    const amcSection = document.getElementById('recurring-alert-section');
    const container = document.getElementById('recurring-alert-container');

    window.toggleAMCFields = function () {
        amcSection.style.display = amcSelect.value === 'Yes' ? 'block' : 'none';
    };

    container?.addEventListener('click', function (event) {
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
            event.target.parentElement.remove();
        }
    });
});