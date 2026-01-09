
import React, { useState, useEffect } from 'react';
import {
    Truck, MapPin, Key, Shield, Activity,
    Save, RefreshCw, Eye, Search, User, Phone, FileText, DollarSign, FileClock, BarChart3, X, Plus, Clock, Navigation
} from 'lucide-react';
import {
    PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend
} from 'recharts';

import { PorterRateRule, PorterZone } from '../types';
import { API_BASE_URL } from '../services/api';

export const PorterView: React.FC = () => {
    // Tabs focused on Local Operations - only Live Ops now
    const [activeTab, setActiveTab] = useState<'Live Ops'>('Live Ops');
    const [searchTerm, setSearchTerm] = useState('');

    // Local state for Rules and Zones
    const [rules, setRules] = useState<PorterRateRule[]>([]);
    const [zones, setZones] = useState<PorterZone[]>([]);

    // Modal States
    const [showRuleModal, setShowRuleModal] = useState(false);
    const [showZoneModal, setShowZoneModal] = useState(false);

    // Form States
    const [newRule, setNewRule] = useState<Partial<PorterRateRule>>({
        vehicleType: '', baseFare: 0, perKmRate: 0, minDistance: 0, weightLimit: ''
    });
    const [newZone, setNewZone] = useState<Partial<PorterZone>>({
        name: '', city: 'Chennai', pincodes: '', status: 'Active'
    });

    // Mock Booking Form
    const [bookingOrder, setBookingOrder] = useState('');
    const [bookingType, setBookingType] = useState('2 Wheeler');

    // Local deliveries (picked up & in Chennai)
    const [outstationDeliveries, setOutstationDeliveries] = useState<any[]>([]);

    useEffect(() => {
        // Fetch local deliveries from backend (city=Chennai filter applied on backend)
        const fetchLocalDeliveries = async () => {
            try {
                const base = API_BASE_URL;
                const token = localStorage.getItem('auth_token');
                const res = await fetch(`${base}/api/v1/orders/deliveries?city=Chennai`, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...(token ? { Authorization: `Bearer ${token}` } : {}),
                    },
                });
                if (!res.ok) return;
                const data = await res.json();

                // Filter for active statuses - normalize status by replacing spaces with underscores
                const activeStatuses = ['READY_TO_PICKUP', 'AWB_GENERATED', 'PICKED_UP', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED'];
                const filtered = (data || []).filter((d: any) => {
                    // Normalize status: replace spaces with underscores and convert to uppercase
                    const status = (d.delivery_status || '').toString().toUpperCase().replace(/\s+/g, '_');
                    return activeStatuses.includes(status);
                });

                setOutstationDeliveries(filtered);
            } catch (e) {
                console.error('Failed to load local deliveries', e);
            }
        };

        fetchLocalDeliveries();
    }, []);

    const filteredLogs = outstationDeliveries.filter((item: any) =>
        (item.order_number || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.customer_name || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getStatusStyle = (status: string) => {
        switch (status) {
            case 'Delivered': return 'bg-green-100 text-green-800 border-green-200';
            case 'On Route': return 'bg-blue-100 text-blue-800 border-blue-200 animate-pulse';
            case 'Assigned': return 'bg-indigo-100 text-indigo-800 border-indigo-200';
            case 'Searching': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            case 'Cancelled': return 'bg-red-100 text-red-800 border-red-200';
            default: return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    const handleAddRule = () => {
        if (newRule.vehicleType && newRule.weightLimit) {
            const rule: PorterRateRule = {
                id: `rule_${Date.now()}`,
                vehicleType: newRule.vehicleType || 'Unknown',
                baseFare: Number(newRule.baseFare),
                perKmRate: Number(newRule.perKmRate),
                minDistance: Number(newRule.minDistance),
                weightLimit: newRule.weightLimit || '0kg'
            };
            setRules([...rules, rule]);
            setShowRuleModal(false);
            setNewRule({ vehicleType: '', baseFare: 0, perKmRate: 0, minDistance: 0, weightLimit: '' });
        }
    };

    const handleAddZone = () => {
        if (newZone.name && newZone.pincodes) {
            const zone: PorterZone = {
                id: `zone_${Date.now()}`,
                name: newZone.name || 'New Zone',
                city: newZone.city || 'Chennai',
                pincodes: newZone.pincodes || '',
                status: (newZone.status as 'Active' | 'Inactive') || 'Active'
            };
            setZones([...zones, zone]);
            setShowZoneModal(false);
            setNewZone({ name: '', city: 'Chennai', pincodes: '', status: 'Active' });
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 font-sans">
            {/* Top Header & Navigation */}
            <div className="flex flex-col space-y-4">
                <div className="flex items-center justify-between bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                            <MapPin className="text-indigo-600" /> Delivery (Local)
                        </h2>
                        <p className="text-gray-500 mt-1">Manage intra-city logistics for B2B & B2C orders via Delivery.</p>
                    </div>

                </div>

                {/* Navigation Tabs - Only Live Operations */}
                <div className="bg-white px-6 rounded-xl border border-gray-200 shadow-sm">
                    <nav className="-mb-px flex space-x-8 overflow-x-auto no-scrollbar">
                        <button
                            className="whitespace-nowrap py-4 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 border-indigo-600 text-indigo-600"
                        >
                            <Activity size={18} /> Live Operations
                        </button>
                    </nav>
                </div>
            </div>

            {/* --- LIVE OPS TAB --- */}
            <div className="space-y-6 animate-in fade-in">
                {/* Local Deliveries */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
                        <h3 className="font-bold text-gray-900">Local Deliveries (Chennai)</h3>
                        <p className="text-sm text-gray-500 mt-1">Showing all Chennai deliveries</p>
                    </div>
                    <div className="divide-y divide-gray-100">
                        {outstationDeliveries.length === 0 ? (
                            <div className="p-6 text-center text-sm text-gray-500">No local deliveries found.</div>
                        ) : (
                            outstationDeliveries.map((d) => (
                                <div key={d.id || d.awb_number || d.order_id} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                                    <div>
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="font-bold text-gray-900">{d.order_number || d.order_id || d.awb_number}</span>
                                            <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 text-[10px] font-bold rounded uppercase">Local</span>
                                        </div>
                                        <div className="text-sm text-gray-500 flex items-center gap-2">
                                            <MapPin size={14} /> {d.full_address || d.customer_name || 'Address not available'}
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-bold text-gray-900">{d.customer_name || d.phone || '-'}</div>
                                        <div className="text-xs text-blue-600 font-medium">{(d.delivery_status || '').replace(/_/g, ' ')}</div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>





            {/* --- MODALS --- */}
            {/* Add Rule Modal */}
            {showRuleModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-6 animate-in fade-in zoom-in-95">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-gray-900">Add Rate Rule</h3>
                            <button onClick={() => setShowRuleModal(false)} className="text-gray-500 hover:text-gray-700"><X size={20} /></button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Vehicle</label>
                                <input
                                    className="w-full border rounded-md px-3 py-2 text-sm text-gray-900 bg-white"
                                    value={newRule.vehicleType}
                                    onChange={(e) => setNewRule({ ...newRule, vehicleType: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Capacity</label>
                                <input
                                    className="w-full border rounded-md px-3 py-2 text-sm text-gray-900 bg-white"
                                    value={newRule.weightLimit}
                                    onChange={(e) => setNewRule({ ...newRule, weightLimit: e.target.value })}
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Base (₹)</label>
                                    <input
                                        type="number"
                                        className="w-full border rounded-md px-3 py-2 text-sm text-gray-900 bg-white"
                                        value={newRule.baseFare}
                                        onChange={(e) => setNewRule({ ...newRule, baseFare: parseFloat(e.target.value) })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">/Km (₹)</label>
                                    <input
                                        type="number"
                                        className="w-full border rounded-md px-3 py-2 text-sm text-gray-900 bg-white"
                                        value={newRule.perKmRate}
                                        onChange={(e) => setNewRule({ ...newRule, perKmRate: parseFloat(e.target.value) })}
                                    />
                                </div>
                            </div>
                        </div>
                        <div className="mt-6 flex justify-end gap-3">
                            <button onClick={() => setShowRuleModal(false)} className="px-4 py-2 border rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">Cancel</button>
                            <button onClick={handleAddRule} className="px-4 py-2 bg-gray-900 text-white rounded-md text-sm font-medium hover:bg-gray-800">Save</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Add Zone Modal */}
            {showZoneModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-6 animate-in fade-in zoom-in-95">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-gray-900">Add Zone</h3>
                            <button onClick={() => setShowZoneModal(false)} className="text-gray-500 hover:text-gray-700"><X size={20} /></button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Zone Name</label>
                                <input
                                    className="w-full border rounded-md px-3 py-2 text-sm text-gray-900 bg-white"
                                    value={newZone.name}
                                    onChange={(e) => setNewZone({ ...newZone, name: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Pincodes</label>
                                <textarea
                                    className="w-full border rounded-md px-3 py-2 text-sm text-gray-900 h-20 resize-none bg-white"
                                    value={newZone.pincodes}
                                    onChange={(e) => setNewZone({ ...newZone, pincodes: e.target.value })}
                                />
                            </div>
                        </div>
                        <div className="mt-6 flex justify-end gap-3">
                            <button onClick={() => setShowZoneModal(false)} className="px-4 py-2 border rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">Cancel</button>
                            <button onClick={handleAddZone} className="px-4 py-2 bg-gray-900 text-white rounded-md text-sm font-medium hover:bg-gray-800">Save</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};