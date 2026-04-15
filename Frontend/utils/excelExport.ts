
export const exportToExcel = async (data: any[], fileName: string, sheetName: string = 'Sheet1') => {
  if (!data || data.length === 0) {
    alert('No data to export');
    return;
  }

  try {
    const XLSX = await import('xlsx');
    const worksheet = XLSX.utils.json_to_sheet(data);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
    XLSX.writeFile(workbook, fileName.endsWith('.xlsx') ? fileName : `${fileName}.xlsx`);
  } catch (error) {
    console.error("Export failed:", error);
    alert("Failed to export. Please try again.");
  }
};
