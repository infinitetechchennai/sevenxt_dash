import React, { useEffect, useRef, useState } from "react";
import {
  Layout,
  Image as ImageIcon,
  Bell,
  FileText,
  Plus,
  Trash2,
  Edit,
  UploadCloud,
  Smartphone,
  Globe,
  X,
} from "lucide-react";

import {
  getCMSBanners,
  createCMSBanner,
  updateCMSBanner,
  deleteCMSBanner,
  getCMSCategoryBanners,
  updateCMSCategoryBanner,
  getCMSNotifications,
  sendCMSNotification,
  getCMSPages,
  updateCMSPage,
  API_BASE_URL
} from "../services/api";

/* =======================
   TABS 
======================= */

const TABS = [
  { id: "cms-home", label: "Homepage Banners", icon: <Layout size={18} /> },
  { id: "cms-category", label: "Category Banners", icon: <ImageIcon size={18} /> },
  { id: "cms-notif", label: "Notification Manager", icon: <Bell size={18} /> },
  { id: "cms-pages", label: "Static Pages", icon: <FileText size={18} /> },
];

/* =======================
   CATEGORY MAPPING
======================= */

const CATEGORIES = [
  { id: 1, name: "All gadgets" },
  { id: 2, name: "mobile & devices" },
  { id: 3, name: "laptops & pc" },
  { id: 4, name: "cameras & photography" },
  { id: 5, name: "wearables" },
  { id: 6, name: "tv & entertainment" },
  { id: 7, name: "networking" },
  { id: 8, name: "peripherals" },
];

const CMSView: React.FC = () => {
  const [activeTab, setActiveTab] = useState("cms-home");

  /* =======================
      HOMEPAGE BANNERS
  ======================= */

  const [banners, setBanners] = useState<any[]>([]);
  const [isBannerModalOpen, setIsBannerModalOpen] = useState(false);
  const [currentBannerId, setCurrentBannerId] = useState<number | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string>("");

  const [bannerForm, setBannerForm] = useState({
    title: "",
    image: "",
    position: "Hero Slider",
    status: "Active",
  });

  const uploadBannerImage = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    const baseUrl = API_BASE_URL;

    try {
      const res = await fetch(
        `${baseUrl}/api/v1/cms/banners/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Server responded with ${res.status}: ${errorText}`);
      }

      const data = await res.json();
      setUploadedImageUrl(data.url);
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Failed to upload image. Please ensure your backend is running.");
    }
  };

  const openBannerModal = (banner?: any) => {
    setUploadedImageUrl("");
    if (banner) {
      setCurrentBannerId(banner.id);
      setBannerForm({
        title: banner.title,
        image: banner.image,
        position: banner.position,
        status: banner.status,
      });
    } else {
      setCurrentBannerId(null);
      setBannerForm({
        title: "",
        image: "",
        position: "Hero Slider",
        status: "Active",
      });
    }
    setIsBannerModalOpen(true);
  };

  const saveBanner = async () => {
    if (!uploadedImageUrl && !currentBannerId) {
      alert("Please upload an image first");
      return;
    }

    const payload = {
      ...bannerForm,
      image: uploadedImageUrl || bannerForm.image,
    };

    if (currentBannerId) {
      await updateCMSBanner(currentBannerId, payload);
    } else {
      await createCMSBanner(payload);
    }

    setIsBannerModalOpen(false);
    setUploadedImageUrl("");
    fetchBanners();
  };

  const deleteBanner = async (id: number) => {
    await deleteCMSBanner(id);
    fetchBanners();
  };

  const fetchBanners = async () => {
    const data = await getCMSBanners();
    setBanners(data);
  };

  /* =======================
      CATEGORY BANNERS
  ======================= */

  const [categoryImages, setCategoryImages] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<number>(CATEGORIES[0].id);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !selectedCategory) return;

    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);

    const baseUrl = API_BASE_URL;

    try {
      const res = await fetch(
        `${baseUrl}/api/v1/cms/category-banners/${selectedCategory}/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!res.ok) throw new Error(`Upload failed with status: ${res.status}`);
      const data = await res.json();

      await updateCMSCategoryBanner(selectedCategory as any, {
        image_url: data.url
      } as any);

      await loadCategoryBanners();
      alert("Category banner updated successfully!");
    } catch (error: any) {
      console.error("Category upload failed:", error);
      alert(`Update Failed: ${error.message || "Check console for details"}`);
    }
  };

  const loadCategoryBanners = async () => {
    const data = await getCMSCategoryBanners();
    setCategoryImages(data);
  };

  /* =======================
      NOTIFICATIONS (Updated with Validation)
  ======================= */

  const [notifHistory, setNotifHistory] = useState<any[]>([]);
  const [notifForm, setNotifForm] = useState({
    title: "",
    message: "",
    audience: "All Users",
  });

  const sendNotification = async () => {
    // Validation Check
    if (!notifForm.title.trim() || !notifForm.message.trim()) {
      alert("Please fill in all required details (Title and Message).");
      return;
    }

    try {
      await sendCMSNotification(notifForm);
      setNotifForm({ title: "", message: "", audience: "All Users" });
      loadNotifications();
      alert("Notification sent successfully!");
    } catch (error) {
      console.error("Failed to send notification:", error);
    }
  };

  const loadNotifications = async () => {
    const data = await getCMSNotifications();
    setNotifHistory(data);
  };

  /* =======================
      STATIC PAGES
  ======================= */

  const [pages, setPages] = useState<any[]>([]);
  const [isPageModalOpen, setIsPageModalOpen] = useState(false);
  const [pageForm, setPageForm] = useState<any>(null);

  const openPageModal = (page: any) => {
    setPageForm({ ...page });
    setIsPageModalOpen(true);
  };

  const savePage = async () => {
    await updateCMSPage(pageForm.id, {
      title: pageForm.title,
      content: pageForm.content,
    });
    setIsPageModalOpen(false);
    loadPages();
  };

  const loadPages = async () => {
    const data = await getCMSPages();
    setPages(data);
  };

  /* =======================
      INITIAL LOAD
  ======================= */

  useEffect(() => {
    fetchBanners();
    loadCategoryBanners();
    loadNotifications();
    loadPages();
  }, []);

  /* =======================
      RENDER FUNCTIONS
  ======================= */

  const renderHomeBanners = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
      <div className="flex justify-between items-center bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Homepage Visuals</h2>
          <p className="text-sm text-slate-500">Manage hero sliders and promotional banners.</p>
        </div>
        <button
          onClick={() => openBannerModal()}
          className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-colors shadow-md"
        >
          <Plus size={18} /> Add Banner
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {banners.map((banner) => (
          <div key={banner.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden group">
            <div className="relative h-40 bg-slate-100">
              <img src={banner.image} alt={banner.title} className="w-full h-full object-cover" />
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                <button
                  onClick={() => openBannerModal(banner)}
                  className="p-2 bg-white/90 text-slate-700 rounded-lg hover:text-gray-900 shadow-sm"
                >
                  <Edit size={16} />
                </button>
                <button
                  onClick={() => deleteBanner(banner.id)}
                  className="p-2 bg-white/90 text-slate-700 rounded-lg hover:text-red-600 shadow-sm"
                >
                  <Trash2 size={16} />
                </button>
              </div>
              <div className="absolute bottom-2 left-2">
                <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide backdrop-blur-md ${banner.status === 'Active' ? 'bg-emerald-500/90 text-white' : 'bg-slate-500/90 text-white'
                  }`}>
                  {banner.status}
                </span>
              </div>
            </div>
            <div className="p-4">
              <h3 className="font-bold text-slate-900">{banner.title}</h3>
              <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                <Layout size={12} /> {banner.position}
              </p>
            </div>
          </div>
        ))}

        <div
          onClick={() => openBannerModal()}
          className="border-2 border-dashed border-slate-200 rounded-2xl flex flex-col items-center justify-center h-full min-h-[200px] bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer group"
        >
          <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform">
            <UploadCloud size={24} className="text-gray-400" />
          </div>
          <p className="mt-3 text-sm font-medium text-slate-600">Add New Banner</p>
          <p className="text-xs text-slate-400 mt-1">1920 x 600px recommended</p>
        </div>
      </div>

      {isBannerModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
              <h3 className="font-bold text-lg text-slate-900">{currentBannerId ? 'Edit Banner' : 'Add Banner'}</h3>
              <button onClick={() => setIsBannerModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Title</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900"
                  value={bannerForm.title}
                  onChange={e => setBannerForm({ ...bannerForm, title: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Banner Image
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      uploadBannerImage(e.target.files[0]);
                    }
                  }}
                  className="w-full text-sm text-slate-600
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-lg file:border-0
                    file:text-sm file:font-semibold
                    file:bg-gray-900 file:text-white
                    hover:file:bg-gray-800 cursor-pointer"
                />

                {(uploadedImageUrl || bannerForm.image) ? (
                  <img
                    src={uploadedImageUrl || bannerForm.image}
                    alt="Preview"
                    className="mt-3 h-32 w-full object-cover rounded-lg border"
                  />
                ) : null}
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Position</label>
                <select
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900"
                  value={bannerForm.position}
                  onChange={e => setBannerForm({ ...bannerForm, position: e.target.value })}
                >
                  <option>Hero Slider</option>
                  <option>Mid Page</option>
                  <option>Footer Strip</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Status</label>
                <select
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900"
                  value={bannerForm.status}
                  onChange={e => setBannerForm({ ...bannerForm, status: e.target.value })}
                >
                  <option>Active</option>
                  <option>Inactive</option>
                </select>
              </div>
              <button
                onClick={saveBanner}
                className="w-full mt-4 py-2.5 bg-gray-900 text-white font-bold rounded-lg hover:bg-gray-800 transition-colors"
              >
                Save Banner
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderCategoryBanners = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Select Category</label>
            <select
              className="w-full px-4 py-2 bg-white border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(Number(e.target.value))}
            >
              {CATEGORIES.map(cat => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm text-center">
        <h3 className="text-lg font-bold text-slate-900 mb-4">
          {CATEGORIES.find(c => c.id === selectedCategory)?.name} Header Banner
        </h3>
        <div className="relative w-full h-48 bg-slate-100 rounded-xl overflow-hidden flex items-center justify-center mb-6 group">
          {categoryImages.find((img: any) => img.id === selectedCategory)?.image_url ? (
            <img src={categoryImages.find((img: any) => img.id === selectedCategory).image_url} alt="Category" className="w-full h-full object-cover" />
          ) : (
            <ImageIcon size={48} className="text-slate-300" />
          )}
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/30">
            <button
              onClick={triggerFileInput}
              className="px-6 py-2 bg-gray-900 rounded-lg font-bold text-white shadow-lg transform translate-y-2 group-hover:translate-y-0 transition-transform flex items-center gap-2"
            >
              <UploadCloud size={18} /> Change Image
            </button>
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              accept="image/*"
              onChange={handleImageUpload}
            />
          </div>
        </div>
        <div className="flex justify-between items-center pt-6 border-t border-slate-100">
          <div className="text-left">
            <p className="text-sm font-bold text-slate-900">Banner Status</p>
            <p className="text-xs text-slate-500">Visible on mobile and desktop</p>
          </div>
          <div className="relative inline-block w-12 align-middle select-none transition duration-200 ease-in">
            <input type="checkbox" defaultChecked className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer" />
            <label className="toggle-label block overflow-hidden h-6 rounded-full bg-emerald-500 cursor-pointer"></label>
          </div>
        </div>
      </div>
    </div>
  );

  const renderNotifications = () => (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-2">
      <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-2 mb-6 pb-4 border-b border-slate-100">
          <Smartphone size={20} className="text-gray-900" />
          <h3 className="text-lg font-bold text-slate-900">Compose Push Notification</h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Title</label>
            <input
              type="text"
              placeholder="e.g. Flash Sale Alert! ⚡"
              className="w-full px-4 py-2 bg-white border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900"
              value={notifForm.title}
              onChange={e => setNotifForm({ ...notifForm, title: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Message Body</label>
            <textarea
              rows={3}
              placeholder="Get 50% off on all electronics today only..."
              className="w-full px-4 py-2 bg-white border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900"
              value={notifForm.message}
              onChange={e => setNotifForm({ ...notifForm, message: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Target Audience</label>
            <select
              className="w-full px-4 py-2 bg-white border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900"
              value={notifForm.audience}
              onChange={e => setNotifForm({ ...notifForm, audience: e.target.value })}
            >
              <option>All Users</option>
              <option>B2B Customers Only</option>
              <option>B2C Customers Only</option>
              <option>Inactive Users (30+ Days)</option>
            </select>
          </div>
          <div className="pt-4 flex justify-end">
            <button
              onClick={sendNotification}
              className="px-8 py-3 bg-gray-900 text-white font-bold rounded-xl hover:bg-gray-800 shadow-lg transition-all flex items-center gap-2"
            >
              <Bell size={18} /> Send Notification
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm h-fit">
        <h3 className="text-lg font-bold text-slate-900 mb-4">Recent History</h3>
        <div className="space-y-4">
          {notifHistory.map(notif => (
            <div key={notif.id} className="p-4 bg-slate-50 rounded-xl border border-slate-100 animate-in slide-in-from-right-4">
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-bold text-slate-500">{notif.time}</span>
                <span className="text-[10px] bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-bold">{notif.status}</span>
              </div>
              <p className="font-bold text-slate-800 text-sm">{notif.title}</p>
              <p className="text-xs text-slate-500 mt-1 line-clamp-2">{notif.message}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderStaticPages = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Static Content Pages</h2>
          <p className="text-sm text-slate-500">Manage legal, about, and support pages.</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead className="bg-slate-50/50 border-b border-slate-200">
            <tr>
              <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Page Title</th>
              <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Slug</th>
              <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Last Updated</th>
              <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Status</th>
              <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {pages.map(page => (
              <tr key={page.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4 text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Globe size={14} className="text-slate-400" />
                  {page.title}
                </td>
                <td className="px-6 py-4 text-sm text-slate-500 font-mono">{page.slug}</td>

                {/* --- FIXED LAST UPDATED COLUMN --- */}
                <td className="px-6 py-4 text-sm text-slate-500">
                  {page.updated_at ? new Date(page.updated_at).toLocaleString('en-IN', {
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  }) : "Never"}
                </td>

                <td className="px-6 py-4">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-100 text-emerald-700 border border-emerald-200">
                    {page.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => openPageModal(page)}
                      className="p-2 text-slate-400 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <Edit size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isPageModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl h-[80vh] flex flex-col animate-in zoom-in-95 duration-200">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
              <h3 className="font-bold text-lg text-slate-900">Edit Page: {pageForm.title}</h3>
              <button onClick={() => setIsPageModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 p-6 flex flex-col gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Page Title</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900"
                  value={pageForm.title}
                  onChange={e => setPageForm({ ...pageForm, title: e.target.value })}
                />
              </div>
              <div className="flex-1 flex flex-col">
                <label className="block text-sm font-medium text-slate-700 mb-1">Content (Markdown/HTML)</label>
                <textarea
                  className="flex-1 w-full px-4 py-3 border border-slate-300 rounded-lg font-mono text-sm text-gray-900"
                  value={pageForm.content}
                  onChange={e => setPageForm({ ...pageForm, content: e.target.value })}
                />
              </div>
            </div>
            <div className="px-6 py-4 border-t border-slate-100 flex justify-end gap-3">
              <button onClick={() => setIsPageModalOpen(false)} className="px-4 py-2 text-slate-600 hover:bg-slate-50 rounded-lg">Cancel</button>
              <button onClick={savePage} className="px-6 py-2 bg-gray-900 text-white font-bold rounded-lg hover:bg-gray-800">Save Changes</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="flex flex-col h-screen bg-slate-50 overflow-hidden font-sans">
      <div className="bg-white border-b border-slate-200 px-6 py-5 shrink-0">
        <h1 className="text-2xl font-bold text-slate-900">Content Management</h1>
        <p className="text-slate-500 text-sm">Manage app banners, notifications, and static content.</p>
      </div>

      <div className="bg-white border-b border-slate-200 px-6 pt-2">
        <nav className="-mb-px flex space-x-8 overflow-x-auto no-scrollbar">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                group whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2
                ${activeTab === tab.id
                  ? 'border-gray-900 text-gray-900'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}
              `}
            >
              <span className={`${activeTab === tab.id ? 'text-gray-900' : 'text-slate-400 group-hover:text-slate-500'}`}>
                {tab.icon}
              </span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-6xl mx-auto">
          {activeTab === 'cms-home' && renderHomeBanners()}
          {activeTab === 'cms-category' && renderCategoryBanners()}
          {activeTab === 'cms-notif' && renderNotifications()}
          {activeTab === 'cms-pages' && renderStaticPages()}
        </div>
      </div>
    </div>
  );
};

export default CMSView;
