import React, { useState, useEffect } from 'react';
import { Search, RotateCcw, AlertCircle, CheckCircle, XCircle, DollarSign, Calendar, FileText, Camera, QrCode, X, Mail, Smartphone, Eye, Send, MessageSquare, Download, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';
import { apiService, API_BASE_URL } from '../services/api';
import { exportToExcel } from '../utils/excelExport';

export const RefundsView: React.FC = () => {
    const [activeTab, setActiveTab] = useState('All Refunds');
    const [searchTerm, setSearchTerm] = useState('');
    const [refunds, setRefunds] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    // Modal & Processing States
    const [proofModalOpen, setProofModalOpen] = useState(false);
    const [selectedProof, setSelectedProof] = useState<string | null>(null);
    const [proofImages, setProofImages] = useState<string[]>([]);
    const [activeImageIndex, setActiveImageIndex] = useState<number>(0);
    const [proofError, setProofError] = useState(false);
    const [qrModalOpen, setQrModalOpen] = useState(false);
    const [selectedQRRefund, setSelectedQRRefund] = useState<any>(null);
    const [processingId, setProcessingId] = useState<number | null>(null);

    // Rejection Modal States
    const [rejectModalOpen, setRejectModalOpen] = useState(false);
    const [rejectId, setRejectId] = useState<number | null>(null);
    const [rejectReason, setRejectReason] = useState('');

    // View Reason Modal State
    const [viewReasonModalOpen, setViewReasonModalOpen] = useState(false);
    const [viewReasonText, setViewReasonText] = useState('');

    const tabs = [
        'All Refunds',
        'Pending',
        'Approved',
        'Rejected',
        'Completed'
    ];

    // Fetch refunds on mount and when tab changes
    useEffect(() => {
        fetchRefunds();
    }, [activeTab]);

    const fetchRefunds = async () => {
        try {
            setLoading(true);
            const status = activeTab === 'All Refunds' ? undefined : activeTab;
            const data = await apiService.fetchRefunds(status);
            setRefunds(data);
        } catch (error) {
            console.error("Failed to fetch refunds:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleApproveAndGenerateQR = async (id: number) => {
        setProcessingId(id);

        try {
            await apiService.updateRefundStatus(id, 'Approved');
            alert(`Refund Approved! \n\n1. QR Code Generated containing product & damage details.\n2. Email sent to customer.\n3. App notification pushed.`);
            fetchRefunds();
        } catch (error) {
            console.error("Failed to approve refund:", error);
            alert('Failed to approve refund. Please try again.');
        } finally {
            setProcessingId(null);
        }
    };

    const handleRejectClick = (id: number) => {
        setRejectId(id);
        setRejectReason('');
        setRejectModalOpen(true);
    };

    const confirmReject = async () => {
        if (rejectId) {
            try {
                await apiService.rejectRefund(rejectId, rejectReason);
                alert(`Refund Rejected.\n\nReason sent to customer: "${rejectReason}"`);
                setRejectModalOpen(false);
                setRejectId(null);
                setRejectReason('');
                fetchRefunds();
            } catch (error) {
                console.error("Failed to reject refund:", error);
                alert('Failed to reject refund. Please try again.');
            }
        }
    };

    const parseProofImages = (path: any): string[] => {
        if (!path) return [];
        if (Array.isArray(path)) {
            return path
                .map(item => (typeof item === 'string' ? item.trim() : ''))
                .filter(url => url.startsWith('http'));
        }
        let raw = String(path).trim();
        if (!raw) return [];

        try {
            if (raw.startsWith('"') && raw.endsWith('"') && (raw.includes('[') || raw.includes('http'))) {
                raw = raw.slice(1, -1);
            }
            if (raw.startsWith('[')) {
                raw = raw.replace(/\\"/g, '"');
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed)) {
                    const urls = parsed
                        .map(item => (typeof item === 'string' ? item.trim() : ''))
                        .filter(url => url.startsWith('http'));
                    if (urls.length > 0) return urls;
                }
            }
            const matched = raw.match(/https?:\/\/[^\s"'\]\\]+/g);
            if (matched && matched.length > 0) {
                return matched;
            }
        } catch (e) {
            console.error('Failed to parse proof images:', e);
        }
        return raw.startsWith('http') ? [raw] : [];
    };

    const handleViewProof = (imageUrl: string) => {
        const images = parseProofImages(imageUrl);
        if (images.length === 0) return;

        setProofImages(images);
        setActiveImageIndex(0);
        setSelectedProof(images[0]);
        setProofError(false);
        setProofModalOpen(true);
    };

    const handleNextImage = () => {
        if (proofImages.length <= 1) return;
        const nextIndex = (activeImageIndex + 1) % proofImages.length;
        setActiveImageIndex(nextIndex);
        setSelectedProof(proofImages[nextIndex]);
        setProofError(false);
    };

    const handlePrevImage = () => {
        if (proofImages.length <= 1) return;
        const prevIndex = (activeImageIndex - 1 + proofImages.length) % proofImages.length;
        setActiveImageIndex(prevIndex);
        setSelectedProof(proofImages[prevIndex]);
        setProofError(false);
    };

    const handleSelectImage = (index: number) => {
        setActiveImageIndex(index);
        setSelectedProof(proofImages[index]);
        setProofError(false);
    };

    const handleViewQR = (refund: any) => {
        setSelectedQRRefund(refund);
        setQrModalOpen(true);
    };

    const handleViewRejectionReason = (reason: string) => {
        setViewReasonText(reason);
        setViewReasonModalOpen(true);
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'Completed': return 'bg-green-100 text-green-800 border-green-200';
            case 'Approved': return 'bg-blue-100 text-blue-800 border-blue-200';
            case 'Pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            case 'Rejected': return 'bg-red-100 text-red-800 border-red-200';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getReturnStatusColor = (status: string | null) => {
        if (!status) return 'bg-gray-100 text-gray-500 border-gray-200';
        const upperStatus = status.toUpperCase();
        if (upperStatus.includes('DELIVERED')) return 'bg-green-100 text-green-800 border-green-200';
        if (upperStatus.includes('TRANSIT')) return 'bg-blue-100 text-blue-800 border-blue-200';
        if (upperStatus.includes('PICKED')) return 'bg-purple-100 text-purple-800 border-purple-200';
        if (upperStatus.includes('MANIFEST')) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        return 'bg-gray-100 text-gray-700 border-gray-200';
    };

    const filteredRefunds = refunds.filter(item => {
        const matchesSearch =
            item.id?.toString().includes(searchTerm.toLowerCase()) ||
            item.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            item.customer_name?.toLowerCase().includes(searchTerm.toLowerCase());

        if (activeTab === 'All Refunds') return matchesSearch;
        return matchesSearch && item.status === activeTab;
    });

    const handleExport = () => {
        const data = filteredRefunds.map(item => ({
            'Refund ID': item.id,
            'Order ID': item.order_number,
            'Customer': item.customer_name,
            'Reason': item.reason,
            'Amount': item.amount,
            'Status': item.status,
            'Return Status': item.return_delivery_status || '-',
            'Date': new Date(item.created_at).toLocaleDateString()
        }));
        exportToExcel(data, `refunds_${activeTab.toLowerCase().replace(' ', '_')}`, activeTab);
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-gray-900">Refund Management</h2>
                <p className="text-gray-500 mt-1">Review damage proofs, approve returns, and auto-generate QR codes.</p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between h-full">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Pending Amount</p>
                            <h3 className="text-2xl font-bold text-gray-900 mt-1">
                                ₹{refunds.filter(r => r.status === 'Pending').reduce((sum, r) => sum + parseFloat(r.amount || 0), 0).toLocaleString()}
                            </h3>
                        </div>
                        <div className="p-2 bg-yellow-50 rounded-lg text-yellow-600">
                            <DollarSign size={20} />
                        </div>
                    </div>
                    <div className="mt-4 text-xs text-yellow-600 font-medium flex items-center gap-1">
                        <AlertCircle size={12} /> {refunds.filter(r => r.status === 'Pending').length} requests pending approval
                    </div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between h-full">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Approved Today</p>
                            <h3 className="text-2xl font-bold text-gray-900 mt-1">
                                ₹{refunds.filter(r => r.status === 'Approved').reduce((sum, r) => sum + parseFloat(r.amount || 0), 0).toLocaleString()}
                            </h3>
                        </div>
                        <div className="p-2 bg-green-50 rounded-lg text-green-600">
                            <CheckCircle size={20} />
                        </div>
                    </div>
                    <div className="mt-4 text-xs text-green-600 font-medium flex items-center gap-1">
                        <RotateCcw size={12} /> {refunds.filter(r => r.status === 'Approved').length} refunds approved
                    </div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between h-full">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Total Rejected</p>
                            <h3 className="text-2xl font-bold text-gray-900 mt-1">{refunds.filter(r => r.status === 'Rejected').length}</h3>
                        </div>
                        <div className="p-2 bg-red-50 rounded-lg text-red-600">
                            <XCircle size={20} />
                        </div>
                    </div>
                    <div className="mt-4 text-xs text-gray-400 font-medium">
                        This month
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
                        placeholder="Search by Order ID, Customer or Refund ID..."
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

            {/* Refunds Table */}
            <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Refund ID</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Order & Customer</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Reason</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Amount</th>
                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">Return Status</th>
                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">Proof</th>
                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">Action</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {filteredRefunds.map((item) => (
                                <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900">#{item.id}</div>
                                        <div className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                                            <Calendar size={10} /> {new Date(item.created_at).toLocaleDateString()}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-semibold text-blue-600">{item.order_number || '-'}</div>
                                        <div className="text-sm text-gray-500">{item.customer_name || 'Unknown'}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="text-sm font-medium text-gray-700">
                                            {item.reason}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                                        ₹{parseFloat(item.amount).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded border text-xs font-medium ${getStatusColor(item.status)}`}>
                                            {item.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        {item.return_delivery_status ? (
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded border text-xs font-medium ${getReturnStatusColor(item.return_delivery_status)}`}>
                                                {item.return_delivery_status}
                                            </span>
                                        ) : (
                                            <span className="text-gray-400 text-xs">-</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        {item.proof_image_path ? (
                                            (() => {
                                                const proofs = parseProofImages(item.proof_image_path);
                                                return proofs.length > 0 ? (
                                                    <button
                                                        onClick={() => handleViewProof(item.proof_image_path)}
                                                        className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-semibold transition-colors shadow-sm"
                                                    >
                                                        <Camera size={14} className="text-blue-600" />
                                                        <span>View</span>
                                                        {proofs.length > 1 && (
                                                            <span className="bg-blue-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none">
                                                                {proofs.length}
                                                            </span>
                                                        )}
                                                    </button>
                                                ) : (
                                                    <span className="text-gray-400 text-xs">No proof</span>
                                                );
                                            })()
                                        ) : (
                                            <span className="text-gray-400 text-xs">No proof</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        {item.status === 'Pending' ? (
                                            <div className="flex items-center justify-center gap-2">
                                                <button
                                                    onClick={() => handleApproveAndGenerateQR(item.id)}
                                                    disabled={processingId === item.id}
                                                    className={`flex items-center gap-1 px-3 py-1.5 rounded text-xs font-bold text-white transition-all shadow-sm ${processingId === item.id
                                                        ? 'bg-gray-400 cursor-not-allowed'
                                                        : 'bg-gray-900 hover:bg-gray-800'
                                                        }`}
                                                    title="Approve & Generate QR"
                                                >
                                                    {processingId === item.id ? (
                                                        <RotateCcw size={14} className="animate-spin" />
                                                    ) : (
                                                        <QrCode size={14} />
                                                    )}
                                                    {processingId === item.id ? 'Processing...' : 'Approve'}
                                                </button>
                                                <button
                                                    onClick={() => handleRejectClick(item.id)}
                                                    disabled={!!processingId}
                                                    className="px-3 py-1.5 bg-white border border-red-200 text-red-600 rounded hover:bg-red-50 transition-colors text-xs font-bold flex items-center gap-1"
                                                    title="Reject Refund"
                                                >
                                                    <X size={14} /> Reject
                                                </button>
                                            </div>
                                        ) : (
                                            <div className="flex items-center justify-center text-gray-400">
                                                {item.status === 'Approved' ? (
                                                    <span className="text-xs text-blue-600 font-medium">Approved</span>
                                                ) : item.status === 'Completed' ? (
                                                    <span className="text-xs text-green-600 font-medium">Completed</span>
                                                ) : (
                                                    <span className="text-xs text-red-500 font-medium">Rejected</span>
                                                )}
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {filteredRefunds.length === 0 && (
                                <tr>
                                    <td colSpan={8} className="px-6 py-10 text-center text-gray-500">
                                        No refund requests found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Proof Image Modal */}
            {proofModalOpen && selectedProof && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in duration-200">
                    <div className="bg-white rounded-2xl overflow-hidden max-w-2xl w-full relative shadow-2xl flex flex-col max-h-[90vh]">
                        {/* Header */}
                        <div className="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between bg-gray-50/90">
                            <div className="flex items-center gap-2">
                                <Camera size={18} className="text-blue-600" />
                                <h3 className="font-bold text-sm text-gray-900">
                                    Customer Proof Images
                                </h3>
                                {proofImages.length > 1 && (
                                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700">
                                        {activeImageIndex + 1} of {proofImages.length}
                                    </span>
                                )}
                            </div>
                            <div className="flex items-center gap-2">
                                <a
                                    href={selectedProof}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 hover:underline px-2.5 py-1 rounded bg-blue-50 transition-colors"
                                    title="Open original full resolution image in new tab"
                                >
                                    <ExternalLink size={13} /> Full Size
                                </a>
                                <button
                                    onClick={() => setProofModalOpen(false)}
                                    className="text-gray-400 hover:text-gray-600 p-1.5 rounded-full hover:bg-gray-200 transition-colors"
                                >
                                    <X size={18} />
                                </button>
                            </div>
                        </div>

                        {/* Main Image Stage */}
                        <div className="bg-slate-950 relative flex items-center justify-center min-h-[320px] max-h-[58vh] p-3 overflow-hidden select-none">
                            {proofError ? (
                                <div className="flex flex-col items-center gap-3 py-16 text-gray-400">
                                    <Camera size={44} className="opacity-40" />
                                    <p className="text-sm font-medium text-gray-300">Image no longer available</p>
                                    <p className="text-xs text-gray-500">This proof cannot be retrieved or the link has expired.</p>
                                </div>
                            ) : (
                                <img
                                    src={selectedProof}
                                    alt={`Proof ${activeImageIndex + 1}`}
                                    className="max-w-full max-h-[54vh] object-contain rounded-lg shadow-lg transition-all duration-150"
                                    onError={() => setProofError(true)}
                                />
                            )}

                            {/* Left / Right Arrow Controls */}
                            {proofImages.length > 1 && (
                                <>
                                    <button
                                        onClick={handlePrevImage}
                                        className="absolute left-3 top-1/2 -translate-y-1/2 bg-black/60 hover:bg-black/90 text-white p-2.5 rounded-full backdrop-blur-sm transition-all hover:scale-110 active:scale-95 shadow-xl"
                                        title="Previous image"
                                    >
                                        <ChevronLeft size={22} />
                                    </button>
                                    <button
                                        onClick={handleNextImage}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 bg-black/60 hover:bg-black/90 text-white p-2.5 rounded-full backdrop-blur-sm transition-all hover:scale-110 active:scale-95 shadow-xl"
                                        title="Next image"
                                    >
                                        <ChevronRight size={22} />
                                    </button>
                                </>
                            )}
                        </div>

                        {/* Thumbnail Carousel Bar */}
                        {proofImages.length > 1 && (
                            <div className="px-4 py-3 bg-gray-900 border-t border-gray-800 flex items-center gap-2.5 overflow-x-auto">
                                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mr-1 shrink-0">
                                    All ({proofImages.length}):
                                </span>
                                {proofImages.map((imgUrl, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => handleSelectImage(idx)}
                                        className={`relative shrink-0 rounded-lg overflow-hidden transition-all duration-150 border-2 ${
                                            activeImageIndex === idx
                                                ? 'border-blue-500 scale-105 shadow-md shadow-blue-500/30'
                                                : 'border-transparent opacity-60 hover:opacity-100 hover:border-gray-500'
                                        }`}
                                    >
                                        <img
                                            src={imgUrl}
                                            alt={`Thumb ${idx + 1}`}
                                            className="w-14 h-14 object-cover"
                                            onError={(e) => {
                                                (e.currentTarget as HTMLElement).style.display = 'none';
                                            }}
                                        />
                                        <span className="absolute bottom-0 right-0 bg-black/75 text-[10px] text-white px-1 font-mono rounded-tl">
                                            {idx + 1}
                                        </span>
                                    </button>
                                ))}
                            </div>
                        )}

                        {/* Footer Notes */}
                        <div className="p-3.5 bg-white border-t border-gray-100 text-xs text-gray-500 flex items-center justify-between">
                            <span>
                                Uploaded by customer as proof of damage/return reason.
                            </span>
                            {proofImages.length > 1 && (
                                <span className="text-gray-400 text-[11px]">
                                    Click arrows or thumbnails to browse all images
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Reject Reason Input Modal */}
            {rejectModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in zoom-in-95 duration-200">
                    <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                            <h3 className="font-bold text-lg text-gray-900 flex items-center gap-2">
                                <XCircle size={20} className="text-red-600" /> Reject Refund
                            </h3>
                            <button onClick={() => setRejectModalOpen(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-6">
                            <p className="text-sm text-gray-600 mb-4">
                                Please provide a reason for rejecting this refund request. This explanation will be sent directly to the customer via email.
                            </p>

                            <div className="mb-4">
                                <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Reason for Rejection</label>
                                <textarea
                                    className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none resize-none transition-shadow"
                                    rows={4}
                                    placeholder="e.g. Item returned does not match the original product, Warranty seal broken..."
                                    value={rejectReason}
                                    onChange={(e) => setRejectReason(e.target.value)}
                                    autoFocus
                                ></textarea>
                            </div>

                            <div className="flex justify-end gap-3 pt-2">
                                <button
                                    onClick={() => setRejectModalOpen(false)}
                                    className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm font-medium transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={confirmReject}
                                    disabled={!rejectReason.trim()}
                                    className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-bold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-sm transition-all"
                                >
                                    <Send size={14} /> Send & Reject
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
