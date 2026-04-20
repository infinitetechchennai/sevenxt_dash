import React, { useState, useEffect } from 'react';
import {
    Users, ShoppingCart, IndianRupee, RefreshCcw,
    Truck, AlertTriangle, TrendingUp, ArrowRight
} from 'lucide-react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend
} from 'recharts';
import axios from 'axios';
import { fetchProducts } from '../services/api';
import { Product } from '../types';

import { API_BASE_URL } from '../services/api';

// API Configuration
const API_BASE = `${API_BASE_URL}/api/v1/dashboard`;

// Updated Card Component: Rupee symbol updated, decorative line/trend removed
const Card = ({ title, value, icon: Icon, iconBg, onClick }: any) => (
    <div
        onClick={onClick}
        className={`bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between h-full transition-all hover:shadow-md ${onClick ? 'cursor-pointer hover:bg-gray-50' : ''}`}
    >
        <div className="flex justify-between items-start text-slate-900">
            <div>
                <p className="text-sm text-gray-500 font-medium">{title}</p>
                <h3 className="text-2xl font-bold mt-1">
                    {/* Handling Rupee symbol for revenue, otherwise showing raw value */}
                    {title.toLowerCase().includes('revenue') ? `${value.toLocaleString()}` : value}
                </h3>
            </div>
            <div className={`p-3 rounded-lg ${iconBg} text-white shadow-sm`}>
                <Icon size={20} />
            </div>
        </div>
    </div>
);

// Helper for default labels in Pie Charts
const renderCustomizedPieLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, name }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + (radius + 30) * Math.cos(-midAngle * RADIAN);
    const y = cy + (radius + 30) * Math.sin(-midAngle * RADIAN);

    return (
        <text x={x} y={y} fill="#4B5563" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize="10" fontWeight="bold">
            {name} ({Math.round(percent * 100)}%)
        </text>
    );
};

export const DashboardView: React.FC<{ onNavigate: (view: string) => void }> = ({ onNavigate }) => {
    const [timeRange, setTimeRange] = useState<'Today' | 'Weekly' | 'Monthly' | 'All'>('Monthly');
    const [stats, setStats] = useState<any>(null);
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadDashboardData = async () => {
            setLoading(true);
            try {
                const [sRes, pRes] = await Promise.all([
                    axios.get(`${API_BASE}/overview?timeframe=${timeRange}`),
                    fetchProducts()
                ]);
                setStats(sRes.data);
                setProducts(pRes);
            } catch (e) {
                console.error("Dashboard Workflow Error:", e);
            } finally {
                setLoading(false);
            }
        };
        loadDashboardData();
    }, [timeRange]);

    const lowStockProducts = products.filter(p => p.stock < 30).sort((a, b) => a.stock - b.stock);

    if (loading || !stats) return <div className="p-20 text-center font-bold text-slate-400 animate-pulse">Initializing Dashboard...</div>;

    return (
        <div className="space-y-6 animate-in fade-in zoom-in-95 duration-300">
            {/* Header Section */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
                    <p className="text-gray-500 mt-1">Live operational overview.</p>
                </div>
                <div className="flex gap-2 bg-white p-1 rounded-lg border border-gray-200 shadow-sm">
                    {(['Today', 'Weekly', 'Monthly', 'All'] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setTimeRange(tab)}
                            className={`px-4 py-1.5 rounded-md text-xs font-semibold transition-all ${timeRange === tab ? 'bg-gray-900 text-white shadow' : 'text-gray-600 hover:bg-gray-50'}`}
                        >
                            {tab}
                        </button>
                    ))}
                </div>
            </div>

            {/* KPI Cards Workflow */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <Card title="Total Revenue" value={stats.revenue.value} icon={IndianRupee} iconBg="bg-blue-600" onClick={() => onNavigate('FINANCE')} />
                <Card title="Total Orders" value={stats.orders.value} icon={ShoppingCart} iconBg="bg-violet-600" onClick={() => onNavigate('ORDERS')} />
                <Card title="B2B Users" value={stats.b2b_users.value} icon={Users} iconBg="bg-emerald-600" onClick={() => onNavigate('USERS')} />
                <Card title="B2C Users" value={stats.b2c_users.value} icon={Users} iconBg="bg-teal-600" onClick={() => onNavigate('USERS')} />
                <Card title="Refunds" value={stats.refunds.value} icon={RefreshCcw} iconBg="bg-rose-600" onClick={() => onNavigate('REFUNDS')} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Analytics Chart */}
                <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <h3 className="text-lg font-semibold text-gray-900 mb-6">B2B vs B2C Analytics</h3>
                    <div className="h-[320px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={stats.chart} margin={{ top: 30, right: 20, left: 10, bottom: 10 }}>
                                <defs>
                                    <linearGradient id="colorB2B" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3B82F6" stopOpacity={0.1} /><stop offset="95%" stopColor="#3B82F6" stopOpacity={0} /></linearGradient>
                                    <linearGradient id="colorB2C" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10B981" stopOpacity={0.1} /><stop offset="95%" stopColor="#10B981" stopOpacity={0} /></linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F3F4F6" />
                                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                                <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                                <Area type="monotone" dataKey="b2b" name="B2B" stroke="#3B82F6" strokeWidth={3} fill="url(#colorB2B)" label={{ fill: '#3B82F6', fontSize: 10, fontWeight: 'bold', position: 'top' }} />
                                <Area type="monotone" dataKey="b2c" name="B2C" stroke="#10B981" strokeWidth={3} fill="url(#colorB2C)" label={{ fill: '#10B981', fontSize: 10, fontWeight: 'bold', position: 'top' }} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>



                {/* Delivery Stats */}
                <div
                    onClick={() => onNavigate('DELIVERY')}
                    className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col">

                    <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
                        <Truck className="text-blue-600" size={20} /> Delivery Stats
                    </h3>
                    <div className="flex-1 relative min-h-[250px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={stats.porter}
                                    cx="50%"
                                    cy="45%"
                                    innerRadius={50}
                                    outerRadius={75}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {stats.porter.map((e: any, i: number) => (<Cell key={i} fill={e.color} />))}
                                </Pie>
                                <Tooltip />
                                <Legend
                                    verticalAlign="bottom"
                                    height={36}
                                    iconType="circle"
                                    formatter={(value, entry: any) => `${value} (${entry.payload.value})`}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Tables Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="p-6 border-b font-bold flex justify-between text-gray-900 text-sm uppercase tracking-wider">
                        <span>Stock Alerts</span>
                        <span className="bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full text-xs">{lowStockProducts.length}</span>
                    </div>
                    <table className="w-full text-sm">
                        <tbody className="divide-y divide-gray-100">
                            {lowStockProducts.slice(0, 5).map(p => (
                                <tr key={p.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 text-gray-700 font-medium">{p.name}</td>
                                    <td className="px-6 py-4 text-right"><span className="text-rose-600 font-bold">{p.stock} units left</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="p-6 border-b font-bold text-gray-900 text-sm uppercase tracking-wider">Best Sellers</div>
                    <table className="w-full text-sm">
                        <tbody className="divide-y divide-gray-100">
                            {stats.bestSellers.map((p: any, i: number) => (
                                <tr key={i} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 font-medium text-gray-700">{p.name}</td>
                                    <td className="px-6 py-4 text-right font-bold text-indigo-600">
                                        ₹{Math.round(p.revenue).toLocaleString()}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
