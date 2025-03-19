function viewDetails(assetJson) {
    let modalBody = document.getElementById("modal-body");
    if (!modalBody) return;

    const fieldOrder = [
        'id', 'created_by', 'created_at', 'asset_id', 'asset_category', 'product_type', 
        'product_name', 'serial_no', 'make', 'model', 'part_no', 'description', 
        'purchase_date', 'product_age', 'vendor_name', 'vendor_id', 'company_name', 
        'asset_type', 'purchase_value', 'product_condition', 'adp_production', 
        'insurance', 'warranty_checked', 'warranty_exists', 'warranty_start', 
        'warranty_period', 'warranty_end', 'extended_warranty_exists', 
        'extended_warranty_period', 'extended_warranty_end', 'has_amc', 
        'recurring_alert_for_amc', 'image_path', 'purchase_bill_path', 
        'modified_by', 'modified_at', 'remarks'
    ];

    let leftColumn = '';
    let rightColumn = '';
    const midPoint = Math.ceil(fieldOrder.length / 2);
    const leftFields = fieldOrder.slice(0, midPoint);
    const rightFields = fieldOrder.slice(midPoint);

    leftFields.forEach(key => {
        if (key in assetJson) {
            let value = formatValue(key, assetJson[key]);
            if (key === 'created_by' && 'created_at' in assetJson) {
                leftColumn += `
                    <div class="detail-item">
                        <strong>Created By at Created At:</strong>
                        <span>${value} at ${formatValue('created_at', assetJson['created_at'])}</span>
                    </div>
                `;
            } else if (key === 'created_at') {
                // Skip as it's handled with created_by
            } else {
                leftColumn += `
                    <div class="detail-item">
                        <strong>${formatKey(key)}:</strong>
                        <span>${value}</span>
                    </div>
                `;
            }
        }
    });

    rightFields.forEach(key => {
        if (key in assetJson) {
            let value = formatValue(key, assetJson[key]);
            if (key === 'modified_by' && 'modified_at' in assetJson) {
                rightColumn += `
                    <div class="detail-item">
                        <strong>Modified By at Modified At:</strong>
                        <span>${value} at ${formatValue('modified_at', assetJson['modified_at'])}</span>
                    </div>
                `;
            } else if (key === 'modified_at') {
                // Skip as it's handled with modified_by
            } else {
                rightColumn += `
                    <div class="detail-item">
                        <strong>${formatKey(key)}:</strong>
                        <span>${value}</span>
                    </div>
                `;
            }
        }
    });

    modalBody.innerHTML = `
        <div class="two-column-grid">
            <div>${leftColumn}</div>
            <div>${rightColumn}</div>
        </div>
        <button class="print-btn" onclick="printModal()">Print</button>
    `;

    document.getElementById("assetModal").style.display = "block";
}

function formatKey(key) {
    return key.replace(/_/g, ' ').split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function formatValue(key, value) {
    if (value === null || value === undefined) {
        return 'N/A';
    }
    if (key.includes('_date') || key.includes('_at') || key.includes('_end')) {
        return new Date(value).toLocaleDateString() || value;
    }
    return value;
}

function closeModal() {
    document.getElementById("assetModal").style.display = "none";
}

window.onclick = function(event) {
    let modal = document.getElementById("assetModal");
    if (event.target == modal) {
        modal.style.display = "none";
    }
}