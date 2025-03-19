function printModal() {
    const modalContent = document.querySelector('.modal-content');
    if (!modalContent) return;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
        <head>
            <title>Print Asset Details</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    padding: 20px;
                }
                h2 {
                    color: #2f276f;
                    border-bottom: 2px solid #2f276f;
                    padding-bottom: 10px;
                }
                .two-column-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    padding: 10px 0;
                }
                .detail-item {
                    margin: 8px 0;
                    padding: 8px;
                    background-color: #f8f9fa;
                }
                .detail-item strong {
                    color: #2f276f;
                    display: block;
                    margin-bottom: 4px;
                }
                .detail-item span {
                    color: #333;
                    word-break: break-word;
                }
                .no-print {
                    display: none;
                }
            </style>
        </head>
        <body>
            ${modalContent.innerHTML}
        </body>
        </html>
    `);

    // Remove the close button and print button from the print view
    printWindow.document.querySelector('.close').classList.add('no-print');
    printWindow.document.querySelector('.print-btn').classList.add('no-print');

    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
    printWindow.close();
}