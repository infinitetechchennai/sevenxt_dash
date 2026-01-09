import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { API_BASE_URL } from '../services/api';

const API_BASE = `${API_BASE_URL}/api/v1/reports`;
const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export const ReportsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState('rep-sales');
  const [timeframe, setTimeframe] = useState('daily');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      let endpoint = `${API_BASE}/sales?timeframe=${timeframe}`;
      if (activeTab === 'rep-products') endpoint = `${API_BASE}/top-products`;
      if (activeTab === 'rep-delivery') endpoint = `${API_BASE}/delivery`;
      if (activeTab === 'rep-segments') endpoint = `${API_BASE}/segments`;
      if (activeTab === 'rep-returns') endpoint = `${API_BASE}/returns`;

      const res = await axios.get(endpoint);

      if (activeTab === 'rep-sales' && res.data.chart) {
        setData(res.data.chart.map((item: any) => ({ name: item.name, value: item.sales })));
      } else {
        setData(Array.isArray(res.data) ? res.data : []);
      }
    } catch (err) {
      console.error("Dashboard error:", err);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [activeTab, timeframe]);

  useEffect(() => { loadData(); }, [loadData]);

  const totalCount = data.reduce((acc, curr) => acc + (Number(curr.value) || 0), 0);

  return (
    <div className="flex flex-col h-screen bg-slate-50 overflow-hidden font-sans">
      <div className="bg-white border-b border-slate-200 px-6 py-5 shrink-0 flex justify-between items-center text-slate-900">
        <h1 className="text-2xl font-bold">Reports & Analytics</h1>
        {activeTab === 'rep-sales' && (
          <div className="flex bg-slate-100 p-1 rounded-lg">
            {['Daily', 'Weekly', 'Monthly', 'All'].map((t) => (
              <button key={t} onClick={() => setTimeframe(t.toLowerCase())}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${timeframe === t.toLowerCase() ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-500'}`}>{t}</button>
            ))}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-2xl border border-slate-200 mb-6 flex p-1 shadow-sm w-fit flex-wrap">
            {['sales', 'products', 'delivery', 'segments', 'returns'].map((tab) => (
              <button key={tab} onClick={() => setActiveTab(`rep-${tab}`)}
                className={`px-4 py-2 text-sm font-medium rounded-xl capitalize transition-all ${activeTab === `rep-${tab}` ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500'}`}>{tab === 'delivery' ? 'Logistics' : tab}</button>
            ))}
          </div>

          <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm min-h-[500px] relative">
            {loading && <div className="absolute inset-0 bg-white/40 flex items-center justify-center rounded-3xl z-10 text-slate-400">Loading Data...</div>}

            <div className="w-full h-full min-h-[400px]">
              {activeTab === 'rep-sales' && (
                <div style={{ width: '100%', height: '400px' }}> {/* FIXED HEIGHT */}
                  <ResponsiveContainer>
                    <AreaChart data={data}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                      <Tooltip />
                      <Area type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={3} fill="#6366f1" fillOpacity={0.05} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}

              {activeTab === 'rep-products' && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="text-slate-400 text-xs font-bold uppercase border-b border-slate-100">
                        <th className="pb-4 px-4 text-left">Product Name</th>
                        <th className="pb-4 px-4 text-right">Units Sold</th>
                        <th className="pb-4 px-4 text-right">Total Revenue</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {data.map((item: any, i: number) => (
                        <tr key={i} className="hover:bg-slate-50 transition-colors text-slate-900">
                          <td className="py-4 px-4 font-medium text-sm">{item.name}</td>
                          <td className="py-4 px-4 text-right text-sm">{item.sales}</td>
                          <td className="py-4 px-4 text-right font-bold text-indigo-600 text-sm">₹{(item.revenue || 0).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {(activeTab === 'rep-delivery' || activeTab === 'rep-segments') && (
                <div style={{ width: '100%', height: '400px' }} className="flex flex-col items-center">
                  <h2 className="text-lg font-bold text-slate-900 mb-6 capitalize">{activeTab === 'rep-delivery' ? 'Logistics' : 'Market Split'}</h2>
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie data={data} innerRadius={80} outerRadius={120} paddingAngle={5} dataKey="value">
                        {data.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                      </Pie>
                      <Tooltip />
                      <Legend verticalAlign="bottom" height={36} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}

              {activeTab === 'rep-returns' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center min-h-[400px]">
                  <div style={{ width: '100%', height: '350px' }} className="relative flex flex-col items-center justify-center">
                    <h3 className="text-lg font-bold mb-6 text-slate-900">Return Distribution</h3>
                    <ResponsiveContainer>
                      <PieChart>
                        <Pie data={data.length > 0 ? data : [{ name: 'No Data', value: 1 }]} innerRadius={90} outerRadius={130} paddingAngle={8} dataKey="value" stroke="none">
                          {data.length > 0 ? data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />) : <Cell fill="#f1f5f9" />}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="absolute top-[60%] left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none text-slate-900">
                      <p className="text-4xl font-black leading-none">{totalCount}</p>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-1">Total Cases</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Reason Breakdown</h3>
                    {data.length > 0 ? data.map((item, i) => (
                      <div key={i} className="flex justify-between items-center p-4 bg-slate-50 rounded-2xl border border-slate-100 text-slate-900">
                        <div className="flex items-center gap-3">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                          <span className="font-semibold text-sm">{item.name}</span>
                        </div>
                        <span className="font-bold">{item.value}</span>
                      </div>
                    )) : <p className="text-slate-400 italic text-center py-10 bg-slate-50 rounded-2xl border border-dashed">No records found.</p>}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};