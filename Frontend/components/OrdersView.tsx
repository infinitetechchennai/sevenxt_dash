
import React, { useState, useMemo, useEffect } from 'react';
import {
  Search, Eye, Download, ShoppingBag, Printer, X, CreditCard, MapPin, Phone, Mail, ArrowLeft, Calendar, PlayCircle, CheckCircle, Package
} from 'lucide-react';
import Barcode from 'react-barcode';

import logo from '../assets/logo.jpg';
import { apiService, API_BASE_URL } from '../services/api';

const STATUS_TABS = [
  'All Orders',
  'Confirmed',
  'Processing',
  'Ready to Pickup',
  'Delivered',
  'Cancelled'
];

interface OrdersViewProps {
  initialSearchTerm?: string;
}

export const OrdersView: React.FC<OrdersViewProps> = ({ initialSearchTerm = '' }) => {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeStatus, setActiveStatus] = useState('All Orders');
  const [searchTerm, setSearchTerm] = useState(initialSearchTerm);
  const [selectedOrder, setSelectedOrder] = useState<any>(null);

  // Bulk Selection State
  const [selectedOrders, setSelectedOrders] = useState<Set<string>>(new Set());

  // Dimensions Modal State
  const [dimensionsModalOpen, setDimensionsModalOpen] = useState(false);
  const [currentOrderId, setCurrentOrderId] = useState<string | null>(null);
  const [dimensionsData, setDimensionsData] = useState({ height: '', weight: '', breadth: '', length: '' });

  // Pickup Time State
  const [pickupTimes, setPickupTimes] = useState<Record<string, string>>({});

  // Date Filters
  const [filterDate, setFilterDate] = useState('');
  const [filterMonth, setFilterMonth] = useState('');
  const [filterYear, setFilterYear] = useState('');

  // Count State
  const [statusCounts, setStatusCounts] = useState<Record<string, number>>({
    'All Orders': 0, 'Confirmed': 0, 'Processing': 0, 'Ready to Pickup': 0, 'Delivered': 0, 'Cancelled': 0
  });

  // Calculate counts
  useEffect(() => {
    const updateCounts = async () => {
      if (activeStatus === 'Ready to Pickup') {
        // When in Delivery view, we don't have all orders in state, so fetch them for counts
        try {
          const data = await apiService.fetchOrders();
          const normalize = (s: string) => (s && s.charAt(0).toUpperCase() + s.slice(1).toLowerCase()) || 'Pending';

          setStatusCounts({
            'All Orders': data.length,
            'Confirmed': data.filter((o: any) => normalize(o.status) === 'Confirmed').length,
            'Processing': data.filter((o: any) => normalize(o.status) === 'Processing').length,
            'Ready to Pickup': orders.filter((o: any) => {
              if (!o.status) return false;
              const s = o.status.toUpperCase().replace('_', ' ');
              return s === 'READY TO PICKUP' || s === 'PICKUP TIME SCHEDULED' || s === 'AWB GENERATED';
            }).length,
            'Delivered': data.filter((o: any) => normalize(o.status) === 'Delivered').length,
            'Cancelled': data.filter((o: any) => normalize(o.status) === 'Cancelled').length
          });
        } catch (e) { console.error(e); }
      } else {
        // When in standard views, 'orders' contains the full list
        setStatusCounts({
          'All Orders': orders.length,
          'Confirmed': orders.filter(o => o.status === 'Confirmed').length,
          'Processing': orders.filter(o => o.status === 'Processing').length,
          'Ready to Pickup': orders.filter(o => ['Ready to Pickup', 'Pickup Time Scheduled', 'AWB Generated'].includes(o.status)).length,
          'Delivered': orders.filter(o => o.status === 'Delivered').length,
          'Cancelled': orders.filter(o => o.status === 'Cancelled').length
        });
      }
    };
    updateCounts();
  }, [orders, activeStatus]);

  // Fetch Orders
  useEffect(() => {
    if (activeStatus === 'Ready to Pickup') {
      fetchDeliveries();
    } else {
      fetchOrders();
    }
  }, [activeStatus]);

  const fetchDeliveries = async () => {
    try {
      setLoading(true);
      const data = await apiService.fetchDeliveries();

      const mappedDeliveries = data.map(d => {
        // Parse item_name string back to productList structure
        // Format: "Item A x2, Item B x1"
        const parsedProducts = d.item_name ? d.item_name.split(', ').map((itemStr: string) => {
          const lastXIndex = itemStr.lastIndexOf(' x');
          if (lastXIndex !== -1) {
            return {
              name: itemStr.substring(0, lastXIndex),
              quantity: parseInt(itemStr.substring(lastXIndex + 2)) || 1
            };
          }
          return { name: itemStr, quantity: 1 };
        }) : [];

        return {
          id: d.order_number || `ORD-${d.order_id}`,
          deliveryId: d.id, // Actual delivery ID for API calls
          customer: d.customer_name,
          date: new Date(d.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }),
          amount: parseFloat(d.amount),
          payment: d.payment,
          items: d.quantity,
          productList: parsedProducts,
          status: d.delivery_status || 'Ready to Pickup', // Use actual status from DB
          type: 'Delivery', // or fetch from order if needed
          email: '', // Not in delivery table
          phone: d.phone,
          address: d.full_address,
          height: d.height,
          weight: d.weight,
          breadth: d.breadth,
          length: d.length,
          schedule_pickup: d.schedule_pickup,
          awb_label_path: d.awb_label_path,
          awb_number: d.awb_number, // AWB number for barcode
          rawDate: d.created_at,
          sgst_percentage: d.sgst_percentage,
          cgst_percentage: d.cgst_percentage
        };
      });

      setOrders(prevOrders => {
        const deliveryMap = new Map(mappedDeliveries.map((d: any) => [d.id, d]));

        // If we have existing orders, merge delivery info
        if (prevOrders.length > 0) {
          return prevOrders.map(order => {
            if (deliveryMap.has(order.id)) {
              const delivery = deliveryMap.get(order.id);
              return {
                ...order,
                ...delivery,
                type: order.type, // Preserve original customer type
                status: delivery.status // Prioritize delivery status
              };
            }
            return order;
          });
        }

        // Fallback if no orders loaded yet (though fetchOrders usually runs first)
        return mappedDeliveries;
      });
    } catch (error) {
      console.error("Failed to fetch deliveries:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const data = await apiService.fetchOrders();

      // Map API data to UI format
      const mappedOrders = data.map(order => {
        let parsedProducts = [];
        try {
          if (typeof order.products === 'object' && order.products !== null) {
            // It's already parsed (likely by the backend or DB driver)
            parsedProducts = order.products;
          } else if (typeof order.products === 'string') {
            // Try standard JSON parse
            parsedProducts = JSON.parse(order.products || '[]');
          } else {
            parsedProducts = [];
          }

          // Ensure it's an array (handle case where it's a single object)
          if (parsedProducts && typeof parsedProducts === 'object' && !Array.isArray(parsedProducts)) {
            parsedProducts = [parsedProducts];
          }
        } catch (e) {
          try {
            // Try replacing single quotes with double quotes (common if data was saved as Python string)
            // Also handle Decimal('...') which might appear in Python string dumps
            let fixedJson = (order.products as string)
              .replace(/'/g, '"')
              .replace(/None/g, 'null')
              .replace(/False/g, 'false')
              .replace(/True/g, 'true')
              .replace(/Decimal\("([^"]+)"\)/g, '$1') // Handle Decimal("10.00")
              .replace(/Decimal\('([^']+)'\)/g, '$1'); // Handle Decimal('10.00')

            parsedProducts = JSON.parse(fixedJson);
          } catch (e2) {
            console.error("Failed to parse products JSON:", order.products);
            parsedProducts = [];
          }
        }

        return {
          id: order.order_id,
          customer: order.customer_name || `User #${order.user_id || 'Unknown'}`, // Use customer_name from API
          date: new Date(order.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }),
          amount: parseFloat(order.amount),
          payment: order.payment || 'Unpaid',
          items: parsedProducts.length || 1,
          productList: parsedProducts, // Store the actual product list
          status: (order.status && order.status.charAt(0).toUpperCase() + order.status.slice(1).toLowerCase()) || 'Pending',
          type: order.customer_type || 'B2C',
          email: order.email,
          phone: order.phone,
          address: order.address,
          height: order.height,
          weight: order.weight,
          breadth: order.breadth,
          length: order.length,
          awb_number: order.awb_number, // AWB number for barcode
          sgst_percentage: order.sgst_percentage,
          cgst_percentage: order.cgst_percentage,

          rawDate: order.created_at // Keep raw date for sorting

        };
      });

      setOrders(mappedOrders);
    } catch (error) {
      console.error("Failed to fetch orders:", error);
    } finally {
      setLoading(false);
    }
  };

  // Sync with global search prop
  useEffect(() => {
    if (initialSearchTerm !== undefined) {
      setSearchTerm(initialSearchTerm);
    }
  }, [initialSearchTerm]);

  // Get unique years for dropdown
  const availableYears = useMemo(() => {
    const years = new Set(orders.map(o => new Date(o.date).getFullYear()));
    return Array.from(years).sort((a, b) => b - a);
  }, [orders]);

  // Filter Logic
  const filteredOrders = orders.filter(order => {
    const orderDate = new Date(order.date);
    const matchesStatus = activeStatus === 'All Orders'
      || order.status === activeStatus
      || (activeStatus === 'Ready to Pickup' && (order.status === 'Pickup Time Scheduled' || order.status === 'AWB Generated'));
    const matchesSearch = order.id.toLowerCase().includes(searchTerm.toLowerCase()) || order.customer.toLowerCase().includes(searchTerm.toLowerCase());

    // Date Logic
    let matchesDate = true;

    if (filterDate) {
      // Exact Date Match
      const selDate = new Date(filterDate);
      matchesDate = orderDate.getDate() === selDate.getDate() &&
        orderDate.getMonth() === selDate.getMonth() &&
        orderDate.getFullYear() === selDate.getFullYear();
    } else {
      // Month & Year Logic
      if (filterMonth) {
        matchesDate = matchesDate && orderDate.getMonth() === parseInt(filterMonth);
      }
      if (filterYear) {
        matchesDate = matchesDate && orderDate.getFullYear() === parseInt(filterYear);
      }
    }

    return matchesStatus && matchesSearch && matchesDate;
  });

  // Group Orders by Date
  const groupedOrders = useMemo(() => {
    const groups: Record<string, any[]> = {};
    filteredOrders.forEach(order => {
      if (!groups[order.date]) {
        groups[order.date] = [];
      }
      groups[order.date].push(order);
    });
    return groups;
  }, [filteredOrders]);

  // Sort dates (newest first)
  const sortedDates = Object.keys(groupedOrders).sort((a, b) => new Date(b).getTime() - new Date(a).getTime());

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Delivered': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'On the way': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'Processing': return 'bg-indigo-100 text-indigo-700 border-indigo-200';
      case 'Confirmed': return 'bg-violet-100 text-violet-700 border-violet-200';
      case 'Ready to Pickup':
      case 'AWB Generated':
        return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'Pickup Time Scheduled':
        return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'Pickup': return 'bg-amber-100 text-amber-700 border-amber-200'; // Fallback
      case 'Pending': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'Cancelled': return 'bg-rose-100 text-rose-700 border-rose-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const downloadCSV = () => {
    const headers = ['Order ID', 'Customer', 'Date', 'Amount', 'Items', 'Status', 'Payment', 'Type', 'Email', 'Address'];
    const csvContent = [
      headers.join(','),
      ...filteredOrders.map(order => [
        order.id,
        `"${order.customer}"`,
        order.date,
        order.amount,
        order.items,
        order.status,
        order.payment,
        order.type,
        order.email,
        `"${order.address}"`
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', 'orders_export.csv');
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const clearDateFilters = () => {
    setFilterDate('');
    setFilterMonth('');
    setFilterYear('');
  };

  const handleProcessOrder = (orderId: string) => {
    setOrders(prevOrders => prevOrders.map(order =>
      order.id === orderId ? { ...order, status: 'Processing' } : order
    ));
  };

  const handleConfirmOrder = async (orderId: string) => {
    try {
      await apiService.updateOrderStatus(orderId, 'Confirmed');
      setOrders(prevOrders => prevOrders.map(order =>
        order.id === orderId ? { ...order, status: 'Confirmed' } : order
      ));
    } catch (error) {
      console.error("Failed to confirm order:", error);
      alert("Failed to confirm order. Please try again.");
    }
  };

  const openDimensionsModal = (orderId: string, existingData?: any) => {
    setCurrentOrderId(orderId);
    if (existingData) {
      setDimensionsData({
        height: existingData.height || '',
        weight: existingData.weight || '',
        breadth: existingData.breadth || '',
        length: existingData.length || ''
      });
    } else {
      setDimensionsData({ height: '', weight: '', breadth: '', length: '' });
    }
    setDimensionsModalOpen(true);
  };

  const handleDimensionsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrderId) return;

    try {
      await apiService.updateOrderDimensions(currentOrderId, {
        height: parseFloat(dimensionsData.height),
        weight: parseFloat(dimensionsData.weight),
        breadth: parseFloat(dimensionsData.breadth),
        length: parseFloat(dimensionsData.length)
      });

      // Update local state
      setOrders(prevOrders => prevOrders.map(order =>
        order.id === currentOrderId ? {
          ...order,
          height: parseFloat(dimensionsData.height),
          weight: parseFloat(dimensionsData.weight),
          breadth: parseFloat(dimensionsData.breadth),
          length: parseFloat(dimensionsData.length)
        } : order
      ));

      setDimensionsModalOpen(false);
    } catch (error) {
      console.error("Failed to update dimensions:", error);
      alert("Failed to update dimensions. Please try again.");
    }
  };

  const handleProcessToDelivery = async (orderId: string) => {
    try {
      await apiService.updateOrderStatus(orderId, 'Processing');
      setOrders(prevOrders => prevOrders.map(order =>
        order.id === orderId ? { ...order, status: 'Processing' } : order
      ));
    } catch (error) {
      console.error("Failed to process order:", error);
    }
  };

  const handlePickupOrder = async (orderId: string) => {
    try {
      await apiService.updateOrderStatus(orderId, 'Ready to Pickup');
      setOrders(prevOrders => prevOrders.map(order =>
        order.id === orderId ? { ...order, status: 'Ready to Pickup' } : order
      ));
    } catch (error) {
      console.error("Failed to move to pickup:", error);
      alert("Failed to move order to pickup. Please try again.");
    }
  };

  // Bulk Selection Functions
  const toggleOrderSelection = (orderId: string) => {
    setSelectedOrders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(orderId)) {
        newSet.delete(orderId);
      } else {
        newSet.add(orderId);
      }
      return newSet;
    });
  };

  const toggleSelectAll = () => {
    if (selectedOrders.size === filteredOrders.length) {
      setSelectedOrders(new Set());
    } else {
      setSelectedOrders(new Set(filteredOrders.map(o => o.id)));
    }
  };

  const downloadBulkAWBLabels = async () => {
    const ordersWithLabels = orders.filter(o =>
      selectedOrders.has(o.id) && o.awb_label_path
    );

    if (ordersWithLabels.length === 0) {
      alert('No AWB labels available for selected orders');
      return;
    }

    try {
      // Get order IDs
      const orderIds: string[] = Array.from(selectedOrders);

      // Call backend to merge PDFs
      const blob = await apiService.bulkDownloadAWBLabels(orderIds);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `AWB_Labels_Bulk_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      alert(`Downloaded ${ordersWithLabels.length} AWB labels in a single PDF`);
    } catch (error) {
      console.error('Error downloading bulk AWB labels:', error);
      alert('Failed to download AWB labels. Please try again.');
    }
  };


  // Determine available bulk action
  const activeBulkAction = useMemo(() => {
    if (selectedOrders.size === 0) return null;

    const selected = orders.filter(o => selectedOrders.has(o.id));

    // Priority 1: Pending -> Confirmed
    const pendingOrders = selected.filter(o => o.status === 'Pending');
    if (pendingOrders.length > 0) {
      return { label: `Move ${pendingOrders.length} to Confirmed`, next: 'Confirmed', targetIds: pendingOrders.map(o => o.id) };
    }

    // Priority 2: Confirmed -> Processing
    const confirmedOrders = selected.filter(o => o.status === 'Confirmed');
    if (confirmedOrders.length > 0) {
      return { label: `Move ${confirmedOrders.length} to Processing`, next: 'Processing', targetIds: confirmedOrders.map(o => o.id) };
    }

    // Priority 3: Processing -> Pickup
    const processingOrders = selected.filter(o => o.status === 'Processing');
    if (processingOrders.length > 0) {
      return { label: `Move ${processingOrders.length} to Pickup`, next: 'Ready to Pickup', targetIds: processingOrders.map(o => o.id) };
    }

    // Priority 4: Pickup -> Delivered
    const pickupOrders = selected.filter(o => ['Ready to Pickup', 'Pickup Time Scheduled', 'AWB Generated'].includes(o.status));
    if (pickupOrders.length > 0) {
      return { label: `Mark ${pickupOrders.length} Delivered`, next: 'Delivered', targetIds: pickupOrders.map(o => o.id) };
    }

    return null;
  }, [selectedOrders, orders]);

  const handleBulkMove = async () => {
    if (!activeBulkAction) return;

    if (!window.confirm(`${activeBulkAction.label}?`)) return;

    try {
      setLoading(true);
      // Use targetIds from the derived action, not all selectedOrders
      const promises = activeBulkAction.targetIds.map((id: string) => apiService.updateOrderStatus(id, activeBulkAction.next));
      await Promise.all(promises);

      if (activeStatus === 'Ready to Pickup') fetchDeliveries();
      else fetchOrders();

      setSelectedOrders(new Set());
    } catch (error) {
      console.error("Bulk update failed", error);
      alert("Failed to update status.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 -m-4 sm:-m-6 lg:-m-8 font-sans overflow-hidden relative">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-5 shrink-0">
        <h1 className="text-2xl font-bold text-slate-900">Order Management</h1>
        <p className="text-slate-500 text-sm">Track and manage all customer orders.</p>
      </div>

      {/* Status Tabs */}
      <div className="bg-white border-b border-slate-200 px-6 pt-2 shrink-0">
        <nav className="-mb-px flex space-x-6 overflow-x-auto no-scrollbar">
          {STATUS_TABS.map(status => (
            <button
              key={status}
              onClick={() => setActiveStatus(status)}
              className={`
                whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2
                ${activeStatus === status
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}
              `}
            >
              {status}
              {status !== 'All Orders' && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${activeStatus === status ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-500'}`}>
                  {statusCounts[status] || 0}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Toolbar */}
      <div className="px-6 py-4 flex flex-col gap-4 shrink-0 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Search by Order ID or Customer..."
              className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-sm text-gray-900"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            {activeBulkAction && (
              <button
                onClick={handleBulkMove}
                className="flex items-center gap-2 px-3 py-2 bg-indigo-600 text-white border border-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm"
              >
                <CheckCircle size={16} />
                {activeBulkAction.label} ({selectedOrders.size})
              </button>
            )}
            {activeStatus === 'Ready to Pickup' && selectedOrders.size > 0 && (
              <button
                onClick={downloadBulkAWBLabels}
                className="flex items-center gap-2 px-3 py-2 bg-indigo-600 text-white border border-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
              >
                <Download size={16} />
                Download AWB Labels ({selectedOrders.size})
              </button>
            )}
            <button
              onClick={downloadCSV}
              className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-600 text-sm font-medium hover:bg-slate-50"
            >
              <Download size={16} />
              Export
            </button>
          </div>
        </div>

        {/* Date Filters */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Specific Date */}
          <div className="flex items-center bg-white border border-slate-200 rounded-lg px-2 py-1.5 shadow-sm">
            <span className="text-xs text-slate-500 mr-2 font-medium">Date:</span>
            <input
              type="date"
              value={filterDate}
              onChange={(e) => {
                setFilterDate(e.target.value);
                setFilterMonth('');
                setFilterYear('');
              }}
              className="text-sm outline-none text-slate-700 bg-transparent border-none focus:ring-0 h-5"
            />
          </div>

          <span className="text-xs text-slate-400 font-medium">OR</span>

          {/* Month */}
          <select
            value={filterMonth}
            onChange={(e) => {
              setFilterMonth(e.target.value);
              setFilterDate('');
            }}
            className="bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-sm text-slate-700 outline-none shadow-sm focus:border-indigo-500"
          >
            <option value="">All Months</option>
            {Array.from({ length: 12 }, (_, i) => (
              <option key={i} value={i}>{new Date(0, i).toLocaleString('default', { month: 'long' })}</option>
            ))}
          </select>

          {/* Year */}
          <select
            value={filterYear}
            onChange={(e) => {
              setFilterYear(e.target.value);
              setFilterDate('');
            }}
            className="bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-sm text-slate-700 outline-none shadow-sm focus:border-indigo-500"
          >
            <option value="">All Years</option>
            {availableYears.map(y => <option key={y} value={y}>{y}</option>)}
          </select>

          {/* Clear Filters */}
          {(filterDate || filterMonth || filterYear) && (
            <button
              onClick={clearDateFilters}
              className="text-xs text-red-600 hover:text-red-800 hover:underline ml-auto sm:ml-0 flex items-center gap-1"
            >
              <X size={12} /> Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto px-6 pb-8 pt-4">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-max">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-200">
                <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider w-12">
                  <input
                    type="checkbox"
                    checked={selectedOrders.size === filteredOrders.length && filteredOrders.length > 0}
                    onChange={toggleSelectAll}
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 cursor-pointer"
                  />
                </th>
                <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Order ID</th>
                <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Customer</th>
                {activeStatus !== 'Ready to Pickup' && (
                  <>
                    <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider min-w-[150px]">Product</th>
                    <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Amount</th>
                    <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Payment</th>
                  </>
                )}
                <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                {(activeStatus === 'Processing' || activeStatus === 'Confirmed' || activeStatus === 'Ready to Pickup') && (
                  <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider min-w-[140px]">Dimensions</th>
                )}
                {activeStatus === 'Ready to Pickup' && (
                  <>
                    <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider min-w-[200px]">Contact</th>
                    <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider min-w-[150px]">Items</th>
                    <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-center">AWB Label</th>
                  </>
                )}
                {activeStatus === 'Ready to Pickup' ? (
                  <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-center">Schedule Pickup Time</th>
                ) : (
                  <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-center">Process</th>
                )}
                <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-center">Invoice</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sortedDates.map(date => (
                <React.Fragment key={date}>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    <td colSpan={10} className="py-2.5 px-4 text-xs font-bold text-slate-700 bg-slate-100 border-y border-slate-200 uppercase tracking-wider pl-4">
                      <div className="flex items-center gap-2">
                        <Calendar size={14} className="text-slate-500" />
                        <span>{date}</span>
                      </div>
                    </td>
                  </tr>
                  {groupedOrders[date].map((order) => (
                    <tr key={order.id} className="hover:bg-slate-50/80 transition-colors group">
                      <td className="py-4 px-6">
                        <input
                          type="checkbox"
                          checked={selectedOrders.has(order.id)}
                          onChange={() => toggleOrderSelection(order.id)}
                          className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 cursor-pointer"
                        />
                      </td>
                      <td className="py-4 px-6 font-medium text-indigo-600 text-sm">{order.id}</td>
                      <td className="py-4 px-6 text-sm text-slate-900">
                        <div className="flex items-center gap-2">
                          <span>{order.customer}</span>
                          <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${order.type === 'B2B'
                            ? 'bg-blue-100 text-blue-700 border border-blue-200'
                            : 'bg-green-100 text-green-700 border border-green-200'
                            }`} title={`Customer name fetched from ${order.type} Applications table`}>
                            {order.type}
                          </span>
                        </div>
                      </td>
                      {activeStatus !== 'Ready to Pickup' && (
                        <>
                          <td className="py-4 px-6 text-sm text-slate-600 max-w-[200px]">
                            <div className="flex flex-col gap-1 max-h-[80px] overflow-y-auto custom-scrollbar">
                              {order.productList && order.productList.length > 0 ? (
                                order.productList.map((p: any, i: number) => (
                                  <div key={i} className="text-xs flex justify-between gap-2 border-b border-gray-50 last:border-0 pb-1 last:pb-0">
                                    <span className="truncate flex-1" title={p.name}>{p.name}</span>
                                    <span className="font-semibold text-slate-500 shrink-0">x{p.quantity || 1}</span>
                                  </div>
                                ))
                              ) : (
                                <span className="text-slate-300 italic">-</span>
                              )}
                            </div>
                          </td>
                          <td className="py-4 px-6 text-sm font-bold text-slate-900">₹{order.amount.toLocaleString()}</td>
                          <td className="py-4 px-6">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${order.payment === 'Paid' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                              }`}>
                              {order.payment}
                            </span>
                          </td>
                        </>
                      )}
                      <td className="py-4 px-6">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide border ${getStatusColor(order.status)}`}>
                          {order.status}
                        </span>
                      </td>
                      {(activeStatus === 'Processing' || activeStatus === 'Confirmed' || activeStatus === 'Ready to Pickup') && (
                        <td className="py-4 px-6">
                          {(order.height || order.weight || order.breadth || order.length) ? (
                            <div className="relative group/dim">
                              <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[10px] text-slate-600">
                                <div title="Height"><span className="text-slate-400 font-medium">H:</span> {order.height}</div>
                                <div title="Weight"><span className="text-slate-400 font-medium">W:</span> {order.weight}</div>
                                <div title="Breadth"><span className="text-slate-400 font-medium">B:</span> {order.breadth}</div>
                                <div title="Length"><span className="text-slate-400 font-medium">L:</span> {order.length}</div>
                              </div>
                              <button
                                onClick={() => openDimensionsModal(order.id, order)}
                                className="absolute -top-2 -right-2 p-1 bg-white border border-slate-200 rounded-full text-slate-400 hover:text-indigo-600 hover:border-indigo-200 shadow-sm opacity-0 group-hover/dim:opacity-100 transition-all"
                                title="Edit Dimensions"
                              >
                                <div className="w-3 h-3">
                                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" /><path d="m15 5 4 4" /></svg>
                                </div>
                              </button>
                            </div>
                          ) : (
                            <span className="text-slate-300 text-xs">-</span>
                          )}
                        </td>
                      )}
                      {activeStatus === 'Ready to Pickup' && (
                        <>
                          <td className="py-4 px-6 text-sm text-slate-600">
                            <div className="flex flex-col gap-1">
                              <div className="flex items-center gap-1.5" title="Phone">
                                <Phone size={12} className="text-slate-400" />
                                <span>{order.phone || '-'}</span>
                              </div>
                              <div className="flex items-start gap-1.5" title="Address">
                                <MapPin size={12} className="text-slate-400 mt-0.5 shrink-0" />
                                <span className="line-clamp-2 text-xs">{order.address || '-'}</span>
                              </div>
                            </div>
                          </td>
                          <td className="py-4 px-6 text-sm text-slate-600">
                            <div className="flex flex-col gap-1 max-h-[60px] overflow-y-auto custom-scrollbar">
                              {order.productList && order.productList.length > 0 ? (
                                order.productList.map((item: any, idx: number) => (
                                  <div key={idx} className="flex justify-between items-center text-xs border-b border-slate-100 last:border-0 pb-1 last:pb-0">
                                    <span className="truncate max-w-[100px]" title={item.name || item.product_name || item.product}>{item.name || item.product_name || item.product || `Item #${idx + 1}`}</span>
                                    <span className="font-semibold bg-slate-100 px-1.5 rounded text-[10px]">x{item.quantity || item.qty || 1}</span>
                                  </div>
                                ))
                              ) : (
                                <span className="text-slate-400 text-xs">No items</span>
                              )}
                            </div>
                          </td>
                          <td className="py-4 px-6 text-center">
                            {order.awb_label_path ? (
                              <a
                                href={`${API_BASE_URL}${order.awb_label_path}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-100 text-slate-700 text-xs font-medium rounded-lg hover:bg-slate-200 transition-colors border border-slate-200"
                              >
                                <Download size={14} /> Download
                              </a>
                            ) : (
                              <span className="text-slate-300 text-[10px]">-</span>
                            )}
                          </td>
                        </>
                      )}
                      <td className="py-4 px-6 text-center">
                        {order.status === 'Confirmed' ? (
                          // Logic for Confirmed Orders
                          activeStatus === 'Confirmed' ? (
                            // In Confirmed Tab: Show Add Dimensions / Process Logic
                            (order.height && order.weight && order.breadth && order.length) ? (
                              <button
                                onClick={() => handleProcessToDelivery(order.id)}
                                className="flex items-center justify-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-sm w-full max-w-[140px] mx-auto"
                                title="Process to Delivery"
                              >
                                <PlayCircle size={14} /> Process to Delivery
                              </button>
                            ) : (
                              <button
                                onClick={() => openDimensionsModal(order.id)}
                                className="flex items-center justify-center gap-1 px-3 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition-colors shadow-sm w-full max-w-[140px] mx-auto"
                                title="Add Dimensions"
                              >
                                <Package size={14} /> Add Dimensions
                              </button>
                            )
                          ) : (
                            // In All Orders (or other tabs): Just show "Order Confirmed" badge
                            <span className="flex items-center justify-center gap-1 px-3 py-1.5 bg-emerald-100 text-emerald-700 text-xs font-semibold rounded-lg border border-emerald-200 w-full max-w-[140px] mx-auto">
                              <CheckCircle size={14} /> Order Confirmed
                            </span>
                          )
                        ) : order.status === 'Processing' ? (
                          <button
                            onClick={() => handlePickupOrder(order.id)}
                            className="flex items-center justify-center gap-1 px-3 py-1.5 bg-amber-600 text-white text-xs font-semibold rounded-lg hover:bg-amber-700 transition-colors shadow-sm w-full max-w-[140px] mx-auto"
                            title="Move to Pickup"
                          >
                            <Package size={14} /> Move to Pickup
                          </button>
                        ) : order.status === 'Ready to Pickup' || order.status === 'Pickup Time Scheduled' || order.status === 'AWB Generated' ? (
                          <div className="flex flex-col gap-1.5 w-full max-w-[160px] mx-auto">
                            {order.status === 'Pickup Time Scheduled' ? (
                              <div className="flex flex-col items-center gap-1">
                                <span className="text-[10px] font-medium text-purple-600 bg-purple-50 px-2 py-1 rounded border border-purple-100 w-full text-center">
                                  Scheduled: {new Date(order.schedule_pickup).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
                                </span>
                                <div className="relative w-full">
                                  <input
                                    type="datetime-local"
                                    value={pickupTimes[order.id] || (order.schedule_pickup ? new Date(order.schedule_pickup).toISOString().slice(0, 16) : '')}
                                    onChange={(e) => setPickupTimes({ ...pickupTimes, [order.id]: e.target.value })}
                                    className="w-full px-2 py-1.5 bg-white border border-slate-200 rounded-lg text-[10px] text-slate-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/20"
                                  />
                                </div>
                                <button
                                  onClick={async () => {
                                    const time = pickupTimes[order.id];
                                    if (!time) return;
                                    try {
                                      console.log('Rescheduling pickup for delivery ID:', order.deliveryId, 'Time:', time);
                                      await apiService.updateDeliverySchedule(order.deliveryId, time);
                                      alert('Pickup rescheduled successfully!');
                                      fetchDeliveries();
                                    } catch (error) {
                                      console.error("Failed to reschedule pickup:", error);
                                      alert('Failed to reschedule pickup');
                                    }
                                  }}
                                  className="w-full flex items-center justify-center gap-1 px-3 py-1.5 bg-purple-600 text-white text-xs font-semibold rounded-lg hover:bg-purple-700 transition-colors shadow-sm"
                                >
                                  <Calendar size={12} /> Reschedule
                                </button>
                              </div>
                            ) : (
                              <>
                                <div className="relative">
                                  <input
                                    type="datetime-local"
                                    value={pickupTimes[order.id] || ''}
                                    onChange={(e) => setPickupTimes({ ...pickupTimes, [order.id]: e.target.value })}
                                    className="w-full px-2 py-1.5 bg-white border border-slate-200 rounded-lg text-[10px] text-slate-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/20"
                                  />
                                </div>
                                <button
                                  onClick={async () => {
                                    const time = pickupTimes[order.id];
                                    if (!time) return;
                                    try {
                                      console.log('Scheduling pickup for delivery ID:', order.deliveryId, 'Time:', time);
                                      await apiService.updateDeliverySchedule(order.deliveryId, time);

                                      // Optimistic update
                                      setOrders(prev => prev.map(o =>
                                        o.id === order.id
                                          ? { ...o, status: 'Pickup Time Scheduled', schedule_pickup: time }
                                          : o
                                      ));

                                      alert('Pickup scheduled successfully!');
                                      fetchDeliveries();
                                    } catch (error) {
                                      console.error("Failed to schedule pickup:", error);
                                      alert('Failed to schedule pickup');
                                    }
                                  }}
                                  className="w-full flex items-center justify-center gap-1 px-3 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition-colors shadow-sm"
                                >
                                  <Calendar size={12} /> Schedule Pickup
                                </button>
                              </>
                            )}
                          </div>
                        ) : (order.status === 'Pending' || order.status === 'New' || order.status === 'Created') ? (
                          <button
                            onClick={() => handleConfirmOrder(order.id)}
                            className="flex items-center justify-center gap-1 px-3 py-1.5 bg-violet-600 text-white text-xs font-semibold rounded-lg hover:bg-violet-700 transition-colors shadow-sm w-full max-w-[140px] mx-auto"
                            title="Move to Confirmed"
                          >
                            <CheckCircle size={14} /> Move to Confirmed
                          </button>
                        ) : (
                          <span className="text-slate-300">-</span>
                        )}
                      </td>
                      <td className="py-4 px-6 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => setSelectedOrder(order)}
                            className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                            title="View Invoice"
                          >
                            <Eye size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </React.Fragment>
              ))}
            </tbody>
          </table>
          {filteredOrders.length === 0 && (
            <div className="p-12 text-center flex flex-col items-center">
              <div className="p-4 bg-slate-50 rounded-full mb-3">
                <ShoppingBag size={32} className="text-slate-300" />
              </div>
              <h3 className="text-slate-900 font-medium">No orders found</h3>
              <p className="text-slate-500 text-sm mt-1">Try changing the filters or search term.</p>
            </div>
          )}
        </div>
      </div >

      {/* Invoice Modal */}
      {
        selectedOrder && (
          <div className="fixed inset-0 z-[1000] flex justify-center items-start bg-black/60 backdrop-blur-sm p-4 pt-24 overflow-y-auto">
            <InvoiceModal order={selectedOrder} onClose={() => setSelectedOrder(null)} />
          </div>
        )
      }

      {/* Dimensions Modal */}
      {
        dimensionsModalOpen && (
          <div className="fixed inset-0 z-[1100] flex justify-center items-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
            <div className="bg-white w-full max-w-md rounded-lg shadow-2xl overflow-hidden animate-in fade-in duration-200">
              <div className="px-6 py-3 flex items-center justify-between border-b">
                <h3 className="text-lg font-medium">Add Package Dimensions</h3>
                <button onClick={() => setDimensionsModalOpen(false)} className="text-slate-500 hover:text-slate-700 p-1">
                  <X size={18} />
                </button>
              </div>
              <form onSubmit={handleDimensionsSubmit} className="p-6">
                <div className="grid grid-cols-2 gap-4">
                  <label className="flex flex-col text-sm">
                    <span className="text-xs text-slate-500 mb-1">Height (cm)</span>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      value={dimensionsData.height}
                      onChange={(e) => setDimensionsData(d => ({ ...d, height: e.target.value }))}
                      className="px-3 py-2 border border-slate-200 rounded-lg outline-none text-sm"
                      required
                    />
                  </label>

                  <label className="flex flex-col text-sm">
                    <span className="text-xs text-slate-500 mb-1">Weight (kg)</span>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      value={dimensionsData.weight}
                      onChange={(e) => setDimensionsData(d => ({ ...d, weight: e.target.value }))}
                      className="px-3 py-2 border border-slate-200 rounded-lg outline-none text-sm"
                      required
                    />
                  </label>

                  <label className="flex flex-col text-sm">
                    <span className="text-xs text-slate-500 mb-1">Breadth (cm)</span>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      value={dimensionsData.breadth}
                      onChange={(e) => setDimensionsData(d => ({ ...d, breadth: e.target.value }))}
                      className="px-3 py-2 border border-slate-200 rounded-lg outline-none text-sm"
                      required
                    />
                  </label>

                  <label className="flex flex-col text-sm">
                    <span className="text-xs text-slate-500 mb-1">Length (cm)</span>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      value={dimensionsData.length}
                      onChange={(e) => setDimensionsData(d => ({ ...d, length: e.target.value }))}
                      className="px-3 py-2 border border-slate-200 rounded-lg outline-none text-sm"
                      required
                    />
                  </label>
                </div>

                <div className="mt-6 flex items-center justify-end gap-3">
                  <button type="button" onClick={() => setDimensionsModalOpen(false)} className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 hover:bg-slate-50">
                    Cancel
                  </button>
                  <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">
                    Save Dimensions
                  </button>
                </div>
              </form>
            </div>
          </div>
        )
      }

    </div >
  );
};

const InvoiceModal = ({ order, onClose }: { order: any, onClose: () => void }) => {
  // Robust amount handling: parse string if needed, or use number directly
  const amountValue = typeof order.amount === 'string'
    ? parseFloat(order.amount.replace(/[^0-9.-]+/g, ""))
    : order.amount;

  // Calculate GST dynamically based on stored percentages
  // Default to 0 if not present
  const sgstPercent = Number(order.sgst_percentage) || 0;
  const cgstPercent = Number(order.cgst_percentage) || 0;

  // Total Tax Rate (e.g., 18% = 0.18)
  const totalTaxRate = (sgstPercent + cgstPercent) / 100;

  // Subtotal = Amount / (1 + Tax Rate)
  const subtotal = totalTaxRate > 0 ? (amountValue / (1 + totalTaxRate)) : amountValue;

  // Calculate specific tax amounts
  const sgst = subtotal * (sgstPercent / 100);
  const cgst = subtotal * (cgstPercent / 100);

  // Generate dummy items based on item count
  // Use actual product list if available, otherwise fallback to dummy items
  // Helper to safely parse price
  const parsePrice = (p: any) => {
    if (typeof p === 'number') return p;
    if (typeof p === 'string') return parseFloat(p.replace(/[^0-9.-]+/g, ""));
    return 0;
  };

  const invoiceItems = (order.productList && order.productList.length > 0)
    ? order.productList.map((item: any, i: number) => ({
      id: i + 1,
      desc: (typeof item === 'string' ? item : (item.name || item.product_name || item.product || item.title || item.description || `Product #${item.id || item.product_id || i + 1}`)),
      hsn: item.hsn || item.hsn_code || item.hsnCode || '',
      qty: parseInt(item.quantity || item.qty || item.count || '1'),
      price: parsePrice(item.price || item.unit_price || item.amount || item.selling_price) || (subtotal / (order.productList.length || 1))
    }))
    : Array.from({ length: order.items || 1 }).map((_, i) => ({
      id: i + 1,
      desc: i === 0 ? `Main Product - ${order.type} SKU` : `Accessory / Component Part #${1000 + i}`,
      hsn: '',
      qty: 1,
      price: (subtotal / (order.items || 1))
    }));

  return (
    <div className="bg-white w-full max-w-3xl rounded-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 mb-8">
      {/* Modal Actions */}
      <div className="bg-slate-800 text-white px-6 py-3 flex justify-between items-center print:hidden">
        <span className="font-medium flex items-center gap-2">
          <CreditCard size={16} /> Invoice Preview
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => window.print()}
            className="p-2 hover:bg-slate-700 rounded-md transition-colors text-slate-300 hover:text-white"
            title="Print Invoice"
          >
            <Printer size={18} />
          </button>
          <button
            onClick={onClose}
            className="p-2 bg-red-600 hover:bg-red-700 rounded-md transition-colors text-white"
            title="Close Invoice"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Invoice Content (Printable Area) */}
      <div className="p-8 print:p-0" id="invoice-content">



        {/* Header */}
        <div className="flex justify-between items-start mb-8 border-b border-gray-100 pb-8">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <img src={logo} alt="Logo" className="h-[90px] w-auto" />
              {/* <h1 className="text-2xl font-bold text-gray-900">Sevenxt</h1> */}
            </div>
            <p className="text-sm text-gray-500">123 Innovation Park, Tech CitNo.181/1, Old No.80/1, Swamy Naicken Street,y</p>
            <p className="text-sm text-gray-500">Chintadripet Chennai 600002</p>
            <p className="text-sm text-gray-500 mt-1">GSTIN: 29ABCDE1234F1Z5</p>
          </div>
          <div className="text-right">
            <h2 className="text-4xl font-light text-gray-200 uppercase tracking-widest mb-2">Invoice</h2>
            <p className="text-sm text-gray-500 mb-1">Invoice Number</p>
            <p className="text-lg font-bold text-gray-900 font-mono">INV-{order.order_id || order.id}</p>
            <p className="text-sm text-gray-500 mt-2">Date: {order.date}</p>
            <div className={`mt-2 inline-block px-3 py-1 rounded border text-xs font-bold uppercase ${order.payment === 'Paid' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
              {order.payment}
            </div>
          </div>
        </div>

        {/* Addresses */}
        <div className="grid grid-cols-2 gap-12 mb-8">
          <div>
            <h3 className="text-xs font-bold text-gray-400 uppercase mb-2">Bill To</h3>
            <p className="font-bold text-gray-900 text-lg">{order.customer}</p>
            <div className="text-sm text-gray-600 mt-1 space-y-1">
              <p className="flex items-start gap-2"><MapPin size={14} className="mt-0.5 shrink-0" /> {order.address || 'Address on file'}</p>
              <p className="flex items-center gap-2"><Mail size={14} /> {order.email || 'email@example.com'}</p>
              <p className="flex items-center gap-2"><Phone size={14} /> {order.phone || '+91 98765 43210'}</p>
            </div>

          </div>
          <div className="text-right">
            <h3 className="text-xs font-bold text-gray-400 uppercase mb-2">Order Details</h3>
            <div className="text-sm text-gray-600 space-y-1">
              <p>Order ID: <span className="font-mono font-medium text-gray-900">{order.id}</span></p>
              <p>Order Type: <span className="font-medium text-gray-900">{order.type}</span></p>
              <p>Total Items: <span className="font-medium text-gray-900">{order.items}</span></p>
            </div>
          </div>
        </div>

        {/* AWB Barcode Section - Only show if AWB number exists */}
        {order.awb_number && (
          <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-lg">
            <div className="flex flex-col items-center">
              <h3 className="text-xs font-bold text-gray-500 uppercase mb-3 tracking-wider">AWB Tracking Number</h3>
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <Barcode
                  value={order.awb_number}
                  width={2}
                  height={60}
                  fontSize={14}
                  background="#ffffff"
                  lineColor="#000000"
                  displayValue={true}
                />
              </div>
              <p className="text-xs text-gray-500 mt-2">Scan this barcode for shipment tracking</p>
            </div>
          </div>
        )}

        {/* Line Items */}
        <div className="mb-8">
          <table className="w-full text-left">
            <thead className="bg-gray-50 text-gray-500 text-xs font-bold uppercase">
              <tr>
                <th className="px-4 py-3 rounded-l-md">#</th>
                <th className="px-4 py-3 w-1/2">Items</th>
                <th className="px-4 py-3 text-center">HSN Code</th>
                <th className="px-4 py-3 text-right">Qty</th>
                <th className="px-4 py-3 text-right rounded-r-md">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {invoiceItems.map((item, idx) => (
                <tr key={idx}>
                  <td className="px-4 py-3 text-sm text-gray-400 font-mono">{idx + 1}</td>
                  <td className="px-4 py-3 text-sm text-gray-900 font-medium">{item.desc}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 text-center font-mono">{item.hsn || 'N/A'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 text-right">{item.qty}</td>
                  <td className="px-4 py-3 text-sm text-gray-900 font-bold text-right">₹{(item.price * item.qty).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Totals */}
        <div className="flex justify-end">
          <div className="w-64 space-y-3">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Subtotal</span>
              <span className="font-medium">₹{subtotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            </div>
            <div className="flex justify-between text-sm text-gray-600">
              <span>SGST ({sgstPercent}%)</span>
              <span className="font-medium">₹{sgst.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            </div>
            <div className="flex justify-between text-sm text-gray-600">
              <span>CGST ({cgstPercent}%)</span>
              <span className="font-medium">₹{cgst.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            </div>
            <div className="flex justify-between text-lg font-bold text-gray-900 border-t border-gray-200 pt-3">
              <span>Total</span>
              <span className="text-blue-600">₹{amountValue.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-gray-100 text-center text-xs text-gray-400">
          <p className="mb-1">Thank you for your business!</p>
          <p>This is a computer generated invoice and does not require a physical signature.</p>
        </div>

        {/* Exit Button */}
        <div className="mt-8 flex justify-center print:hidden border-t border-gray-100 pt-6">
          <button
            onClick={onClose}
            className="flex items-center gap-2 px-6 py-2.5 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-all shadow-sm font-medium text-sm"
          >
            <ArrowLeft size={16} />
            Exit to Dashboard
          </button>
        </div>


      </div>
    </div>
  );
};
