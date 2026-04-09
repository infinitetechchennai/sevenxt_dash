import React, { useState, useEffect } from 'react';
import { Package, RefreshCw, CheckCircle, XCircle, Clock, Truck, Search, AlertCircle, Camera, X, ArrowRight, RotateCcw, Copy, Check, Download } from 'lucide-react';
import { apiService, API_BASE_URL } from '../services/api';
import { exportToExcel } from '../utils/excelExport';

interface Exchange {
    id: number;
    order_id: string;
    customer_name: string;
    reason: string;
    description: string | null;
    proof_image_path: string | null;
    product_id: string;
    product_name: string;
    variant_color: string | null;
    quantity: number;
    price: number;
    status: string;
    return_awb_number: string | null;
    return_label_path: string | null;
    return_delivery_status: string | null;
    new_awb_number: string | null;
    new_label_path: string | null;
    new_delivery_status: string | null;
    admin_notes: string | null;
    quality_approved: number | null;
    quality_check_notes: string | null;
    created_at: string;
    updated_at: string | null;
    approved_at: string | null;
    quality_checked_at: string | null;
    completed_at: string | null;
}

const ExchangesView: React.FC = () => {
    const [exchanges, setExchanges] = useState<Exchange[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<string>('All');
    const [searchTerm, setSearchTerm] = useState('');

    // Modals
    const [proofModalOpen, setProofModalOpen] = useState(false);
    const [selectedProof, setSelectedProof] = useState<string | null>(null);
    const [qcModalOpen, setQcModalOpen] = useState(false);
    const [selectedExchange, setSelectedExchange] = useState<Exchange | null>(null);
    const [qcNotes, setQcNotes] = useState('');
    const [processingId, setProcessingId] = useState<number | null>(null);
    const [rejectModalOpen, setRejectModalOpen] = useState(false);
    const [rejectionReason, setRejectionReason] = useState('');
    const [copiedId, setCopiedId] = useState<string | null>(null);

    useEffect(() => {
        fetchExchanges();
    }, [activeTab]);

    const fetchExchanges = async () => {
        try {
            setLoading(true);
            const data = await apiService.fetchExchanges();
            setExchanges(data);
        } catch (error) {
            console.error('Failed to fetch exchanges:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (exchangeId: number) => {
        if (!window.confirm("Are you sure you want to approve this exchange? This will generate a return AWB.")) return;

        setProcessingId(exchangeId);
        try {
            await apiService.approveExchange(exchangeId);
            fetchExchanges();
            alert('Exchange approved! Return AWB generated and sent to customer.');
        } catch (error) {
            console.error('Failed to approve exchange:', error);
            alert('Failed to approve exchange');
        } finally {
            setProcessingId(null);
        }
    };

    const handleQualityCheck = async (approved: boolean) => {
        if (!selectedExchange) return;

        setProcessingId(selectedExchange.id);
        try {
            await apiService.qualityCheckExchange(selectedExchange.id, approved, qcNotes);
            fetchExchanges();
            setQcModalOpen(false);
            setQcNotes('');
            alert(`Quality check ${approved ? 'passed' : 'failed'}!`);
        } catch (error) {
            console.error('Failed to perform quality check:', error);
            alert('Failed to perform quality check');
        } finally {
            setProcessingId(null);
        }
    };

    const handleProcessReplacement = async (exchangeId: number) => {
        if (!window.confirm("Are you sure you want to send a replacement? This will generate a new forward AWB.")) return;

        setProcessingId(exchangeId);
        try {
            await apiService.processExchangeReplacement(exchangeId);
            fetchExchanges();
            alert('Replacement processed! New AWB generated.');
        } catch (error) {
            console.error('Failed to process replacement:', error);
            alert('Failed to process replacement');
        } finally {
            setProcessingId(null);
        }
    };

    const handleRefund = async (exchangeId: number) => {
        if (!window.confirm("Are you sure you want to refund this order instead of exchanging?")) return;

        setProcessingId(exchangeId);
        try {
            await apiService.refundExchange(exchangeId);
            fetchExchanges();
            alert('Exchange marked as Refunded.');
        } catch (error) {
            console.error('Failed to refund exchange:', error);
            alert('Failed to refund exchange');
        } finally {
            setProcessingId(null);
        }
    };

    const handleReject = async () => {
        if (!selectedExchange) return;
        if (!rejectionReason.trim()) {
            alert('Please enter a rejection reason');
            return;
        }

        setProcessingId(selectedExchange.id);
        try {
            await apiService.rejectExchange(selectedExchange.id, rejectionReason);
            fetchExchanges();
            setRejectModalOpen(false);
            setRejectionReason('');
            alert('Exchange rejected! Rejection email sent to customer.');
        } catch (error) {
            console.error('Failed to reject exchange:', error);
            alert('Failed to reject exchange');
        } finally {
            setProcessingId(null);
        }
    };


    const handleViewProof = (path: string) => {
        // Parse if it's a JSON array string like ["url"]
        let imageUrl = path;
        try {
            const urlMatch = path.match(/https?:\/\/[^\s"'\]\\]+/);
            if (urlMatch) {
                imageUrl = urlMatch[0];
            } else {
                let cleanStr = path.trim();
                if (cleanStr.startsWith('"') && cleanStr.endsWith('"')) {
                    cleanStr = cleanStr.substring(1, cleanStr.length - 1);
                }
                if (cleanStr.startsWith('[')) {
                    cleanStr = cleanStr.replace(/\\"/g, '"');
                    const parsed = JSON.parse(cleanStr);
                    imageUrl = Array.isArray(parsed) && parsed.length > 0 ? parsed[0] : cleanStr;
                }
            }
        } catch (e) {
            console.error("Parse proof image url error", e);
            imageUrl = path;
        }

        // Extract the path if it contains /uploads/ or /upload/ to use the correct API_BASE_URL
        // ONLY apply if the URL is relative (doesn't start with http). Plural handles cases where DB has saved an old IP.
        if (imageUrl && !imageUrl.startsWith('http') && !imageUrl.startsWith('data:')) {
            if (imageUrl.includes('/uploads/')) {
                const uploadPath = imageUrl.substring(imageUrl.indexOf('/uploads/'));
                const cleanBaseUrl = API_BASE_URL.replace(/\/+$/, '');
                imageUrl = `${cleanBaseUrl}${uploadPath}`;
            } else if (imageUrl.includes('upload/')) {
                const uploadPath = imageUrl.substring(imageUrl.indexOf('upload/'));
                const cleanBaseUrl = API_BASE_URL.replace(/\/+$/, '');
                imageUrl = `${cleanBaseUrl}/${uploadPath.replace('upload/', 'uploads/')}`;
            } else {
                const cleanBaseUrl = API_BASE_URL.replace(/\/+$/, '');
                imageUrl = imageUrl.startsWith('/') ? imageUrl : `/${imageUrl}`;
                imageUrl = `${cleanBaseUrl}${imageUrl}`;
            }
        }

        setSelectedProof(imageUrl);
        setProofModalOpen(true);
    };

    const getStatusColor = (status: string) => {
        const statusColors: { [key: string]: string } = {
            'Pending': 'bg-yellow-100 text-yellow-800 border-yellow-200',
            'Approved': 'bg-blue-100 text-blue-800 border-blue-200',
            'Return In Transit': 'bg-indigo-100 text-indigo-800 border-indigo-200',
            'Return Received': 'bg-purple-100 text-purple-800 border-purple-200',
            'Quality Check Passed': 'bg-green-100 text-green-800 border-green-200',
            'Quality Check Failed': 'bg-red-100 text-red-800 border-red-200',
            'New Product Dispatched': 'bg-cyan-100 text-cyan-800 border-cyan-200',
            'Completed': 'bg-green-100 text-green-800 border-green-200',
            'Refunded': 'bg-orange-100 text-orange-800 border-orange-200',
            'Rejected': 'bg-red-100 text-red-800 border-red-200',
        };
        return statusColors[status] || 'bg-gray-100 text-gray-800 border-gray-200';
    };

    const tabs = [
        'All',
        'Pending',
        'Approved',
        'Return Received',
        'Completed'
    ];

    const filteredExchanges = exchanges.filter(exchange => {
        const matchesSearch =
            exchange.id.toString().includes(searchTerm) ||
            exchange.order_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
            exchange.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            exchange.product_name.toLowerCase().includes(searchTerm.toLowerCase());

        if (activeTab === 'All') return matchesSearch;
        if (activeTab === 'Completed') return matchesSearch && (exchange.status === 'Completed' || exchange.status === 'Refunded' || exchange.status === 'New Product Dispatched');
        return matchesSearch && exchange.status === activeTab;
    });

    const handleExport = () => {
        const data = filteredExchanges.map(item => ({
            'Exchange ID': item.id,
            'Order ID': item.order_id,
            'Customer': item.customer_name,
            'Product': item.product_name,
            'Reason': item.reason,
            'Status': item.status,
            'Return AWB': item.return_awb_number || '-',
            'New AWB': item.new_awb_number || '-',
            'Date': new Date(item.created_at).toLocaleDateString()
        }));
        exportToExcel(data, `exchanges_${activeTab.toLowerCase().replace(' ', '_')}`, activeTab);
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-gray-900">Exchange Management</h2>
                <p className="text-gray-500 mt-1">Manage product exchanges, returns, and replacements.</p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between h-full">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Pending Requests</p>
                            <h3 className="text-2xl font-bold text-gray-900 mt-1">
                                {exchanges.filter(e => e.status === 'Pending').length}
                            </h3>
                        </div>
                        <div className="p-2 bg-yellow-50 rounded-lg text-yellow-600">
                            <Clock size={20} />
                        </div>
                    </div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between h-full">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Returns In Progress</p>
                            <h3 className="text-2xl font-bold text-gray-900 mt-1">
                                {exchanges.filter(e => ['Approved', 'Return In Transit', 'Return Received'].includes(e.status)).length}
                            </h3>
                        </div>
                        <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
                            <Truck size={20} />
                        </div>
                    </div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between h-full">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Completed Exchanges</p>
                            <h3 className="text-2xl font-bold text-gray-900 mt-1">
                                {exchanges.filter(e => ['Completed', 'New Product Dispatched', 'Refunded'].includes(e.status)).length}
                            </h3>
                        </div>
                        <div className="p-2 bg-green-50 rounded-lg text-green-600">
                            <CheckCircle size={20} />
                        </div>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8 overflow-x-auto no-scrollbar">
                    {tabs.map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`
                                whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors
                                ${activeTab === tab
                                    ? 'border-gray-900 text-gray-900'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                            `}
                        >
                            {tab}
                        </button>
                    ))}
                </nav>
            </div>

            {/* Controls */}
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
                <div className="relative w-full max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search by Order ID, Customer, or Product..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                </div>
                <button
                    onClick={handleExport}
                    className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors shadow-sm text-sm font-medium"
                >
                    <Download size={16} /> Export
                </button>
            </div>

            {/* Exchanges Table */}
            <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Exchange ID</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Order & Customer</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Product</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Reason</th>
                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">Return Delivery</th>
                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">New Exchange</th>
                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">Proof</th>
                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">Action</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {filteredExchanges.map((item) => (
                                <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900">#{item.id}</div>
                                        <div className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                                            <Clock size={10} /> {new Date(item.created_at).toLocaleDateString()}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-semibold text-blue-600 flex items-center gap-2">
                                            {item.order_id}
                                            <button
                                                onClick={() => {
                                                    navigator.clipboard.writeText(item.order_id);
                                                    setCopiedId(item.order_id);
                                                    setTimeout(() => setCopiedId(null), 2000);
                                                }}
                                                className={`transition-colors p-1 rounded ${copiedId === item.order_id ? "text-green-600 bg-green-50"
                                                    : "text-gray-400 hover:text-blue-600 bg-blue-50 hover:bg-blue-100"
                                                    }`}
                                                title="Copy Order ID"
                                            >
                                                {copiedId === item.order_id ? <Check size={12} /> : <Copy size={12} />}
                                            </button>
                                        </div>
                                        <div className="text-sm text-gray-500">{item.customer_name || 'Unknown'}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-sm font-medium text-gray-900">{item.product_name}</div>
                                        <div className="text-xs text-gray-500">
                                            {item.variant_color && `${item.variant_color} • `}
                                            Qty: {item.quantity}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="text-sm font-medium text-gray-700">
                                            {item.reason}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded border text-xs font-medium ${getStatusColor(item.status)}`}>
                                            {item.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        {item.return_awb_number ? (
                                            <div className="space-y-1">
                                                <div className="text-xs font-mono text-gray-600 bg-gray-50 px-2 py-1 rounded">
                                                    {item.return_awb_number}
                                                </div>
                                                {item.return_delivery_status ? (
                                                    <div className="flex items-center gap-1 justify-center">
                                                        <Truck size={12} className="text-orange-600" />
                                                        <span className="text-xs font-medium text-orange-600">
                                                            {item.return_delivery_status}
                                                        </span>
                                                    </div>
                                                ) : (
                                                    <span className="text-xs text-gray-400">Pending Pickup</span>
                                                )}
                                            </div>
                                        ) : (
                                            <span className="text-gray-400 text-xs">-</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        {item.new_awb_number ? (
                                            <div className="space-y-1">
                                                <div className="text-xs font-mono text-gray-600 bg-gray-50 px-2 py-1 rounded">
                                                    {item.new_awb_number}
                                                </div>
                                                {item.new_delivery_status ? (
                                                    <div className="flex items-center gap-1 justify-center">
                                                        <Truck size={12} className="text-green-600" />
                                                        <span className="text-xs font-medium text-green-600">
                                                            {item.new_delivery_status}
                                                        </span>
                                                    </div>
                                                ) : (
                                                    <span className="text-xs text-gray-400">Pending Dispatch</span>
                                                )}
                                            </div>
                                        ) : (
                                            <span className="text-gray-400 text-xs">-</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        {item.proof_image_path ? (
                                            <button
                                                onClick={() => handleViewProof(item.proof_image_path!)}
                                                className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-medium transition-colors"
                                            >
                                                <Camera size={14} /> View
                                            </button>
                                        ) : (
                                            <span className="text-gray-400 text-xs">No proof</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        <div className="flex items-center justify-center gap-2">
                                            {item.status === 'Pending' && (
                                                <>
                                                    <button
                                                        onClick={() => handleApprove(item.id)}
                                                        disabled={processingId === item.id}
                                                        className="px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 text-xs font-bold transition-colors"
                                                    >
                                                        {processingId === item.id ? 'Processing...' : 'Approve'}
                                                    </button>
                                                    <button
                                                        onClick={() => {
                                                            setSelectedExchange(item);
                                                            setRejectModalOpen(true);
                                                        }}
                                                        disabled={processingId === item.id}
                                                        className="px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-700 text-xs font-bold transition-colors"
                                                    >
                                                        Reject
                                                    </button>
                                                </>
                                            )}

                                            {item.status === 'Return Received' && (
                                                <>
                                                    <button
                                                        onClick={() => handleProcessReplacement(item.id)}
                                                        disabled={processingId === item.id}
                                                        className="px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 text-xs font-bold transition-colors flex items-center gap-1"
                                                        title="Process Exchange - Generate New AWB"
                                                    >
                                                        <RefreshCw size={12} /> Exchange
                                                    </button>
                                                    <button
                                                        onClick={() => handleRefund(item.id)}
                                                        disabled={processingId === item.id}
                                                        className="px-3 py-1.5 bg-orange-500 text-white rounded hover:bg-orange-600 text-xs font-bold transition-colors flex items-center gap-1"
                                                        title="Out of Stock - Refund Customer"
                                                    >
                                                        <RotateCcw size={12} /> Out of Stock
                                                    </button>
                                                </>
                                            )}

                                            {item.status === 'Quality Check Passed' && (
                                                <>
                                                    <button
                                                        onClick={() => handleProcessReplacement(item.id)}
                                                        disabled={processingId === item.id}
                                                        className="px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 text-xs font-bold transition-colors flex items-center gap-1"
                                                        title="Send Replacement"
                                                    >
                                                        <RefreshCw size={12} /> Exchange
                                                    </button>
                                                    <button
                                                        onClick={() => handleRefund(item.id)}
                                                        disabled={processingId === item.id}
                                                        className="px-3 py-1.5 bg-orange-500 text-white rounded hover:bg-orange-600 text-xs font-bold transition-colors flex items-center gap-1"
                                                        title="Refund (Out of Stock)"
                                                    >
                                                        <RotateCcw size={12} /> Refund
                                                    </button>
                                                </>
                                            )}

                                            {['Completed', 'New Product Dispatched', 'Refunded', 'Rejected', 'Quality Check Failed'].includes(item.status) && (
                                                <span className="text-gray-400 text-xs italic">No actions</span>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                            {filteredExchanges.length === 0 && (
                                <tr>
                                    <td colSpan={9} className="px-6 py-10 text-center text-gray-500">
                                        No exchange requests found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Proof Image Modal */}
            {proofModalOpen && selectedProof && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
                    <div className="bg-white rounded-xl overflow-hidden max-w-lg w-full relative shadow-2xl">
                        <button
                            onClick={() => setProofModalOpen(false)}
                            className="absolute top-2 right-2 bg-black/50 hover:bg-black/70 text-white p-1 rounded-full transition-colors z-10"
                        >
                            <X size={20} />
                        </button>
                        <div className="bg-gray-100 p-1 flex items-center justify-center min-h-[300px]">
                            <img
                                src={selectedProof}
                                alt="Proof"
                                className="max-w-full max-h-[60vh] object-contain rounded"
                            />
                        </div>
                    </div>
                </div>
            )}

            {/* Quality Check Modal */}
            {qcModalOpen && selectedExchange && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in zoom-in-95 duration-200">
                    <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                            <h3 className="font-bold text-lg text-gray-900">Quality Check</h3>
                            <button onClick={() => setQcModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-6">
                            <p className="text-sm text-gray-600 mb-4">
                                Inspect the returned item. If approved, you can proceed to exchange or refund.
                            </p>
                            <div className="mb-4">
                                <label className="block text-xs font-bold text-gray-700 uppercase mb-1">QC Notes</label>
                                <textarea
                                    className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                                    rows={3}
                                    placeholder="Condition of the returned item..."
                                    value={qcNotes}
                                    onChange={(e) => setQcNotes(e.target.value)}
                                ></textarea>
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={() => handleQualityCheck(false)}
                                    className="flex-1 px-4 py-2 bg-red-100 text-red-700 hover:bg-red-200 rounded-lg text-sm font-bold transition-colors"
                                >
                                    ✗ Fail
                                </button>
                                <button
                                    onClick={() => handleQualityCheck(true)}
                                    className="flex-1 px-4 py-2 bg-green-600 text-white hover:bg-green-700 rounded-lg text-sm font-bold transition-colors"
                                >
                                    ✓ Pass
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Reject Exchange Modal */}
            {rejectModalOpen && selectedExchange && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in zoom-in-95 duration-200">
                    <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-red-50">
                            <h3 className="font-bold text-lg text-gray-900">Reject Exchange Request</h3>
                            <button onClick={() => {
                                setRejectModalOpen(false);
                                setRejectionReason('');
                            }} className="text-gray-400 hover:text-gray-600">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-6">
                            <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                                <p className="text-sm text-yellow-800">
                                    <strong>Order:</strong> {selectedExchange.order_id}<br />
                                    <strong>Product:</strong> {selectedExchange.product_name}<br />
                                    <strong>Customer:</strong> {selectedExchange.customer_name}
                                </p>
                            </div>
                            <p className="text-sm text-gray-600 mb-4">
                                Please provide a reason for rejecting this exchange request. This reason will be sent to the customer via email.
                            </p>
                            <div className="mb-4">
                                <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Rejection Reason *</label>
                                <textarea
                                    className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-red-500 outline-none resize-none"
                                    rows={4}
                                    placeholder="e.g., Product is not damaged, normal wear and tear, does not meet exchange criteria..."
                                    value={rejectionReason}
                                    onChange={(e) => setRejectionReason(e.target.value)}
                                    required
                                ></textarea>
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={() => {
                                        setRejectModalOpen(false);
                                        setRejectionReason('');
                                    }}
                                    className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 hover:bg-gray-200 rounded-lg text-sm font-bold transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleReject}
                                    disabled={!rejectionReason.trim() || processingId === selectedExchange.id}
                                    className="flex-1 px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded-lg text-sm font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {processingId === selectedExchange.id ? 'Rejecting...' : 'Reject & Send Email'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ExchangesView;
