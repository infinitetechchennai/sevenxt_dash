export interface ExcelSheet {
  data: any[];
  sheetName: string;
}

export const exportToExcel = async (data: any[] | ExcelSheet[], fileName: string, sheetName: string = 'Sheet1') => {
  if (!data || (Array.isArray(data) && data.length === 0)) {
    // Basic check for empty array or null
    return;
  }

  try {
    const XLSX = await import('xlsx');
    const workbook = XLSX.utils.book_new();

    // Check if it's the multi-sheet format
    if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object' && 'sheetName' in data[0] && 'data' in data[0]) {
      (data as ExcelSheet[]).forEach(sheet => {
        if (sheet.data && sheet.data.length > 0) {
          const worksheet = XLSX.utils.json_to_sheet(sheet.data);
          XLSX.utils.book_append_sheet(workbook, worksheet, sheet.sheetName);
        }
      });
    } else {
      // Standard single sheet format
      const worksheet = XLSX.utils.json_to_sheet(data as any[]);
      XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
    }

    if (workbook.SheetNames.length === 0) {
      alert('No valid data to export');
      return;
    }

    XLSX.writeFile(workbook, fileName.endsWith('.xlsx') ? fileName : `${fileName}.xlsx`);
  } catch (error) {
    console.error("Export failed:", error);
    alert("Failed to export. Please try again.");
  }
};
