import React, { useState, useEffect, useMemo } from 'react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend
} from 'recharts';
import { Download, Filter, RefreshCw, Search, ChevronDown, Calendar, Clock, RotateCcw, Globe, ChevronLeft, ChevronRight, Eye } from 'lucide-react';
import { apiService, API_BASE_URL } from '../services/api';
import { exportToExcel } from '../utils/excelExport';

const COLORS = ['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#1e40af'];

export const ReportsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'inventory' | 'sales' | 'all'>('inventory');
  // State for fetched data
  const [inventoryDataState, setInventoryDataState] = useState<any[]>([]);
  const [salesDetailsState, setSalesDetailsState] = useState<any[]>([]);
  const [allReportsData, setAllReportsData] = useState<{ 
    inventory: any[], 
    sales: any[],
    delivery?: any,
    payments?: any,
    returns?: any
  } | null>(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [paymentFilter, setPaymentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Inventory Tab State
  const [showAllInventory, setShowAllInventory] = useState(false);
  const [inventoryPage, setInventoryPage] = useState(1);
  const [inventorySearch, setInventorySearch] = useState('');
  const [stockFilter, setStockFilter] = useState('all');
  const [inventorySort, setInventorySort] = useState('revenue_desc');
  const [revenueFilter, setRevenueFilter] = useState('all');
  const [salesSearch, setSalesSearch] = useState('');
  const ITEMS_PER_PAGE = 20;

  useEffect(() => {
    setInventoryPage(1);
  }, [inventorySearch, stockFilter, inventorySort, revenueFilter]);

  useEffect(() => {
    loadData();
  }, [activeTab]); // Load data when tab changes to avoid over-fetching if we want lazy loading, but simple is fine too.

  const handleExportInventory = (data?: any[]) => {
    const source = data || inventoryData.tableData;
    const dataToExport = source.map(item => ({
      'Item ID': item.id,
      'Product Name': item.name,
      'Price (₹)': item.price,
      'Stock Status': item.stock > 0 ? 'Available' : 'Out of Stock',
      'Available Stock': item.stock,
      'Orders Placed': item.ordersPlaced,
      'Total Revenue (₹)': item.totalRevenue
    }));
    return dataToExport;
  };

  const handleExportSales = (data?: any[]) => {
    const source = data || salesReportData.tableData;
    const dataToExport = source.map(row => ({
      'Order Date': new Date(row.orderDate).toLocaleDateString(),
      'Order ID': row.orderId,
      'Item ID': row.itemId,
      'Product Name': row.productName,
      'Quantity': row.quantity,
      'Total (₹)': row.finalTotal,
      'Payment Method': row.paymentMethod,
      'Status': row.status,
      'Store Name': row.storeName,
      'Customer Email': row.email || 'N/A',
      'Customer Phone': row.phone || 'N/A',
      'Full Address': row.address || 'N/A',
      'City': row.city || 'N/A',
      'State': row.state || 'N/A',
      'Pincode': row.pincode || 'N/A',
      'HSN Code': row.hsn || 'N/A',
      'SGST (%)': row.sgst || 0,
      'CGST (%)': row.cgst || 0,
      'IGST (%)': row.igst || 0,
      'Sales Representative': row.salesRep
    }));
    return dataToExport;
  };

  const downloadInventoryReport = () => {
    const data = handleExportInventory();
    exportToExcel(data, 'Sales_Inventory_Report', 'Inventory');
  };

  const downloadSalesReport = () => {
    const data = handleExportSales();
    exportToExcel(data, 'Sales_Report', 'Sales');
  };

  const handleExportAll = async () => {
    setLoading(true);
    try {
      const data = await apiService.getReportsAll();
      const inventorySheet = {
        sheetName: 'Inventory Report',
        data: handleExportInventory(data.inventory)
      };
      const salesSheet = {
        sheetName: 'Sales Report',
        data: handleExportSales(data.sales)
      };
      exportToExcel([inventorySheet, salesSheet], 'Complete_Systems_Report');
    } catch (error) {
      console.error("Failed to export all reports:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'inventory') {
        const data = await apiService.getSalesInventory();
        setInventoryDataState(data || []);
      } else if (activeTab === 'sales') {
        const data = await apiService.getSalesDetails();
        setSalesDetailsState(data || []);
      } else if (activeTab === 'all') {
        const data = await apiService.getReportsAll();
        setAllReportsData(data);
        setInventoryDataState(data.inventory || []);
        setSalesDetailsState(data.sales || []);
      }
    } catch (error) {
      console.error("Failed to load reports data:", error);
    } finally {
      setLoading(false);
    }
  };

  /* ===================================================================================
   *  DATA PREPARATION (Client-side filtering only)
   * =================================================================================== */

  // 1. Inventory Report Data
  const inventoryData = useMemo(() => {
    // Note: Inventory Date Filtering would require backend support as data is pre-aggregated.
    // For now we return all data as fetched.
    const filteredTable = inventoryDataState;

    // Chart Data: Top 6 by totalRevenue
    const sortedBySales = [...filteredTable].sort((a, b) => (Number(b.totalRevenue) || 0) - (Number(a.totalRevenue) || 0));
    const topProducts = sortedBySales.slice(0, 6).map(p => ({
      name: p.name,
      value: Number(p.totalRevenue) || 0
    }));

    const totalRevenue = topProducts.reduce((acc, curr) => acc + curr.value, 0);

    return { tableData: sortedBySales, chartData: topProducts, totalRevenue };
  }, [inventoryDataState]);


  // 2. Sales Report Data
  const salesReportData = useMemo(() => {
    let filteredRows = [...salesDetailsState];

    // Apply Filters
    if (startDate) {
      filteredRows = filteredRows.filter(r => new Date(r.orderDate) >= new Date(startDate));
    }
    if (endDate) {
      const end = new Date(endDate);
      end.setHours(23, 59, 59, 999);
      filteredRows = filteredRows.filter(r => new Date(r.orderDate) <= end);
    }
    if (paymentFilter) {
      filteredRows = filteredRows.filter(r => r.paymentMethod?.toLowerCase() === paymentFilter.toLowerCase());
    }
    if (statusFilter) {
      filteredRows = filteredRows.filter(r => r.status?.toLowerCase() === statusFilter.toLowerCase());
    }

    // Search Filter
    if (salesSearch) {
      const lowerSearch = salesSearch.toLowerCase();
      filteredRows = filteredRows.filter(r =>
        r.itemId?.toString().toLowerCase().includes(lowerSearch) ||
        r.productName?.toLowerCase().includes(lowerSearch) ||
        r.storeName?.toLowerCase().includes(lowerSearch) ||
        r.salesRep?.toLowerCase().includes(lowerSearch)
      );
    }

    // Calculate Total Value
    const totalValue = filteredRows.reduce((acc, curr) => acc + (curr.finalTotal || 0), 0);

    return { tableData: filteredRows, totalValue };
  }, [salesDetailsState, paymentFilter, statusFilter, startDate, endDate, salesSearch]);



  /* ===================================================================================
   *  RENDERERS
   * =================================================================================== */

  const renderInventoryTab = () => {
    const filteredItems = inventoryData.tableData.filter(item => {
      const matchesSearch = item.name?.toLowerCase().includes(inventorySearch.toLowerCase()) ||
        String(item.id).includes(inventorySearch);

      let matchesStock = true;
      if (stockFilter === 'available') matchesStock = item.stock > 0;
      if (stockFilter === 'out_of_stock') matchesStock = item.stock <= 0;

      let matchesRevenue = true;
      const rev = item.totalRevenue || 0;
      if (revenueFilter === 'high') matchesRevenue = rev > 50000;
      if (revenueFilter === 'medium') matchesRevenue = rev >= 10000 && rev <= 50000;
      if (revenueFilter === 'low') matchesRevenue = rev < 10000;

      return matchesSearch && matchesStock && matchesRevenue;
    });

    // Apply Sorting
    const sortedItems = [...filteredItems].sort((a, b) => {
      switch (inventorySort) {
        case 'revenue_asc': return (a.totalRevenue || 0) - (b.totalRevenue || 0);
        case 'orders_desc': return (b.ordersPlaced || 0) - (a.ordersPlaced || 0);
        case 'stock_desc': return (b.stock || 0) - (a.stock || 0);
        case 'stock_asc': return (a.stock || 0) - (b.stock || 0);
        case 'revenue_desc':
        default: return (b.totalRevenue || 0) - (a.totalRevenue || 0);
      }
    });

    const indexOfLastItem = inventoryPage * ITEMS_PER_PAGE;
    const indexOfFirstItem = indexOfLastItem - ITEMS_PER_PAGE;
    const currentItems = sortedItems.slice(indexOfFirstItem, indexOfLastItem);
    const totalPages = Math.ceil(sortedItems.length / ITEMS_PER_PAGE);

    return (
      <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
        {/* Top Section: Chart & Filters */}
        {/* Top Section: Chart Only (Full Width) */}
        <div className="grid grid-cols-1 gap-6">

          {/* Chart Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm min-h-[350px]">
            {/* Chart Content same as before */}
            <h3 className="text-sm font-bold text-slate-700 flex items-center gap-2 mb-4">
              <Clock size={16} /> Top Selling Products
            </h3>
            <div className="flex items-center justify-center h-[250px] relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={inventoryData.chartData}
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {inventoryData.chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                  <Legend layout="vertical" align="right" verticalAlign="middle" wrapperStyle={{ fontSize: '12px' }} />
                </PieChart>
              </ResponsiveContainer>
              {/* Center Text */}
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none pr-28">
                <span className="text-xs text-slate-400 font-medium">Total Revenue</span>
                <span className="text-2xl font-bold text-slate-800">₹{inventoryData.totalRevenue.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* View All Option */}
        {!showAllInventory ? (
          <div className="flex justify-center py-8">
            <button
              onClick={() => setShowAllInventory(true)}
              className="flex items-center gap-2 px-8 py-3 bg-blue-600 text-white rounded-xl shadow-lg hover:bg-blue-700 transition-all font-bold text-sm"
            >
              <Eye size={16} /> View All Products Sales Reports
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-between items-center px-2">
              <h3 className="font-bold text-slate-700">All Products Sales Report</h3>
              <button
                onClick={() => setShowAllInventory(false)}
                className="text-xs text-red-500 hover:underline font-medium"
              >
                Hide Report
              </button>
            </div>

            {/* Table */}
            <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                  <div className="w-1 h-4 bg-orange-500 rounded-full"></div> Sales Inventory Details
                </h3>
                <div className="flex gap-2">
                  <select
                    className="px-3 py-1.5 text-xs border border-slate-200 rounded-md bg-white text-slate-700 outline-none focus:border-blue-500 transition-colors"
                    value={stockFilter}
                    onChange={(e) => setStockFilter(e.target.value)}
                  >
                    <option value="all">Stock: All</option>
                    <option value="available">Available</option>
                    <option value="out_of_stock">Out of Stock</option>
                  </select>

                  <select
                    className="px-3 py-1.5 text-xs border border-slate-200 rounded-md bg-white text-slate-700 outline-none focus:border-blue-500 transition-colors"
                    value={revenueFilter}
                    onChange={(e) => setRevenueFilter(e.target.value)}
                  >
                    <option value="all">Revenue: All</option>
                    <option value="high">High (&gt;50k)</option>
                    <option value="medium">Medium (10k-50k)</option>
                    <option value="low">Low (&lt;10k)</option>
                  </select>

                  <select
                    className="px-3 py-1.5 text-xs border border-slate-200 rounded-md bg-white text-slate-700 outline-none focus:border-blue-500 transition-colors"
                    value={inventorySort}
                    onChange={(e) => setInventorySort(e.target.value)}
                  >
                    <option value="revenue_desc">Sort: Revenue High-Low</option>
                    <option value="revenue_asc">Sort: Revenue Low-High</option>
                    <option value="orders_desc">Sort: Orders High-Low</option>
                    <option value="stock_desc">Sort: Stock High-Low</option>
                    <option value="stock_asc">Sort: Stock Low-High</option>
                  </select>

                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={14} />
                    <input
                      type="text"
                      placeholder="Search Product or ID"
                      className="pl-9 pr-4 py-1.5 text-xs border border-slate-200 rounded-md outline-none focus:border-blue-500 transition-colors"
                      value={inventorySearch}
                      onChange={(e) => setInventorySearch(e.target.value)}
                    />
                  </div>
                  <button
                    onClick={downloadInventoryReport}
                    className="flex items-center gap-2 px-3 py-1.5 bg-green-600 text-white rounded-md text-xs font-bold hover:bg-green-700 transition-colors"
                    title="Export to Excel"
                  >
                    <Download size={14} /> Export
                  </button>
                  <button
                    onClick={() => { setInventorySearch(''); setStockFilter('all'); setRevenueFilter('all'); setInventorySort('revenue_desc'); setInventoryPage(1); }}
                    className="p-1 px-2 border border-slate-200 rounded-md bg-white text-slate-500 hover:text-slate-800"
                    title="Reset All"
                  >
                    <RotateCcw size={14} />
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-slate-50 border-b border-slate-100">
                    <tr>
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Item ID</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Product Name</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Stock</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Orders Placed</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Revenue</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {currentItems.map((item, idx) => (
                      <tr key={item.id || idx} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-6 py-4 text-sm text-slate-600 font-mono">{item.id}</td>
                        <td className="px-6 py-4 text-sm font-medium text-slate-800">{item.name}</td>
                        <td className="px-6 py-4">
                          <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase ${item.stock > 10 ? 'bg-amber-50 text-amber-700 border border-amber-100' : 'bg-red-50 text-red-700 border border-red-100'
                            }`}>
                            {item.stock > 0 ? 'Available' : 'Out of Stock'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-600 font-bold">{item.ordersPlaced}</td>
                        <td className="px-6 py-4 text-sm text-slate-800 font-bold">₹{(item.totalRevenue || 0).toLocaleString()}</td>
                      </tr>
                    ))}
                    {currentItems.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-6 py-8 text-center text-slate-400 text-sm">
                          {inventorySearch || stockFilter !== 'all' ? 'No products match your search/filter.' : 'No inventory data found.'}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="px-6 py-4 border-t border-slate-100 flex flex-col sm:flex-row justify-between items-center gap-4 bg-slate-50/30">
                <span className="text-xs text-slate-500">
                  Showing <span className="font-bold text-slate-700">{filteredItems.length > 0 ? indexOfFirstItem + 1 : 0}</span> to <span className="font-bold text-slate-700">{Math.min(indexOfLastItem, filteredItems.length)}</span> of <span className="font-bold text-slate-700">{filteredItems.length}</span> entries
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setInventoryPage(prev => Math.max(prev - 1, 1))}
                    disabled={inventoryPage === 1}
                    className="p-1 px-3 border border-slate-200 rounded-md bg-white text-slate-600 disabled:opacity-50 hover:bg-slate-50 disabled:hover:bg-white text-xs font-medium transition-colors"
                  >
                    Previous
                  </button>
                  <span className="text-xs font-bold text-slate-700 bg-white border border-slate-200 px-3 py-1 rounded-md">Page {inventoryPage} of {totalPages || 1}</span>
                  <button
                    onClick={() => setInventoryPage(prev => Math.min(prev + 1, totalPages))}
                    disabled={inventoryPage === totalPages}
                    className="p-1 px-3 border border-slate-200 rounded-md bg-white text-slate-600 disabled:opacity-50 hover:bg-slate-50 disabled:hover:bg-white text-xs font-medium transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          </div>
        )
        }
      </div >
    );
  };

  const renderSalesTab = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">

      {/* Top Section: Chart (Duplicated to Sales Reports as per request) */}

      <div className="flex justify-between items-end border-b border-slate-200 pb-4">
        <div>
          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <Globe size={18} className="text-slate-400" /> Sale Report Details
          </h3>
        </div>
        <div>
          <span className="text-sm font-bold text-blue-600 flex items-center gap-1 bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100">
            <Download size={14} /> Total Order Value: <span className="text-slate-900 text-lg">₹{salesReportData.totalValue.toLocaleString()}</span>
          </span>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">

        <div className="relative">
          <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Start Date</label>
          <div className="relative">
            <input
              type="date"
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
        </div>

        <div className="relative">
          <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">End Date</label>
          <div className="relative">
            <input
              type="date"
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
        </div>

        <div>
          <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Payment Method</label>
          <select
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none"
            value={paymentFilter}
            onChange={(e) => setPaymentFilter(e.target.value)}
          >
            <option value="">Select option</option>
            <option value="cod">Cash on delivery</option>
            <option value="prepaid">Prepaid</option>
            <option value="razorpay">Razorpay</option>
          </select>
        </div>

        <div>
          <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Status</label>
          <select
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">Select option</option>
            <option value="pending">Pending</option>
            <option value="confirmed">Confirmed</option>
            <option value="shipped">Shipped</option>
            <option value="delivered">Delivered</option>
            <option value="AWB_GENERATED">AWB Generated</option>
          </select>
        </div>

        <div className="md:col-span-4 flex gap-3 justify-end pt-2 border-t border-slate-100 mt-2">

          <button
            onClick={() => { setStartDate(''); setEndDate(''); setPaymentFilter(''); setStatusFilter(''); setSalesSearch(''); }}
            className="flex items-center gap-2 px-6 py-2 bg-white text-slate-600 rounded-lg text-sm font-bold border border-slate-200 hover:bg-slate-50"
          >
            <RefreshCw size={14} /> Reset
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">

        {/* Toolbar */}
        {/* Toolbar */}
        <div className="px-4 py-3 border-b border-slate-100 flex justify-end gap-2 bg-slate-50/50">
          <div className="relative">
            <input
              type="text"
              placeholder="Search Sales..."
              className="px-3 py-1.5 text-xs border border-slate-200 rounded-md bg-white w-64 focus:outline-none focus:border-blue-500 transition-colors"
              value={salesSearch}
              onChange={(e) => setSalesSearch(e.target.value)}
            />
            {salesSearch && (
              <button
                onClick={() => setSalesSearch('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <RefreshCw size={10} />
              </button>
            )}
          </div>
          <button 
            onClick={downloadSalesReport}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-xs font-bold"
          >
            <Download size={14} /> Export Excel
          </button>
          <button className="p-1.5 bg-slate-700 text-white rounded-md hover:bg-slate-800 transition-colors"><RefreshCw size={14} /></button>
          <button className="p-1.5 bg-slate-700 text-white rounded-md hover:bg-slate-800 transition-colors"><Filter size={14} /></button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>
                <th className="px-4 py-4 w-8 text-center text-slate-400">+</th>
                <th className="px-4 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Item ID</th>
                <th className="px-4 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Product Name</th>
                <th className="px-4 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Final Total (₹)</th>
                <th className="px-4 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Payment Method</th>
                <th className="px-4 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Store Name</th>
                <th className="px-4 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Sales Representative</th>
                <th className="px-4 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Order Date</th>
                <th className="px-4 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Order Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {salesReportData.tableData.map((row) => (
                <tr key={row.uniqueKey} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-4 py-3 text-center text-blue-500 font-bold text-lg cursor-pointer">+</td>
                  <td className="px-4 py-3 text-xs text-slate-600 font-mono">{row.itemId}</td>
                  <td className="px-4 py-3 text-xs font-medium text-slate-800 max-w-[200px] truncate" title={row.productName}>{row.productName}</td>
                  <td className="px-4 py-3 text-xs text-slate-700 font-bold">₹{row.finalTotal.toFixed(2)}</td>
                  <td className="px-4 py-3 text-xs text-slate-600">{row.paymentMethod}</td>
                  <td className="px-4 py-3 text-xs text-slate-600">{row.storeName}</td>
                  <td className="px-4 py-3 text-xs text-slate-600">{row.salesRep}</td>
                  <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">{new Date(row.orderDate).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-slate-100 text-slate-600">
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
              {salesReportData.tableData.length === 0 && (
                <tr><td colSpan={9} className="text-center py-8 text-slate-400 text-sm">No sales records found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderAllReportsTab = () => {
    const totalInventoryItems = inventoryDataState.length;
    const totalSalesCount = inventoryDataState.reduce((acc, curr) => acc + (curr.ordersPlaced || 0), 0);
    const totalRevenue = inventoryDataState.reduce((acc, curr) => acc + (curr.totalRevenue || 0), 0);

    // Prepare Payment Mix Chart Data
    const paymentData = allReportsData?.payments ? Object.entries(allReportsData.payments).map(([name, value]) => ({ name, value })) : [];
    // Prepare Delivery Stats Chart Data
    const deliveryData = allReportsData?.delivery ? Object.entries(allReportsData.delivery).map(([name, value]) => ({ name, value })) : [];

    return (
      <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4">
        {/* Top Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h4 className="text-slate-500 text-[10px] font-bold uppercase tracking-wider mb-1">Catalog Items</h4>
            <div className="text-2xl font-bold text-slate-900">{totalInventoryItems}</div>
            <div className="mt-2 text-[10px] text-blue-600 font-bold bg-blue-50 px-2 py-0.5 rounded-full inline-block">Live Inventory</div>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h4 className="text-slate-500 text-[10px] font-bold uppercase tracking-wider mb-1">Units Sold</h4>
            <div className="text-2xl font-bold text-slate-900">{totalSalesCount}</div>
            <div className="mt-2 text-[10px] text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded-full inline-block">Total Volume</div>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h4 className="text-slate-500 text-[10px] font-bold uppercase tracking-wider mb-1">Total Revenue</h4>
            <div className="text-2xl font-bold text-slate-900">₹{totalRevenue.toLocaleString()}</div>
            <div className="mt-2 text-[10px] text-amber-600 font-bold bg-amber-50 px-2 py-0.5 rounded-full inline-block">Gross Sales</div>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h4 className="text-slate-500 text-[10px] font-bold uppercase tracking-wider mb-1">Active Returns</h4>
            <div className="text-2xl font-bold text-slate-900">{allReportsData?.returns?.total_returns || 0}</div>
            <div className="mt-2 text-[10px] text-red-600 font-bold bg-red-50 px-2 py-0.5 rounded-full inline-block">Return Rate: {allReportsData?.returns?.return_rate || 0}%</div>
          </div>
        </div>

        {/* System Records Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <h5 className="text-slate-400 text-[9px] font-bold uppercase">Registered Users</h5>
            <div className="text-xl font-bold text-slate-700">{allReportsData?.master_counts?.users || 0}</div>
          </div>
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <h5 className="text-slate-400 text-[9px] font-bold uppercase">B2B Partners</h5>
            <div className="text-xl font-bold text-slate-700">{allReportsData?.master_counts?.b2b || 0}</div>
          </div>
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <h5 className="text-slate-400 text-[9px] font-bold uppercase">Deliveries</h5>
            <div className="text-xl font-bold text-slate-700">{allReportsData?.master_counts?.deliveries || 0}</div>
          </div>
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <h5 className="text-slate-400 text-[9px] font-bold uppercase">Refunds/Exchanges</h5>
            <div className="text-xl font-bold text-slate-700">
              {(allReportsData?.master_counts?.refunds || 0) + (allReportsData?.master_counts?.exchanges || 0)}
            </div>
          </div>
        </div>

        {/* Analytics Charts Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Payment Mix */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-xs font-bold text-slate-700 flex items-center gap-2 mb-4 uppercase">
              <div className="w-1 h-3 bg-blue-500 rounded-full"></div> Payment Mix
            </h3>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={paymentData} innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value">
                    {paymentData.map((_, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 space-y-1">
              {paymentData.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center text-[10px]">
                  <span className="text-slate-500">{item.name}</span>
                  <span className="font-bold text-slate-700">{item.value} Orders</span>
                </div>
              ))}
            </div>
          </div>

          {/* Top Selling Chart */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-xs font-bold text-slate-700 flex items-center gap-2 mb-4 uppercase">
              <div className="w-1 h-3 bg-orange-500 rounded-full"></div> Product Sales
            </h3>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={inventoryData.chartData} innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value">
                    {inventoryData.chartData.map((_, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
             <div className="mt-2 space-y-1 text-[10px]">
                <div className="flex justify-between font-bold text-blue-600 mb-1 border-b border-slate-50 pb-1">
                  <span>Top Performing Item</span>
                  <span>Revenue Contribution</span>
                </div>
                {inventoryData.chartData.slice(0, 3).map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-slate-500 truncate w-32">{item.name}</span>
                    <span className="font-bold text-slate-700">₹{item.value.toLocaleString()}</span>
                  </div>
                ))}
             </div>
          </div>

          {/* Delivery Stats */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-xs font-bold text-slate-700 flex items-center gap-2 mb-4 uppercase">
              <div className="w-1 h-3 bg-emerald-500 rounded-full"></div> Delivery Funnel
            </h3>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={deliveryData} innerRadius={50} outerRadius={70} paddingAngle={2} dataKey="value">
                    {deliveryData.map((_, index) => <Cell key={`cell-${index}`} fill={['#10b981', '#3b82f6', '#f59e0b', '#64748b'][index % 4]} />)}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
             <div className="mt-2 space-y-1">
              {deliveryData.slice(0, 4).map((item, idx) => (
                <div key={idx} className="flex justify-between items-center text-[10px]">
                  <span className="text-slate-500 capitalize">{item.name.replace('_', ' ')}</span>
                  <span className="font-bold text-slate-700">{item.value} Units</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Master Report Download Section */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-3xl p-8 text-white shadow-xl flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="space-y-2 text-center md:text-left">
              <h3 className="text-xl font-bold">Consolidated Data Vault</h3>
              <p className="text-blue-100 text-xs max-w-lg opacity-90">
                Generate a comprehensive master export containing detailed inventory metrics and transaction-level sales data with full tax and customer metadata.
              </p>
            </div>
            <button
              onClick={handleExportAll}
              disabled={loading}
              className="px-8 py-4 bg-white text-blue-600 rounded-2xl font-bold shadow-2xl hover:bg-slate-50 transition-all flex items-center gap-3 disabled:opacity-50 min-w-[280px] justify-center"
            >
              {loading ? <RefreshCw className="animate-spin" size={20} /> : <Download size={20} />}
              {loading ? "Crunching All Data..." : "Export Full Master Report"}
            </button>
        </div>

        {/* FULL DATA TABLES SECTION */}
        <div className="space-y-12 pb-20">
            {/* Inventory Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center text-orange-600 font-bold">01</div>
                <h2 className="text-lg font-bold text-slate-800">Sales Inventory Master Table</h2>
              </div>
              {renderInventoryTableContent(true)}
            </div>

            {/* Sales Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center text-blue-600 font-bold">02</div>
                <h2 className="text-lg font-bold text-slate-800">Transaction Details Master Table</h2>
              </div>
              {renderSalesTableContent(true)}
            </div>
        </div>
      </div>
    );
  };

  // Helper functions to reuse table parts
  const renderInventoryTableContent = (isAllTab = false) => {
    // Reusing existing table logic
    const filteredItems = inventoryData.tableData.filter(item => {
      const matchesSearch = item.name?.toLowerCase().includes(inventorySearch.toLowerCase()) ||
        String(item.id).includes(inventorySearch);
      let matchesStock = true;
      if (stockFilter === 'available') matchesStock = item.stock > 0;
      if (stockFilter === 'out_of_stock') matchesStock = item.stock <= 0;
      return matchesSearch && matchesStock;
    });

    const currentItems = isAllTab ? filteredItems.slice(0, 100) : filteredItems.slice(0, 20); // Show more in all tab

    return (
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
           {!isAllTab && <h3 className="font-bold text-slate-800 text-sm">Inventory Details</h3>}
           <div className={`flex gap-2 ${isAllTab ? 'w-full justify-between' : ''}`}>
               <div className="relative flex-1 max-w-xs">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" size={14} />
                  <input
                    type="text"
                    placeholder="Search inventory..."
                    className="pl-8 pr-4 py-1.5 text-xs border border-slate-200 rounded-md bg-white w-full"
                    value={inventorySearch}
                    onChange={(e) => setInventorySearch(e.target.value)}
                  />
               </div>
               <div className="flex gap-2">
                <select className="px-2 py-1.5 text-xs border border-slate-200 rounded-md" value={stockFilter} onChange={(e) => setStockFilter(e.target.value)}>
                    <option value="all">Stock: All</option>
                    <option value="available">Available</option>
                    <option value="out_of_stock">Out of Stock</option>
                </select>
                <button onClick={downloadInventoryReport} className="p-2 bg-green-50 text-green-600 rounded-md border border-green-100"><Download size={14} /></button>
               </div>
           </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>
                <th className="px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Item ID</th>
                <th className="px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Product Name</th>
                <th className="px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Stock</th>
                <th className="px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Orders</th>
                <th className="px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Revenue</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {currentItems.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50">
                  <td className="px-5 py-3 text-xs text-slate-500 font-mono">{item.id}</td>
                  <td className="px-5 py-3 text-xs font-medium text-slate-800">{item.name}</td>
                  <td className="px-5 py-3"><span className={`text-[10px] font-bold ${item.stock > 0 ? 'text-emerald-500' : 'text-red-500'}`}>{item.stock > 0 ? 'INSTOCK' : 'OUTSTOCK'}</span></td>
                  <td className="px-5 py-3 text-xs text-slate-600 font-bold">{item.ordersPlaced}</td>
                  <td className="px-5 py-3 text-xs text-slate-900 font-bold">₹{item.totalRevenue?.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {isAllTab && filteredItems.length > 100 && <div className="p-4 text-center text-[10px] text-slate-400 font-bold uppercase tracking-widest bg-slate-50/30">Showing Top 100 Items — Export for full list</div>}
        </div>
      </div>
    );
  };

  const renderSalesTableContent = (isAllTab = false) => {
    const currentRows = isAllTab ? salesReportData.tableData.slice(0, 100) : salesReportData.tableData;

    return (
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
           {!isAllTab && <h3 className="font-bold text-slate-800 text-sm">Transaction Logs</h3>}
           <div className={`flex gap-2 ${isAllTab ? 'w-full justify-between' : ''}`}>
               <div className="relative flex-1 max-w-xs">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" size={14} />
                  <input
                    type="text"
                    placeholder="Search transactions..."
                    className="pl-8 pr-4 py-1.5 text-xs border border-slate-200 rounded-md bg-white w-full"
                    value={salesSearch}
                    onChange={(e) => setSalesSearch(e.target.value)}
                  />
               </div>
               <div className="flex gap-2">
                <select className="px-2 py-1.5 text-xs border border-slate-200 rounded-md" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                    <option value="">Status: All</option>
                    <option value="pending">Pending</option>
                    <option value="confirmed">Confirmed</option>
                    <option value="shipped">Shipped</option>
                    <option value="delivered">Delivered</option>
                </select>
                <button onClick={downloadSalesReport} className="p-2 bg-green-50 text-green-600 rounded-md border border-green-100"><Download size={14} /></button>
               </div>
           </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>
                <th className="px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Date</th>
                <th className="px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Order ID</th>
                <th className="px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Customer</th>
                <th className="px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Item</th>
                <th className="px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Total</th>
                <th className="px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {currentRows.map((row) => (
                <tr key={row.uniqueKey} className="hover:bg-slate-50/50">
                  <td className="px-5 py-3 text-[10px] text-slate-500 whitespace-nowrap">{new Date(row.orderDate).toLocaleDateString()}</td>
                  <td className="px-5 py-3 text-xs font-mono text-slate-600">{row.orderId}</td>
                  <td className="px-5 py-3 text-xs text-slate-800 font-medium">{row.storeName}</td>
                  <td className="px-5 py-3 text-[10px] text-slate-500 max-w-[150px] truncate">{row.productName}</td>
                  <td className="px-5 py-3 text-xs text-slate-900 font-bold">₹{row.finalTotal?.toLocaleString()}</td>
                  <td className="px-5 py-3">
                    <span className="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase bg-slate-100 text-slate-600">
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {isAllTab && salesReportData.tableData.length > 100 && <div className="p-4 text-center text-[10px] text-slate-400 font-bold uppercase tracking-widest bg-slate-50/30">Showing Latest 100 Transactions — Export for full history</div>}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-[#F8FAFC] overflow-hidden font-sans">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-8 py-5 shrink-0 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {activeTab === 'inventory' ? 'View Sale Inventory Reports' : 'View Sale Reports'}
          </h1>
          <div className="flex gap-2 text-xs text-slate-500 mt-1">
            <span>Home</span> <span>&rsaquo;</span> <span>Reports</span> <span>&rsaquo;</span>
            <span className="font-semibold text-slate-800">{activeTab === 'inventory' ? 'Sales Inventory Reports' : 'Sales Reports'}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-slate-200 px-8">
        <div className="flex space-x-8">
          <button
            onClick={() => setActiveTab('inventory')}
            className={`py-4 text-sm font-bold border-b-2 transition-colors ${activeTab === 'inventory' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
          >
            Sales Inventory Reports
          </button>
          <button
            onClick={() => setActiveTab('sales')}
            className={`py-4 text-sm font-bold border-b-2 transition-colors ${activeTab === 'sales' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
          >
            Sales Reports
          </button>
          <button
            onClick={() => setActiveTab('all')}
            className={`py-4 text-sm font-bold border-b-2 transition-colors ${activeTab === 'all' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
          >
            All Reports Summary
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-[1400px] mx-auto">
          {activeTab === 'inventory' ? renderInventoryTab() : 
           activeTab === 'sales' ? renderSalesTab() : renderAllReportsTab()}
        </div>
      </div>
    </div>
  );
};