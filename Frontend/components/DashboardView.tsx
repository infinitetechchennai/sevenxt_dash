<<<<<<< HEAD
import React, { useState, useEffect } from 'react';
=======
import React, { useState, useMemo, useEffect } from 'react';
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
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

<<<<<<< HEAD
// API Configuration
const API_BASE = `${API_BASE_URL}/api/v1/dashboard`;
=======
const DASHBOARD_DATA = {

    Today: {
        revenue: { value: '₹45,230', trend: 'up', percent: '+12%', subtext: 'vs yesterday' },
        orders: { value: '124', trend: 'up', percent: '+5%', subtext: 'vs yesterday' },
        users: { value: '45', trend: 'up', percent: '+8%', subtext: 'new signups' },
        refunds: { value: '2', trend: 'down', percent: '-50%', subtext: 'vs yesterday' },
        chart: [
            { name: '8 AM', B2B: 4000, B2C: 2400 },
            { name: '10 AM', B2B: 3000, B2C: 1398 },
            { name: '12 PM', B2B: 2000, B2C: 9800 },
            { name: '2 PM', B2B: 2780, B2C: 3908 },
            { name: '4 PM', B2B: 1890, B2C: 4800 },
            { name: '6 PM', B2B: 2390, B2C: 3800 },
            { name: '8 PM', B2B: 3490, B2C: 4300 },
        ],
        porter: [
            { name: 'On Time', value: 95, color: '#10B981' },
            { name: 'Late', value: 5, color: '#EF4444' },
        ],
        bestSellers: [
            { id: 1, name: 'Wireless Mouse M2', category: 'Accessories', sales: 42, revenue: '₹18,900', growth: '+5%' },
            { id: 2, name: 'USB-C Cable', category: 'Accessories', sales: 38, revenue: '₹11,400', growth: '+2%' },
        ]
    },
    Weekly: {
        revenue: { value: '₹5,68,900', trend: 'up', percent: '+8%', subtext: 'vs last week' },
        orders: { value: '1,245', trend: 'up', percent: '+14%', subtext: 'vs last week' },
        users: { value: '340', trend: 'up', percent: '+12%', subtext: 'new signups' },
        refunds: { value: '15', trend: 'down', percent: '-10%', subtext: 'vs last week' },
        chart: [
            { name: 'Mon', B2B: 12000, B2C: 8400 },
            { name: 'Tue', B2B: 15000, B2C: 9300 },
            { name: 'Wed', B2B: 18000, B2C: 12800 },
            { name: 'Thu', B2B: 16780, B2C: 10908 },
            { name: 'Fri', B2B: 21890, B2C: 14800 },
            { name: 'Sat', B2B: 24390, B2C: 18800 },
            { name: 'Sun', B2B: 19490, B2C: 15300 },
        ],
        porter: [
            { name: 'On Time', value: 88, color: '#10B981' },
            { name: 'Late', value: 12, color: '#EF4444' },
        ],
        bestSellers: [
            { id: 1, name: 'Gaming Laptop Ryzen 7', category: 'Computers', sales: 24, revenue: '₹21,59,976', growth: '+15%' },
            { id: 2, name: '5G Smartphone 256GB', category: 'Mobile', sales: 45, revenue: '₹29,24,955', growth: '+8%' },
            { id: 3, name: 'Smart Home Security Camera', category: 'Smart Home', sales: 89, revenue: '₹2,22,411', growth: '+12%' },
        ]
    },
    Monthly: {
        revenue: { value: '₹25,68,900', trend: 'up', percent: '+15%', subtext: 'vs last month' },
        orders: { value: '8,456', trend: 'up', percent: '+23%', subtext: 'vs last month' },
        users: { value: '1,240', trend: 'up', percent: '+18%', subtext: 'new signups' },
        refunds: { value: '45', trend: 'down', percent: '-3%', subtext: 'vs last month' },
        chart: [
            { name: 'Week 1', B2B: 45000, B2C: 24000 },
            { name: 'Week 2', B2B: 52000, B2C: 28000 },
            { name: 'Week 3', B2B: 48000, B2C: 32000 },
            { name: 'Week 4', B2B: 61000, B2C: 45000 },
        ],
        porter: [
            { name: 'On Time', value: 82, color: '#10B981' },
            { name: 'Late', value: 18, color: '#EF4444' },
        ],
        bestSellers: [
            { id: 1, name: 'Ultra HD 4K Smart TV 55"', category: 'Electronics', sales: 142, revenue: '₹63,90,000', growth: '+12%' },
            { id: 2, name: 'Gaming Laptop Ryzen 7', category: 'Computers', sales: 89, revenue: '₹80,09,911', growth: '+8%' },
            { id: 3, name: '5G Smartphone 256GB', category: 'Mobile', sales: 234, revenue: '₹1,52,09,766', growth: '+24%' },
            { id: 4, name: 'Smart Home Security Camera', category: 'Smart Home', sales: 450, revenue: '₹11,24,550', growth: '+5%' },
        ]
    },
    All: {
        revenue: { value: '₹1,82,45,000', trend: 'up', percent: '+45%', subtext: 'Total Lifetime' },
        orders: { value: '89,231', trend: 'up', percent: '+67%', subtext: 'Total Lifetime' },
        users: { value: '46,912', trend: 'up', percent: '+12%', subtext: 'Total Users' },
        refunds: { value: '1,203', trend: 'up', percent: '+2%', subtext: 'Total Lifetime' },
        chart: [
            { name: 'Jan', B2B: 4000, B2C: 2400 },
            { name: 'Feb', B2B: 3000, B2C: 1398 },
            { name: 'Mar', B2B: 2000, B2C: 9800 },
            { name: 'Apr', B2B: 2780, B2C: 3908 },
            { name: 'May', B2B: 1890, B2C: 4800 },
            { name: 'Jun', B2B: 2390, B2C: 3800 },
            { name: 'Jul', B2B: 3490, B2C: 4300 },
        ],
        porter: [
            { name: 'On Time', value: 85, color: '#10B981' },
            { name: 'Late', value: 15, color: '#EF4444' },
        ],
        bestSellers: [
            { id: 1, name: 'Ultra HD 4K Smart TV 55"', category: 'Electronics', sales: 1420, revenue: '₹6,39,00,000', growth: '+120%' },
            { id: 2, name: '5G Smartphone 256GB', category: 'Mobile', sales: 2340, revenue: '₹15,20,97,660', growth: '+240%' },
        ]
    }
};
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7

// Updated Card Component: Rupee symbol updated, decorative line/trend removed
const Card = ({ title, value, icon: Icon, iconBg }: any) => (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between h-full transition-all hover:shadow-md">
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card title="Total Revenue" value={stats.revenue.value} icon={IndianRupee} iconBg="bg-blue-600" />
                <Card title="Total Orders" value={stats.orders.value} icon={ShoppingCart} iconBg="bg-violet-600" />
                <Card title="Total Users" value={stats.users.value} icon={Users} iconBg="bg-emerald-600" />
                <Card title="Refunds" value={stats.refunds.value} icon={RefreshCcw} iconBg="bg-rose-600" />
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
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col">
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
<<<<<<< HEAD
};
=======
};
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
