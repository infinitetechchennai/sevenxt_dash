
import React, { useState } from 'react';
import {
    Truck, MapPin, Key, Shield, Activity,
    Save, RefreshCw, Eye, Search, User, Phone, FileText, DollarSign, FileClock, BarChart3, X, Plus, Clock, Navigation
} from 'lucide-react';
import {
    PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend
} from 'recharts';
import {
    MOCK_LOCAL_TRIPS, MOCK_PORTER_RULES,
    MOCK_PORTER_ZONES, MOCK_PORTER_PERFORMANCE
} from '../constants';
import { PorterRateRule, PorterZone } from '../types';

export const PorterView: React.FC = () => {
    // Tabs focused on Local Operations
    const [activeTab, setActiveTab] = useState<'Live Ops' | 'Book Rider' | 'History' | 'Settings'>('Live Ops');
    const [searchTerm, setSearchTerm] = useState('');

    // Local state for Rules and Zones
    const [rules, setRules] = useState<PorterRateRule[]>(MOCK_PORTER_RULES);
    const [zones, setZones] = useState<PorterZone[]>(MOCK_PORTER_ZONES);

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

    const filteredLogs = MOCK_LOCAL_TRIPS.filter(item =>
        item.orderId.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.customerName.toLowerCase().includes(searchTerm.toLowerCase())
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
                            <MapPin className="text-indigo-600" /> Porter (Local)
                        </h2>
                        <p className="text-gray-500 mt-1">Manage intra-city logistics for B2B & B2C orders via Porter.</p>
                    </div>
                    <div className="flex items-center gap-2 bg-indigo-50 px-3 py-1.5 rounded-full border border-indigo-100">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        <span className="text-xs font-bold text-indigo-700">Porter API Connected</span>
                    </div>
                </div>

                {/* Navigation Tabs */}
                <div className="bg-white px-6 rounded-xl border border-gray-200 shadow-sm">
                    <nav className="-mb-px flex space-x-8 overflow-x-auto no-scrollbar">
                        <button
                            onClick={() => setActiveTab('Live Ops')}
                            className={`whitespace-nowrap py-4 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${activeTab === 'Live Ops' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            <Activity size={18} /> Live Operations
                        </button>
                        <button
                            onClick={() => setActiveTab('Book Rider')}
                            className={`whitespace-nowrap py-4 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${activeTab === 'Book Rider' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            <Plus size={18} /> Book Rider
                        </button>
                        <button
                            onClick={() => setActiveTab('History')}
                            className={`whitespace-nowrap py-4 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${activeTab === 'History' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            {/* <FileClock size={18} /> Trip History */}
                        </button>
                        <button
                            onClick={() => setActiveTab('Settings')}
                            className={`whitespace-nowrap py-4 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${activeTab === 'Settings' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            {/* <Key size={18} /> Configuration */}
                        </button>
                    </nav>
                </div>
            </div>

            {/* --- LIVE OPS TAB --- */}
            {activeTab === 'Live Ops' && (
                <div className="space-y-6 animate-in fade-in">
                    {/* Active Stats */}
                    <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex flex-col justify-center">
                            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Active Riders</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">8 <span className="text-sm font-normal text-gray-500">on duty</span></p>
                        </div>
                        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex flex-col justify-center">
                            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Active Orders</p>
                            <p className="text-3xl font-bold text-indigo-600 mt-1">12 <span className="text-sm font-normal text-gray-500">in transit</span></p>
                        </div>
                        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex flex-col justify-center">
                            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Avg Pickup Time</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">18 <span className="text-sm font-normal text-gray-500">mins</span></p>
                        </div>
                        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex flex-col justify-center">
                            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Wallet Balance</p>
                            <p className="text-3xl font-bold text-emerald-600 mt-1">₹4,500</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Active Trips List */}
                        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
                                <h3 className="font-bold text-gray-900">Active Trips in Chennai</h3>
                            </div>
                            <div className="divide-y divide-gray-100">
                                {MOCK_LOCAL_TRIPS.slice(0, 3).map((trip) => (
                                    <div key={trip.id} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="font-bold text-gray-900">{trip.id}</span>
                                                <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 text-[10px] font-bold rounded uppercase">{trip.vehicleType}</span>
                                            </div>
                                            <div className="text-sm text-gray-500 flex items-center gap-2">
                                                <MapPin size={14} /> {trip.dropLocation}
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="font-bold text-gray-900">{trip.driverName}</div>
                                            <div className="text-xs text-blue-600 font-medium">{trip.status}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Performance Chart */}
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                            <h3 className="font-bold text-gray-900 mb-6 text-center">Delivery Success Rate</h3>
                            <div className="h-[250px] w-full relative">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={MOCK_PORTER_PERFORMANCE}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={60}
                                            outerRadius={80}
                                            paddingAngle={5}
                                            dataKey="value"
                                        >
                                            {MOCK_PORTER_PERFORMANCE.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} strokeWidth={0} />
                                            ))}
                                        </Pie>
                                        <RechartsTooltip />
                                        <Legend verticalAlign="bottom" height={36} iconType="circle" />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* --- BOOK RIDER TAB --- */}
            {activeTab === 'Book Rider' && (
                <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm animate-in fade-in">
                    <div className="max-w-3xl mx-auto">
                        <div className="text-center mb-8">
                            <h2 className="text-xl font-bold text-gray-900">Book a Porter Rider</h2>
                            <p className="text-gray-500 text-sm mt-1">Assign immediate pickup for local Chennai orders.</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Order ID</label>
                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            placeholder="e.g. ORD-5521"
                                            className="flex-1 px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-gray-900"
                                            value={bookingOrder}
                                            onChange={e => setBookingOrder(e.target.value)}
                                        />
                                        <button className="px-4 py-2 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200">Check</button>
                                    </div>
                                </div>

                                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                                    <h4 className="text-xs font-bold text-gray-500 uppercase mb-3">Pickup Location</h4>
                                    <p className="text-sm font-medium text-gray-900">Warehouse A (Anna Nagar)</p>
                                    <p className="text-xs text-gray-500 mt-1">Plot 45, 2nd Avenue, Chennai - 600040</p>
                                </div>

                                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                                    <h4 className="text-xs font-bold text-gray-500 uppercase mb-3">Drop Location</h4>
                                    <p className="text-sm text-gray-400 italic">Please enter Order ID to fetch drop location...</p>
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Select Vehicle</label>
                                    <div className="grid grid-cols-2 gap-3">
                                        {['2 Wheeler', '3 Wheeler', 'Tata Ace', 'Pickup 8ft'].map(v => (
                                            <div
                                                key={v}
                                                onClick={() => setBookingType(v)}
                                                className={`p-3 rounded-lg border cursor-pointer transition-all text-center ${bookingType === v
                                                    ? 'border-indigo-600 bg-indigo-50 text-indigo-700 shadow-sm'
                                                    : 'border-gray-200 hover:border-gray-300 text-gray-600'
                                                    }`}
                                            >
                                                <Truck size={20} className="mx-auto mb-1" />
                                                <span className="text-xs font-bold">{v}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="bg-indigo-900 text-white p-5 rounded-xl shadow-lg">
                                    <div className="flex justify-between items-center mb-4">
                                        <span className="text-indigo-200 text-sm">Estimated Cost</span>
                                        <span className="text-2xl font-bold">₹0.00</span>
                                    </div>
                                    <button
                                        onClick={() => alert("Booking Confirmed! Rider assigned.")}
                                        className="w-full py-3 bg-white text-indigo-900 font-bold rounded-lg hover:bg-indigo-50 transition-colors"
                                    >
                                        Confirm Booking
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* --- TRIP HISTORY TAB --- */}
            {activeTab === 'History' && (
                <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden animate-in fade-in">
                    <div className="p-6 border-b border-gray-200 flex justify-between items-center">
                        <h3 className="text-lg font-semibold text-gray-900">Local Delivery Logs</h3>
                        <div className="relative w-64">
                            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search Trip ID..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 text-gray-900"
                            />
                        </div>
                    </div>
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50 text-gray-500 text-xs font-bold uppercase">
                            <tr>
                                <th className="px-6 py-3 text-left">Date</th>
                                <th className="px-6 py-3 text-left">Trip ID</th>
                                <th className="px-6 py-3 text-left">Customer / Company</th>
                                <th className="px-6 py-3 text-left">Destination</th>
                                <th className="px-6 py-3 text-left">Vehicle</th>
                                <th className="px-6 py-3 text-center">Status</th>
                                <th className="px-6 py-3 text-right">Cost</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 bg-white">
                            {filteredLogs.map((log) => (
                                <tr key={log.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 text-sm text-gray-500">{log.date}</td>
                                    <td className="px-6 py-4 font-mono font-medium text-indigo-600 text-sm">{log.id}</td>
                                    <td className="px-6 py-4 text-sm text-gray-900">
                                        {log.customerName}
                                        <div className={`text-[10px] inline-block px-1.5 rounded ml-2 font-bold ${log.type === 'B2B' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>
                                            {log.type}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-900">{log.dropLocation}</td>
                                    <td className="px-6 py-4 text-sm text-gray-600">{log.vehicleType}</td>
                                    <td className="px-6 py-4 text-center">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded border text-xs font-medium ${getStatusStyle(log.status)}`}>
                                            {log.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right font-bold text-gray-900">₹{log.cost}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* --- SETTINGS TAB --- */}
            {activeTab === 'Settings' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-in fade-in">
                    {/* Rate Rules */}
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                        <div className="p-5 border-b border-gray-200 flex justify-between items-center bg-gray-50">
                            <h3 className="font-bold text-gray-900">Rate Card (Chennai)</h3>
                            <button onClick={() => setShowRuleModal(true)} className="text-xs bg-gray-900 text-white px-3 py-1.5 rounded hover:bg-gray-800">Add Rule</button>
                        </div>
                        <table className="w-full text-sm text-left">
                            <thead className="bg-white text-gray-500 border-b border-gray-100">
                                <tr>
                                    <th className="px-4 py-3">Vehicle</th>
                                    <th className="px-4 py-3 text-right">Base</th>
                                    <th className="px-4 py-3 text-right">/Km</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {rules.map(rule => (
                                    <tr key={rule.id}>
                                        <td className="px-4 py-3 font-medium text-gray-900">{rule.vehicleType}</td>
                                        <td className="px-4 py-3 text-right">₹{rule.baseFare}</td>
                                        <td className="px-4 py-3 text-right">₹{rule.perKmRate}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Zones */}
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                        <div className="p-5 border-b border-gray-200 flex justify-between items-center bg-gray-50">
                            <h3 className="font-bold text-gray-900">Service Zones</h3>
                            <button onClick={() => setShowZoneModal(true)} className="text-xs bg-gray-900 text-white px-3 py-1.5 rounded hover:bg-gray-800">Add Zone</button>
                        </div>
                        <div className="divide-y divide-gray-100 p-4">
                            {zones.map(zone => (
                                <div key={zone.id} className="py-3">
                                    <div className="flex justify-between">
                                        <span className="font-bold text-gray-900">{zone.name}</span>
                                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded font-bold">{zone.status}</span>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1 font-mono truncate">{zone.pincodes}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* API Config */}
                    <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                        <h3 className="font-bold text-gray-900 mb-4">API Configuration</h3>
                        <div className="flex gap-4 items-end">
                            <div className="flex-1">
                                <label className="block text-xs font-medium text-gray-700 mb-1">API Key</label>
                                <input type="password" value="pk_test_xxxxxxxx" readOnly className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-md text-white text-sm" />
                            </div>
                            <div className="flex-1">
                                <label className="block text-xs font-medium text-gray-700 mb-1">Client ID</label>
                                <input type="text" value="client_778899" readOnly className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-md text-white text-sm" />
                            </div>
                            <button className="px-4 py-2 bg-gray-900 text-white rounded-md text-sm font-medium hover:bg-gray-800">Save</button>
                        </div>
                    </div>
                </div>
            )}

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
