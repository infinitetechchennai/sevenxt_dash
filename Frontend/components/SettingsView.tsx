
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Eye, Bell, Lock, FileText, Save, Upload, RefreshCw,
  AlertTriangle, Shield, ShoppingCart, RotateCcw, Package, User, LogOut
} from 'lucide-react';
import { MOCK_ACTIVITY_LOGS } from '../constants';
import { API_BASE_URL } from '../services/api';


interface SettingsViewProps {
  activeView?: string;
}

type TabId = 'set-profile' | 'set-notifications';

const TABS = [
  { id: 'set-profile', label: 'Edit Profile', icon: <User size={18} /> },
  { id: 'set-notifications', label: 'Notification', icon: <Bell size={18} /> },
];

export const SettingsView: React.FC<SettingsViewProps> = ({ activeView }) => {
  const [activeTab, setActiveTab] = useState<TabId>('set-profile');
  const [showLogoutModal, setShowLogoutModal] = useState(false);

  // Sync activeTab with prop activeView if it matches one of our tabs
  useEffect(() => {
    if (activeView && TABS.some(t => t.id === activeView)) {
      setActiveTab(activeView as TabId);
    } else if (activeView === 'set-notifications') {
      setActiveTab('set-notifications');
    } else if (activeView === 'set-profile') {
      setActiveTab('set-profile');
    } else if (activeView === 'settings') {
      setActiveTab('set-profile');
    }
  }, [activeView]);

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    window.location.href = '/'; // Redirect to login
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'set-profile': return <ProfileSettings />;
      case 'set-notifications': return <NotificationSettings />;
      default: return <ProfileSettings />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 overflow-hidden font-sans">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6 shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">System Settings</h1>
            <p className="text-gray-500 mt-1 text-sm">Manage application branding, integrations, and security protocols.</p>
          </div>
          <button
            onClick={() => setShowLogoutModal(true)}
            className="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg font-medium hover:from-red-600 hover:to-red-700 transition-all shadow-md hover:shadow-lg flex items-center gap-2"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200 px-8 shrink-0">
        <nav className="-mb-px flex space-x-8 overflow-x-auto no-scrollbar">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabId)}
              className={`
                group whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2
                ${activeTab === tab.id
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
              `}
            >
              <span className={activeTab === tab.id ? 'text-indigo-600' : 'text-gray-400 group-hover:text-gray-500'}>
                {tab.icon}
              </span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Main Content Area with Animation */}
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-5xl animate-in fade-in slide-in-from-bottom-4 duration-500">
          {renderContent()}
        </div>
      </div>

      {/* Logout Confirmation Modal */}
      {showLogoutModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full animate-in fade-in zoom-in duration-200">
            {/* Header */}
            <div className="bg-gradient-to-r from-red-500 to-red-600 p-6 rounded-t-2xl">
              <div className="flex items-center justify-center w-16 h-16 bg-white rounded-full mx-auto mb-4">
                <LogOut size={32} className="text-red-600" />
              </div>
              <h3 className="text-2xl font-bold text-white text-center">Logout Confirmation</h3>
            </div>

            {/* Body */}
            <div className="p-6">
              <p className="text-gray-600 text-center mb-6">
                Are you sure you want to logout from the dashboard? You'll need to login again to access your account.
              </p>

              {/* Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => setShowLogoutModal(false)}
                  className="flex-1 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleLogout}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg font-medium hover:from-red-600 hover:to-red-700 transition-all shadow-md flex items-center justify-center gap-2"
                >
                  <LogOut size={18} />
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// --- Sub-Components for Each Section ---

const ProfileSettings = () => {
  const [profileData, setProfileData] = useState({
    name: '',
    email: '',
    phone: '',
    role: '',
    profilePicture: '',
    address: '',
    city: '',
    state: '',
    pincode: ''
  });
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await axios.get(`${API_BASE_URL}/api/v1/auth/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfileData({
        name: response.data.name || '',
        email: response.data.email || '',
        phone: response.data.phone || '',
        role: response.data.role || '',
        profilePicture: response.data.profile_picture || '',
        address: response.data.address || '',
        city: response.data.city || '',
        state: response.data.state || '',
        pincode: response.data.pincode || ''
      });
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setProfileData(prev => ({ ...prev, [field]: value }));
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file size (2MB max)
    if (file.size > 2 * 1024 * 1024) {
      alert('File size must be less than 2MB');
      return;
    }

    // Validate file type
    if (!['image/jpeg', 'image/png', 'image/gif'].includes(file.type)) {
      alert('Only JPG, PNG, and GIF files are allowed');
      return;
    }

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);

      const token = localStorage.getItem('auth_token');
      console.log('Token exists:', !!token);
      console.log('Token value:', token?.substring(0, 20) + '...');

      const response = await axios.post(
        `${API_BASE_URL}/api/v1/auth/upload-profile-picture`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      setProfileData(prev => ({
        ...prev,
        profilePicture: response.data.profile_picture
      }));

      // Refresh the entire profile to get updated data
      await fetchProfile();

      // Trigger a global event to refresh profile in header/sidebar
      window.dispatchEvent(new Event('profileUpdated'));

      alert('Profile picture uploaded successfully!');
    } catch (error) {
      console.error('Failed to upload profile picture:', error);
      alert('Failed to upload profile picture');
    } finally {
      setUploading(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      const response = await axios.put(
        `${API_BASE_URL}/api/v1/auth/profile`,
        {
          name: profileData.name,
          phone: profileData.phone,
          email: profileData.email,
          address: profileData.address,
          city: profileData.city,
          state: profileData.state,
          pincode: profileData.pincode
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      // Refresh profile data
      await fetchProfile();

      // Trigger global event to update header/sidebar
      window.dispatchEvent(new Event('profileUpdated'));

      setIsEditing(false); // Exit edit mode
      alert('Profile updated successfully!');
    } catch (error) {
      console.error('Failed to update profile:', error);
      alert('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    fetchProfile(); // Reload original data
    setIsEditing(false); // Exit edit mode
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <div className="mb-6 pb-4 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <User size={20} className="text-indigo-500" />
                Profile Information
              </h2>
              <p className="text-sm text-gray-500 mt-1">Update your personal information and profile picture</p>
            </div>
            {!isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors shadow-sm flex items-center gap-2"
              >
                <User size={16} />
                Edit Profile
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Profile Picture */}
          <div className="md:col-span-2">
            <label className="block text-sm font-bold text-gray-700 mb-3">Profile Picture</label>
            <div className="flex items-center gap-6">
              {profileData.profilePicture ? (
                <img
                  src={`${API_BASE_URL}${profileData.profilePicture}`}
                  alt="Profile"
                  className="h-24 w-24 rounded-full object-cover border-4 border-white shadow-lg"
                />
              ) : (
                <div className="h-24 w-24 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 flex items-center justify-center text-white font-bold text-2xl border-4 border-white shadow-lg">
                  {profileData.name.split(' ').map(n => n[0]).join('').toUpperCase() || 'SA'}
                </div>
              )}
              <div>
                <input
                  type="file"
                  id="profile-picture-upload"
                  accept="image/jpeg,image/png,image/gif"
                  onChange={handleFileUpload}
                  disabled={!isEditing}
                  className="hidden"
                />
                <label
                  htmlFor="profile-picture-upload"
                  className={`px-4 py-2 rounded-lg font-medium transition-colors shadow-sm flex items-center gap-2 ${!isEditing || uploading
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-indigo-600 text-white hover:bg-indigo-700 cursor-pointer'
                    }`}
                >
                  {uploading ? <RefreshCw size={16} className="animate-spin" /> : <Upload size={16} />}
                  {uploading ? 'Uploading...' : isEditing ? 'Upload New Picture' : 'Upload Disabled'}
                </label>
                <p className="text-xs text-gray-500 mt-2">
                  {isEditing ? 'JPG, PNG or GIF. Max size 2MB' : 'Click "Edit Profile" to upload'}
                </p>
              </div>
            </div>
          </div>

          {/* Full Name */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">Full Name</label>
            <input
              type="text"
              value={profileData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              readOnly={!isEditing}
              className={`w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all ${!isEditing ? 'bg-gray-50 cursor-not-allowed' : ''}`}
              placeholder="Enter your full name"
            />
          </div>

          {/* Address */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">Address</label>
            <input
              type="text"
              value={profileData.address}
              onChange={(e) => handleInputChange('address', e.target.value)}
              readOnly={!isEditing}
              className={`w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all ${!isEditing ? 'bg-gray-50 cursor-not-allowed' : ''}`}
              placeholder="Enter your address"
            />
          </div>

          {/* City */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">City</label>
            <input
              type="text"
              value={profileData.city}
              onChange={(e) => handleInputChange('city', e.target.value)}
              readOnly={!isEditing}
              className={`w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all ${!isEditing ? 'bg-gray-50 cursor-not-allowed' : ''}`}
              placeholder="Enter your city"
            />
          </div>

          {/* State */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">State</label>
            <input
              type="text"
              value={profileData.state}
              onChange={(e) => handleInputChange('state', e.target.value)}
              readOnly={!isEditing}
              className={`w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all ${!isEditing ? 'bg-gray-50 cursor-not-allowed' : ''}`}
              placeholder="Enter your state"
            />
          </div>

          {/* Pincode */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">Pincode</label>
            <input
              type="text"
              value={profileData.pincode}
              onChange={(e) => handleInputChange('pincode', e.target.value)}
              readOnly={!isEditing}
              className={`w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all ${!isEditing ? 'bg-gray-50 cursor-not-allowed' : ''}`}
              placeholder="Enter your pincode"
            />
          </div>

          {/* Role (Read-only) */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">Role</label>
            <input
              type="text"
              value={profileData.role}
              disabled
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed"
            />
          </div>
        </div>


        {isEditing && (
          <div className="flex justify-end gap-3 mt-8 pt-6 border-t border-gray-100">
            <button
              onClick={handleCancel}
              className="px-6 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors shadow-sm"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveProfile}
              className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors shadow-sm flex items-center gap-2"
            >
              <Save size={18} />
              Save Changes
            </button>
          </div>
        )}
      </div>
    </div>
  );
};



const NotificationSettings = () => {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/v1/notifications/recent`);
      setNotifications(response.data.slice(0, 5)); // Show only latest 5
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'order': return <ShoppingCart size={16} className="text-blue-500" />;
      case 'refund': return <RotateCcw size={16} className="text-red-500" />;
      case 'exchange': return <RefreshCw size={16} className="text-amber-500" />;
      default: return <Package size={16} className="text-gray-500" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'order': return 'bg-blue-50 border-blue-200';
      case 'refund': return 'bg-red-50 border-red-200';
      case 'exchange': return 'bg-amber-50 border-amber-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    const statusLower = status?.toLowerCase() || '';
    if (statusLower.includes('delivered') || statusLower.includes('completed') || statusLower.includes('approved')) {
      return 'bg-green-100 text-green-800 border-green-200';
    }
    if (statusLower.includes('pending') || statusLower.includes('processing')) {
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    }
    if (statusLower.includes('rejected') || statusLower.includes('failed')) {
      return 'bg-red-100 text-red-800 border-red-200';
    }
    return 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className="space-y-6">
      {/* Recent Activity Section */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-6 pb-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Bell size={20} className="text-amber-500" />
                Recent Activity
              </h2>
              <p className="text-sm text-gray-500 mt-1">Latest orders, refunds, and exchanges</p>
            </div>
            <button
              onClick={fetchNotifications}
              className="px-3 py-1.5 text-xs font-medium bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors shadow-sm flex items-center gap-2"
            >
              <RefreshCw size={14} />
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="text-center py-8 text-gray-400">
              <RefreshCw size={24} className="animate-spin mx-auto mb-2" />
              <p className="text-sm">Loading...</p>
            </div>
          ) : notifications.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <Bell size={24} className="mx-auto mb-2 opacity-50" />
              <p className="text-sm">No recent activity</p>
            </div>
          ) : (
            <div className="space-y-2">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-3 rounded-lg border ${getTypeColor(notification.type)} hover:shadow-sm transition-all`}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">{getTypeIcon(notification.type)}</div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-bold text-gray-900">{notification.title}</h4>
                      <p className="text-xs text-gray-600 mt-0.5">{notification.message}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(notification.status)}`}>
                          {notification.status}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(notification.timestamp).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
