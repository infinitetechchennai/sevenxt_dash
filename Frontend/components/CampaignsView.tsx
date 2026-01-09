import React, { useEffect, useState } from "react";
import { Tag, Zap, Plus, Search, X } from "lucide-react";
import { getCampaignCoupons, createCampaignCoupon, updateCampaignCoupon, deleteCampaignCoupon, getCampaignFlashDeals } from "../services/api";

export const CampaignsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"Promos" | "Flash Deals">("Promos");
  const [searchTerm, setSearchTerm] = useState("");
  const [coupons, setCoupons] = useState<any[]>([]);
  const [flashDeals, setFlashDeals] = useState<any[]>([]);
  const [showPromoModal, setShowPromoModal] = useState(false);
  const [editingCoupon, setEditingCoupon] = useState<any | null>(null);
  const [newPromo, setNewPromo] = useState({ code: "", type: "Percentage", value: "", target: "All", expiry: "", min_order_value: "0", usage_limit: "100" });

  useEffect(() => { loadCoupons(); loadFlashDeals(); }, []);

  const loadCoupons = async () => { setCoupons(await getCampaignCoupons()); };
  const loadFlashDeals = async () => { setFlashDeals(await getCampaignFlashDeals()); };

  const handleAddPromo = async () => {
    if (!newPromo.code || !newPromo.value) return;

    // 🔥 FIX: Clean payload before sending
    const payload: any = {
      code: newPromo.code,
      type: newPromo.type,
      value: newPromo.value,
      target: newPromo.target,
      min_order_value: newPromo.min_order_value,
      usage_limit: newPromo.usage_limit,
      expiry: newPromo.expiry.trim() === "" ? null : newPromo.expiry
    };

    if (editingCoupon) {
      await updateCampaignCoupon(editingCoupon.id, payload);
    } else {
      await createCampaignCoupon(payload);
    }

    setShowPromoModal(false);
    setEditingCoupon(null);
    setNewPromo({ code: "", type: "Percentage", value: "", target: "All", expiry: "", min_order_value: "0", usage_limit: "100" });
    loadCoupons();
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 overflow-hidden">
      <div className="bg-white border-b px-6 py-5">
        <h1 className="text-2xl font-bold">Campaigns & Promotions</h1>
        <p className="text-sm text-gray-500">Manage coupons and product flash deals</p>
      </div>

      <div className="bg-white border-b px-6">
        <nav className="flex space-x-8">
          <button onClick={() => setActiveTab("Promos")} className={`pb-3 flex items-center gap-2 text-sm font-medium border-b-2 transition-colors ${activeTab === "Promos" ? "border-indigo-600 text-indigo-600" : "border-transparent text-gray-500"}`}><Tag size={18} /> Coupons & Promos</button>
          <button onClick={() => setActiveTab("Flash Deals")} className={`pb-3 flex items-center gap-2 text-sm font-medium border-b-2 transition-colors ${activeTab === "Flash Deals" ? "border-indigo-600 text-indigo-600" : "border-transparent text-gray-500"}`}><Zap size={18} /> Flash Deals</button>
        </nav>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        {activeTab === "Promos" && (
          <>
            <div className="flex justify-between mb-4">
              <div className="relative w-64">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input className="w-full pl-9 pr-3 py-2 border rounded-lg text-sm outline-none" placeholder="Search..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
              </div>
              <button onClick={() => { setEditingCoupon(null); setShowPromoModal(true); }} className="bg-gray-900 text-white px-4 py-2 rounded-lg flex items-center gap-2"><Plus size={16} /> Create Coupon</button>
            </div>
            <div className="bg-white rounded-xl border overflow-hidden shadow-sm">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                  <tr><th className="px-6 py-4">Code</th><th className="px-6 py-4">Value</th><th className="px-6 py-4 text-right">Action</th></tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {coupons.filter(c => c.code.toLowerCase().includes(searchTerm.toLowerCase())).map(coupon => (
                    <tr key={coupon.id}>
                      <td className="px-6 py-4 font-mono font-bold text-indigo-600">{coupon.code}</td>
                      <td className="px-6 py-4">{coupon.value} ({coupon.type})</td>
                      <td className="px-6 py-4 text-right">
                        <button onClick={() => { setEditingCoupon(coupon); setNewPromo({ ...coupon, expiry: coupon.expiry || "" }); setShowPromoModal(true); }} className="text-indigo-600 mr-4">Edit</button>
                        <button onClick={async () => { if (confirm("Delete?")) { await deleteCampaignCoupon(coupon.id); loadCoupons(); } }} className="text-red-600">Delete</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {/* ================= FLASH DEALS (RESTORED ORIGINAL) ================= */}
        {activeTab === "Flash Deals" && (
          <div className="bg-white rounded-xl border overflow-hidden shadow-sm">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                <tr><th className="px-6 py-3">Product</th><th className="px-6 py-3">Original</th><th className="px-6 py-3">Deal Price</th><th className="px-6 py-3">Discount</th><th className="px-6 py-3">Ends</th><th className="px-6 py-3">Status</th></tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {flashDeals.filter(d => d.product.toLowerCase().includes(searchTerm.toLowerCase())).map(deal => (
                  <tr key={deal.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900">{deal.product}</td>
                    <td className="px-6 py-4 text-gray-500 line-through">₹{deal.original_price}</td>
                    <td className="px-6 py-4 text-green-600 font-bold">₹{deal.deal_price}</td>
                    <td className="px-6 py-4"><span className="text-orange-600 font-medium bg-orange-50 px-2 py-0.5 rounded">{deal.discount}</span></td>
                    <td className="px-6 py-4 text-gray-600">{deal.ends_in ? new Date(deal.ends_in).toLocaleDateString() : "—"}</td>
                    <td className="px-6 py-4"><span className="bg-green-100 text-green-700 text-[10px] font-bold uppercase px-2 py-1 rounded-full">Active</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showPromoModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md shadow-2xl p-6 space-y-4 overflow-hidden">
            <div className="flex justify-between">
              <h3 className="text-lg font-bold">{editingCoupon ? "Edit" : "Create"} Coupon & Sync</h3>
              <X className="cursor-pointer" onClick={() => setShowPromoModal(false)} />
            </div>
            <input className="w-full border p-2.5 rounded-lg font-mono uppercase" placeholder="WELCOME50" value={newPromo.code} onChange={e => setNewPromo({ ...newPromo, code: e.target.value.toUpperCase() })} />
            <div className="grid grid-cols-2 gap-4">
              <input className="border p-2.5 rounded-lg" placeholder="Value" value={newPromo.value} onChange={e => setNewPromo({ ...newPromo, value: e.target.value })} />
              <select className="border p-2.5 rounded-lg bg-white" value={newPromo.type} onChange={e => setNewPromo({ ...newPromo, type: e.target.value })}><option value="Percentage">Percentage %</option><option value="Fixed">Fixed ₹</option></select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] text-gray-400 font-bold">MIN ORDER</label>
                <input type="number" className="w-full border p-2.5 rounded-lg" value={newPromo.min_order_value} onChange={e => setNewPromo({ ...newPromo, min_order_value: e.target.value })} />
              </div>
              <div>
                <label className="text-[10px] text-gray-400 font-bold">EXPIRY DATE</label>
                <input type="date" className="w-full border p-2.5 rounded-lg" value={newPromo.expiry} onChange={e => setNewPromo({ ...newPromo, expiry: e.target.value })} />
              </div>
            </div>
            <button onClick={handleAddPromo} className="w-full bg-indigo-600 text-white font-bold py-3 rounded-lg shadow-lg active:scale-95 transition-all">Create & Sync with Razorpay</button>
          </div>
        </div>
      )}
    </div>
  );
};
