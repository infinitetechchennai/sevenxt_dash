
import React, { useState, useEffect } from 'react';
import { Package, Search, ExternalLink, Truck, MapPin, Loader2, AlertCircle, Download } from 'lucide-react';
import { API_BASE_URL } from '../services/api';
import { exportToExcel } from '../utils/excelExport';

const TABS = [
    { id: 'all', label: 'All Shipments', icon: <Package size={18} /> },
];

export const DeliveryView: React.FC = () => {
    const [activeTab, setActiveTab] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');

    // Real Data States
    const [deliveries, setDeliveries] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Fetch deliveries from the database on load
    useEffect(() => {
        const loadDeliveries = async () => {
            try {
                setLoading(true);
                // Fetch outstation deliveries (exclude Chennai) AND filter for Picked Up+ statuses
                const response = await fetch(`${API_BASE_URL}/api/v1/orders/deliveries?exclude_city=Chennai&min_status=PICKED_UP`);

                if (!response.ok) {
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                setDeliveries(data);
                setError(null);
            } catch (err: any) {
                console.error("Fetch Error:", err);
                setError("Failed to connect to the delivery database.");
            } finally {
                setLoading(false);
            }
        };
        loadDeliveries();
    }, []);



    const filteredDeliveries = deliveries.filter(item => {
        // Requirement 1: City is NOT Chennai (Backend handles this too, but double check)
        const isOutstation = item.city?.toLowerCase() !== 'chennai';

        // Requirement 2: Search matching
        const matchesSearch =
            item.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            item.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            item.awb_number?.toLowerCase().includes(searchTerm.toLowerCase());

        return isOutstation && matchesSearch;
    });

    // // Filter Logic: Show only 'PICKED_UP' (or 'Picked up') and 'NOT Chennai'
    // const filteredDeliveries = deliveries.filter(item => {
    //     // Requirement 1: Check delivery_status
    //     // Note: Normalizing to uppercase to catch 'PICKED_UP' or 'Picked up'
    //     const status = item.delivery_status?.toUpperCase();
    //     const isPickedUp = status === 'PICKED_UP' || status === 'PICKED UP';

    //     // Requirement 2: City is NOT Chennai (Outstation)
    //     const isOutstation = item.city?.toLowerCase() !== 'chennai';

    //     // Requirement 3: Search matching
    //     const matchesSearch =
    //         item.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    //         item.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    //         item.awb_number?.toLowerCase().includes(searchTerm.toLowerCase());

    //     return isPickedUp && isOutstation && matchesSearch;
    // });

    const handleExport = () => {
        const data = filteredDeliveries.map(item => ({
            'Order ID': item.order_number,
            'Customer': item.customer_name,
            'City': item.city,
            'State': item.state,
            'AWB Number': item.awb_number,
            'Status': item.delivery_status,
            'Last Updated': item.updated_at ? new Date(item.updated_at).toLocaleDateString() : 'N/A'
        }));
        exportToExcel(data, 'delivery_outstation_export', 'Outstation Ships');
    };

    return (
        <div className="flex flex-col h-full bg-gray-50 -m-4 sm:-m-6 lg:-m-8 font-sans">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-8 py-6 shrink-0">
                <h1 className="text-2xl font-bold text-gray-900">Delivery (Outstation)</h1>
                <p className="text-gray-500 mt-1 text-sm">Real-time status tracking for long-distance shipments.</p>
            </div>

            {/* Tabs */}
            <div className="bg-white border-b border-gray-200 px-8 shrink-0">
                <nav className="-mb-px flex space-x-8">
                    {TABS.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`
                                group whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2
                                ${activeTab === tab.id
                                    ? 'border-gray-900 text-gray-900'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                            `}
                        >
                            {tab.label}
                        </button>
                    ))}
                </nav>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto p-8">
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-20">
                        <Loader2 className="w-10 h-10 animate-spin text-blue-600 mb-4" />
                        <p className="text-gray-500">Loading delivery records...</p>
                    </div>
                ) : error ? (
                    <div className="flex items-center gap-2 p-4 bg-red-50 text-red-700 rounded-lg border border-red-100 max-w-2xl mx-auto">
                        <AlertCircle size={20} /> {error}
                    </div>
                ) : activeTab === 'all' && (
                    <div className="max-w-6xl mx-auto space-y-6">
                        <div className="flex items-center justify-between">
                            <div className="relative w-72">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                <input
                                    type="text"
                                    placeholder="Search Order ID or AWB..."
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm bg-white outline-none focus:ring-2 focus:ring-gray-400"
                                    value={searchTerm}
                                    onChange={e => setSearchTerm(e.target.value)}
                                />
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={handleExport}
                                    className="flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                                >
                                    <Download size={14} /> Export
                                </button>
                                <div className="text-xs font-semibold text-gray-500 bg-gray-100 px-3 py-1.5 rounded-full">
                                    {filteredDeliveries.length} Shipments Found
                                </div>
                            </div>
                        </div>

                        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                            <table className="w-full text-left border-collapse">
                                <thead className="bg-gray-50 text-xs font-bold text-gray-500 uppercase">
                                    <tr>
                                        <th className="px-6 py-4">Order ID</th>
                                        <th className="px-6 py-4">Customer</th>
                                        <th className="px-6 py-4">Destination</th>
                                        <th className="px-6 py-4">AWB Number</th>
                                        <th className="px-6 py-4">Status</th>
                                        <th className="px-6 py-4 text-right">Last Updated</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100 text-sm">
                                    {filteredDeliveries.map(item => (
                                        <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4 font-bold text-blue-600">{item.order_number}</td>
                                            <td className="px-6 py-4 font-medium text-gray-900">{item.customer_name}</td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-1 text-gray-700">
                                                    <MapPin size={14} className="text-gray-400" />
                                                    {item.city}, {item.state}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 font-mono text-gray-600">
                                                {item.awb_number || 'Pending'}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-green-50 text-green-700 border border-green-100">
                                                    {item.delivery_status}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right text-gray-500 text-xs">
                                                {item.updated_at ? new Date(item.updated_at).toLocaleDateString() : 'N/A'}
                                            </td>
                                        </tr>
                                    ))}
                                    {filteredDeliveries.length === 0 && (
                                        <tr>
                                            <td colSpan={6} className="px-6 py-16 text-center text-gray-500">
                                                <div className="flex flex-col items-center">
                                                    <Truck size={40} className="text-gray-300 mb-2" />
                                                    <p>No outstation orders are currently in "Picked Up" status.</p>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

