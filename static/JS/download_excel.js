function downloadExcel() {
    const headers = [
        '#',
        'Product Type',
        'Product Name',
        'Serial No',
        'Make',
        'Warranty',
        'Extended Warranty',
        'Insurance',
        'AMC',
        
    ];

    // Detect if search is active
    const searchValue = document.getElementById('searchInput').value.trim().toLowerCase();

    // Get all table rows
    const allTableRows = Array.from(document.querySelectorAll('table tbody tr'));

    // If search is active, filter to visible rows
    const rowsToExport = searchValue
        ? allTableRows.filter(row => row.offsetParent !== null) // only visible ones
        : allTableRows; // all rows (all pages should already be in DOM if pagination is client-side)

    const data = rowsToExport.map((row, index) => {
        const cells = row.cells;
        return [
            index + 1,
            cells[1].textContent.trim(),
            cells[2].textContent.trim(),
            cells[3].textContent.trim(),
            cells[4].textContent.trim(),
            cells[5].querySelector('.status-container').children[0].textContent.includes('✅') ? 'Yes' : 'No',
            cells[5].querySelector('.status-container').children[1].textContent.includes('✅') ? 'Yes' : 'No',
            cells[5].querySelector('.status-container').children[2].textContent.includes('✅') ? 'Yes' : 'No',
            cells[5].querySelector('.status-container').children[3].textContent.includes('✅') ? 'Yes' : 'No',
           
        ];
    });

    const worksheet = XLSX.utils.json_to_sheet([headers, ...data], { skipHeader: true });
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Assets');
    XLSX.writeFile(workbook, 'Assets_Export.xlsx');
}
