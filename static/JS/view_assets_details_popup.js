async function viewDetails(assetJson) {
    console.log("viewDetails called with assetJson:", assetJson);
    let modalBody = document.getElementById("modal-body");
    if (!modalBody) {
        console.error("Modal body not found");
        return;
    }

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
        <div id="related-data">
            <p>Loading related data...</p>
        </div>
        <button class="print-btn" onclick="printModal()">Print</button>
    `;
    document.getElementById("assetModal").style.display = "block";

    // Fetch related data with debugging
    const url = `/get_asset_details/${assetJson.asset_id}`;
    console.log("Fetching related data from:", url);

    try {
        const response = await fetch(url);
        console.log("Fetch response status:", response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const relatedData = await response.json();
        console.log("Related data received:", relatedData);

        // Service Details Table
        let serviceRows = '';
        if (relatedData.service_details && relatedData.service_details.length > 0) {
            relatedData.service_details.forEach(service => {
                serviceRows += `
                    <tr>
                        <td>${service.service_id || 'N/A'}</td>
                        <td>${service.service_type || 'N/A'}</td>
                        <td>${service.ticket_id || 'N/A'}</td>
                        <td>${service.work_done || 'N/A'}</td>
                        <td>${formatValue('next_service_date', service.next_service_date)}</td>
                        <td>${service.service_charge || 'N/A'}</td>
                    </tr>
                `;
            });
        } else {
            serviceRows = '<tr><td colspan="6">No service details available</td></tr>';
        }

        // Raised Tickets Table
        let ticketRows = '';
        if (relatedData.raised_tickets && relatedData.raised_tickets.length > 0) {
            relatedData.raised_tickets.forEach(ticket => {
                ticketRows += `
                    <tr>
                        <td>${ticket.ticket_id || 'N/A'}</td>
                        <td>${ticket.problem_description || 'N/A'}</td>
                        <td>${ticket.ticket_status || 'N/A'}</td>
                    </tr>
                `;
            });
        } else {
            ticketRows = '<tr><td colspan="3">No raised tickets available</td></tr>';
        }

        // Extended Warranty Table
        let warrantyRows = '';
        if (relatedData.extended_warranty_info && relatedData.extended_warranty_info.length > 0) {
            relatedData.extended_warranty_info.forEach(warranty => {
                warrantyRows += `
                    <tr>
                        <td>${warranty.warranty_asset_id || 'N/A'}</td>
                        <td>${formatValue('purchase_date', warranty.purchase_date)}</td>
                        <td>${warranty.extended_warranty || 'N/A'}</td>
                        <td>${warranty.value || 'N/A'}</td>
                    </tr>
                `;
            });
        } else {
            warrantyRows = '<tr><td colspan="4">No extended warranty info available</td></tr>';
        }

        // Insurance Details Table
        let insuranceRows = '';
        if (relatedData.insurance_details && relatedData.insurance_details.length > 0) {
            relatedData.insurance_details.forEach(insurance => {
                insuranceRows += `
                    <tr>
                        <td>${insurance.policy_number || 'N/A'}</td>
                        <td>${insurance.insurance_value || 'N/A'}</td>
                        <td>${formatValue('insurance_start', insurance.insurance_start)}</td>
                        <td>${insurance.insurance_period || 'N/A'}</td>
                        <td>${formatValue('insurance_end', insurance.insurance_end)}</td>
                    </tr>
                `;
            });
        } else {
            insuranceRows = '<tr><td colspan="5">No insurance details available</td></tr>';
        }

        document.getElementById('related-data').innerHTML = `
            <h3>Service Details</h3>
            <table class="modal-table asset-table">
                <thead>
                    <tr>
                        <th>Service ID</th>
                        <th>Service Type</th>
                        <th>Ticket ID</th>
                        <th>Work Done</th>
                        <th>Next Service Date</th>
                        <th>Charge</th>
                    </tr>
                </thead>
                <tbody>${serviceRows}</tbody>
            </table>
            <h3>Raised Tickets</h3>
            <table class="modal-table asset-table">
                <thead>
                    <tr>
                        <th>Ticket ID</th>
                        <th>Problem Description</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>${ticketRows}</tbody>
            </table>
            <h3>Extended Warranty Info</h3>
            <table class="modal-table asset-table">
                <thead>
                    <tr>
                        <th>Warranty Asset ID</th>
                        <th>Purchase Date</th>
                        <th>Extended Warranty</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>${warrantyRows}</tbody>
            </table>
            <h3>Insurance Details</h3>
            <table class="modal-table asset-table">
                <thead>
                    <tr>
                        <th>Policy Number</th>
                        <th>Insurance Value</th>
                        <th>Start Date</th>
                        <th>Period</th>
                        <th>End Date</th>
                    </tr>
                </thead>
                <tbody>${insuranceRows}</tbody>
            </table>
        `;
    } catch (error) {
        console.error('Error fetching related data:', error);
        document.getElementById('related-data').innerHTML = '<p>Error loading related data.</p>';
    }
}