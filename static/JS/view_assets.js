$(document).ready(function () {
    // Initialize DataTable
    $("#assetTable").DataTable();

    // Barcode Generation
    $(".barcode").each(function () {
        let barcodeId = $(this).attr("id");
        let barcodeValue = barcodeId.replace("barcode-", "");
        JsBarcode("#" + barcodeId, barcodeValue, {
            format: "CODE128",
            width: 1.8,
            height: 40
        });
    });
});

// Function to download barcode
function downloadBarcode(barcodeId) {
    const svg = document.getElementById(barcodeId);
    if (!svg) return;

    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const svgData = new XMLSerializer().serializeToString(svg);
    const img = new Image();

    img.onload = function () {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        const a = document.createElement("a");
        a.href = canvas.toDataURL("image/png");
        a.download = barcodeId + ".png";
        a.click();
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
}

// Function to toggle action menu
function toggleActions(assetId) {
    let menu = document.getElementById("actions-" + assetId);
    if (menu) {
        menu.style.display = (menu.style.display === "none" || menu.style.display === "") ? "block" : "none";
    }
}

// Function to view asset details
function viewDetails(assetJson) {
    let modalBody = document.getElementById("modal-body");
    if (!modalBody) return;

    modalBody.innerHTML = Object.keys(assetJson).map(key => 
        `<p><b>${key}:</b> ${assetJson[key]}</p>`
    ).join("");

    document.getElementById("assetModal").style.display = "block";
}

// Function to close modal
function closeModal() {
    document.getElementById("assetModal").style.display = "none";
}





function addUser(assetId) {
	// Add your edit logic here, e.g., redirect to edit page
	//window.location.href = `/create_user_asset/${assetId}`;
	window.location.href = `/view_user_details/${assetId}`;
}



// Function to manage insurance
function manageInsurance(assetId) {
    alert("Manage insurance for: " + assetId);
}

// Function to manage extended warranty
function manageExtendedWarranty(assetId) {
    alert("Manage extended warranty for: " + assetId);
}

