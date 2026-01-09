import React, { useEffect, useState } from 'react';
import { Eye, Check, X, Phone, Mail, XCircle, Activity, FileText, FileCheck, Maximize2, Download, Clock, CheckCircle2, Ban, AlertCircle, ShieldCheck } from 'lucide-react';
import { getB2BUsers, updateB2BStatus, API_BASE_URL } from '../services/api';
import Swal from 'sweetalert2';

export const B2BView: React.FC = () => {
  const [b2bUsers, setB2BUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState('pending_approval');
  const [viewingUser, setViewingUser] = useState<any>(null);
  const [fullScreenImg, setFullScreenImg] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await getB2BUsers();
      setB2BUsers(data);
    } catch (error) {
      Swal.fire({ title: 'Error', text: 'Failed to load B2B data.', icon: 'error', customClass: { popup: 'rounded-2xl' } });
    } finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, []);

  // --- AUTOMATIC VERIFICATION HANDLER (RAZORPAY WORKFLOW) ---
  const handleAutoVerify = async (type: 'PAN' | 'GST', value: string) => {
    if (!value) {
      return Swal.fire({ title: 'Missing Info', text: `No ${type} number provided for this business.`, icon: 'warning', customClass: { popup: 'rounded-2xl' } });
    }

    const confirm = await Swal.fire({
      title: `Verify ${type}?`,
      text: `Consulting Government records for: ${value}`,
      icon: 'info',
      showCancelButton: true,
      confirmButtonColor: '#4f46e5',
      confirmButtonText: 'Verify Now',
      customClass: { popup: 'rounded-2xl' }
    });

    if (!confirm.isConfirmed) return;

    setIsVerifying(true);
    Swal.fire({ title: 'Verifying...', allowOutsideClick: false, didOpen: () => { Swal.showLoading(); }, customClass: { popup: 'rounded-2xl' } });

    try {
      // API call to your backend which talks to Razorpay Identity
      const response = await fetch(`${API_BASE_URL}/api/v1/b2b/verify-${type.toLowerCase()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ number: value })
      });

      const data = await response.json();

      if (response.ok && data.valid) {
        Swal.fire({
          title: 'Authentic!',
          html: `<div class="text-left bg-slate-50 p-3 rounded-lg text-sm">
                        <b>Registered Name:</b> ${data.business_name}<br/>
                        <b>Status:</b> ${data.status_desc || 'Active'}
                       </div>`,
          icon: 'success',
          customClass: { popup: 'rounded-2xl' }
        });
      } else {
        Swal.fire({ title: 'Validation Failed', text: data.detail || 'This document is invalid or not found in records.', icon: 'error', customClass: { popup: 'rounded-2xl' } });
      }
    } catch (error) {
      Swal.fire({ title: 'Service Error', text: 'Verification gateway is unreachable.', icon: 'error', customClass: { popup: 'rounded-2xl' } });
    } finally {
      setIsVerifying(false);
    }
  };

  const handleStatusChange = async (id: number, newStatus: string) => {
    const statusLabels: Record<string, string> = { approved: 'Approve', rejected: 'Reject', suspended: 'Suspend' };
    const result = await Swal.fire({
      title: `${statusLabels[newStatus] || 'Update'} Business?`,
      text: `Set business status to ${newStatus.replace('_', ' ')}?`,
      icon: 'question',
      showCancelButton: true,
      confirmButtonColor: newStatus === 'approved' ? '#16a34a' : '#dc2626',
      cancelButtonColor: '#64748b',
      confirmButtonText: `Yes, Proceed`,
      customClass: { popup: 'rounded-2xl' }
    });

    if (!result.isConfirmed) return;

    try {
      await updateB2BStatus(id, { status: newStatus });
      Swal.fire({ title: 'Updated!', icon: 'success', timer: 1500, showConfirmButton: false, customClass: { popup: 'rounded-2xl' } });
      loadData();
    } catch (error) {
      Swal.fire({ title: 'Error', text: 'Status update failed.', icon: 'error', customClass: { popup: 'rounded-2xl' } });
    }
  };

  const filteredUsers = b2bUsers.filter(user => user.status === activeSubTab);
  const subTabs = [
    { id: 'pending_approval', label: 'Pending', icon: <Clock size={16} /> },
    { id: 'approved', label: 'Approved', icon: <CheckCircle2 size={16} /> },
    { id: 'suspended', label: 'Suspended', icon: <Ban size={16} /> },
    { id: 'rejected', label: 'Rejected', icon: <AlertCircle size={16} /> },
  ];

  const renderFilePreview = (url: string) => {
    if (!url) return <div className="text-gray-400 text-sm font-medium">No Document</div>;
    const isPDF = url.toLowerCase().endsWith('.pdf');
    return isPDF ? (
      <div className="flex flex-col items-center">
        <FileText size={48} className="text-red-500 mb-2" />
        <span className="text-[10px] font-bold text-gray-500 uppercase">PDF Document</span>
      </div>
    ) : (
      <img src={url} className="w-full h-full object-contain" alt="Certificate" />
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 tracking-tight">B2B Management</h2>
          <p className="text-gray-500 mt-1">Manage business approvals and compliance docs</p>
        </div>
        <button onClick={loadData} className="p-2 text-gray-400 hover:text-gray-900 border rounded-full hover:bg-gray-50 transition-all">
          <Activity size={20} />
        </button>
      </div>

      <div className="flex space-x-1 border-b border-gray-200">
        {subTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id)}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-bold transition-all border-b-2 ${activeSubTab === tab.id ? 'border-gray-900 text-gray-900' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
          >
            {tab.icon} {tab.label}
            <span className={`ml-1 px-2 py-0.5 rounded-full text-[10px] ${activeSubTab === tab.id ? 'bg-gray-900 text-white' : 'bg-gray-200 text-gray-600'}`}>
              {b2bUsers.filter(u => u.status === tab.id).length}
            </span>
          </button>
        ))}
      </div>

      <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-200 bg-gray-50/50 uppercase font-bold text-xs tracking-wider text-gray-500">
          {activeSubTab.replace('_', ' ')} Requests
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Business Details</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">GSTIN / PAN</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Contact Info</th>
                <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUsers.length > 0 ? filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-bold text-gray-900 uppercase">{user.bussiness_name}</div>
                    <div className="text-xs text-gray-500 font-medium">ID: #{user.id}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 font-medium">GST: {user.gstin}</div>
                    <div className="text-xs text-indigo-600 font-mono font-bold uppercase tracking-tighter">PAN: {user.pan}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-600 flex items-center gap-1 font-medium"><Mail size={12} /> {user.email}</div>
                    <div className="text-sm text-gray-600 flex items-center gap-1 font-medium"><Phone size={12} /> {user.phone_number}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => setViewingUser(user)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded border border-blue-200 transition-colors">
                        <Eye size={16} />
                      </button>
                      {user.status === 'pending_approval' && (
                        <>
                          <button onClick={() => handleStatusChange(user.id, 'approved')} className="px-3 py-1 text-xs font-bold text-white bg-green-600 rounded hover:bg-green-700 flex items-center gap-1"><Check size={14} /> Approve</button>
                          <button onClick={() => handleStatusChange(user.id, 'rejected')} className="px-3 py-1 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 flex items-center gap-1"><X size={14} /> Reject</button>
                        </>
                      )}
                      {user.status === 'approved' && (
                        <button onClick={() => handleStatusChange(user.id, 'suspended')} className="px-3 py-1 text-xs font-bold text-white bg-orange-600 rounded hover:bg-orange-700 flex items-center gap-1"><XCircle size={14} /> Suspend</button>
                      )}
                      {user.status === 'suspended' && (
                        <button onClick={() => handleStatusChange(user.id, 'approved')} className="px-3 py-1 text-xs font-bold text-white bg-indigo-600 rounded hover:bg-indigo-700 flex items-center gap-1"><Activity size={14} /> Unsuspend</button>
                      )}
                    </div>
                  </td>
                </tr>
              )) : (
                <tr><td colSpan={4} className="px-6 py-12 text-center text-gray-400 text-sm font-medium">No entities found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* VIEW MODAL WITH AUTO-VERIFY FEATURE */}
      {viewingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b flex justify-between items-center bg-gray-50">
              <h3 className="text-xl font-extrabold text-gray-900 tracking-tight">{viewingUser.bussiness_name} Verification</h3>
              <button onClick={() => setViewingUser(null)} className="p-2 hover:bg-gray-200 rounded-full transition-colors"><X size={24} /></button>
            </div>
            <div className="p-8 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-10">
              {/* GST SECTION */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h4 className="font-bold text-gray-800 flex items-center gap-2 underline underline-offset-8 decoration-2 decoration-blue-500 tracking-tighter"><FileText size={20} /> GST Certificate</h4>
                  <button
                    onClick={() => handleAutoVerify('GST', viewingUser.gstin)}
                    className="flex items-center gap-1 text-[10px] bg-blue-600 text-white px-2 py-1 rounded font-bold hover:bg-blue-700 transition-all shadow-sm"
                  >
                    <ShieldCheck size={12} /> Verify GST
                  </button>
                </div>
                <div onClick={() => viewingUser.gst_certificate_url && setFullScreenImg(viewingUser.gst_certificate_url)} className="relative border-2 border-dashed border-gray-200 rounded-2xl overflow-hidden bg-gray-50 aspect-[4/5] flex items-center justify-center cursor-pointer group shadow-inner">
                  {renderFilePreview(viewingUser.gst_certificate_url)}
                  <div className="absolute inset-0 bg-black/10 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity"><Maximize2 size={24} className="text-white" /></div>
                </div>
              </div>
              {/* PAN SECTION */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h4 className="font-bold text-gray-800 flex items-center gap-2 underline underline-offset-8 decoration-2 decoration-orange-500 tracking-tighter"><FileCheck size={20} /> PAN Certificate</h4>
                  <button
                    onClick={() => handleAutoVerify('PAN', viewingUser.pan)}
                    className="flex items-center gap-1 text-[10px] bg-orange-600 text-white px-2 py-1 rounded font-bold hover:bg-orange-700 transition-all shadow-sm"
                  >
                    <ShieldCheck size={12} /> Verify PAN
                  </button>
                </div>
                <div onClick={() => viewingUser.business_license_url && setFullScreenImg(viewingUser.business_license_url)} className="relative border-2 border-dashed border-gray-200 rounded-2xl overflow-hidden bg-gray-50 aspect-[4/5] flex items-center justify-center cursor-pointer group shadow-inner">
                  {renderFilePreview(viewingUser.business_license_url)}
                  <div className="absolute inset-0 bg-black/10 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity"><Maximize2 size={24} className="text-white" /></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* LIGHTBOX FOR FULL VIEW */}
      {fullScreenImg && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/95 p-4 animate-in fade-in">
          <div className="absolute top-6 right-6 flex items-center gap-4">
            <a href={fullScreenImg} download className="p-3 bg-white/10 text-white rounded-full flex items-center gap-2 px-5 font-bold text-sm border border-white/20 hover:bg-white/20 transition-all"><Download size={20} /> Download</a>
            <button onClick={() => setFullScreenImg(null)} className="p-3 bg-white/10 text-white rounded-full hover:bg-white/20 transition-all"><X size={32} /></button>
          </div>
          <div className="w-full h-full max-w-6xl max-h-[85vh] flex items-center justify-center mt-12">
            {fullScreenImg.toLowerCase().endsWith('.pdf') ? (<iframe src={fullScreenImg} className="w-full h-full rounded-xl bg-white shadow-2xl" title="PDF Full Viewer" />) : (<img src={fullScreenImg} className="max-w-full max-h-full object-contain rounded-lg shadow-2xl border border-white/10" alt="Full Document" />)}
          </div>
        </div>
      )}
    </div>
  );
};
