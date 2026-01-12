import React, { useState, useEffect } from "react";
import { Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { API_BASE_URL } from "./services/api";
import {
  LayoutDashboard,
  Users,
  Briefcase,
  ShoppingCart,
  Truck,
  RotateCcw,
  Package,

  CreditCard,
  Menu,
  Bell,
  Search,
  ChevronDown,
  X,
  Settings,
  DollarSign,
  Layout,
  BarChart3,
  LogOut,
  Plane,
  MapPin,
  RefreshCw
} from "lucide-react";
import { DashboardView } from "./components/DashboardView";
import { ProductsView } from "./components/ProductsView";
import { UsersView } from "./components/UsersView";
import { B2BView } from "./components/B2BView";
import { OrdersView } from "./components/OrdersView";
import { DeliveryView } from "./components/DeliveryView";
import { PorterView } from "./components/LocalDelivery";
import { RefundsView } from "./components/RefundsView";
import ExchangesView from "./components/ExchangesView";
<<<<<<< HEAD

=======
import { CategoriesView } from "./components/CategoriesView";
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
import { SettingsView } from "./components/SettingsView";
import { FinanceView } from "./components/FinanceView";
import { CampaignsView } from "./components/CampaignsView";
import CMSView from "./components/CMSView";
import { ReportsView } from "./components/ReportsView";
import { LoginView } from "./components/LoginView";
import { ViewState } from "./types";
import logo from "./assets/logo.jpg";
import { apiService } from "./services/api";


const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(apiService.isAuthenticated());
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [userProfile, setUserProfile] = useState<any>(null);

  // Fetch user profile on mount
  useEffect(() => {
    if (isAuthenticated) {
      fetchUserProfile();
    }

    // Listen for profile updates
    const handleProfileUpdate = () => {
      fetchUserProfile();
    };
    window.addEventListener('profileUpdated', handleProfileUpdate);

    return () => {
      window.removeEventListener('profileUpdated', handleProfileUpdate);
    };
  }, [isAuthenticated]);

  // Helper to check permission (case-insensitive) - MOVED TO TOP SCOPE
  const hasPermission = (permissionName: string) => {
    // If no profile yet or explicitly Admin, show all
    if (!userProfile) return true; // Default to true while loading to avoid flash, or handled downstream

    // Check if Admin
    if (userProfile.user_type === 'admin' || userProfile.role === 'admin' || userProfile.role === 'super_admin') {
      return true;
    }

    const permissions = userProfile.permissions || [];
    return permissions.some((p: string) => p.toLowerCase() === permissionName.toLowerCase());
  };

  const fetchUserProfile = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      console.log('🔍 Fetching user profile with token:', token ? 'Token exists' : 'No token');

      if (!token) {
        console.error('❌ No auth token found');
        setIsAuthenticated(false);
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/auth/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      console.log('📡 Profile API response status:', response.status);

      if (!response.ok) {
        console.error('❌ Profile fetch failed:', response.status, response.statusText);
        // If unauthorized, clear auth and redirect to login
        if (response.status === 401) {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          setIsAuthenticated(false);
          return;
        }
        throw new Error(`Failed to fetch profile: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Profile data received:', data);
      setUserProfile(data);

      // Auto-redirect if current view is not allowed
      // If user just logged in or refreshed, location might be /dashboard.
      // If user doesn't have Dashboard permission, move them to first allowed item.
      if (data.user_type !== 'admin' && data.role !== 'admin' && data.role !== 'super_admin') {
        const permissions = (data.permissions || []).map((p: string) => p.toLowerCase());
        const hasDashboard = permissions.includes('dashboard');

        if (!hasDashboard && location.pathname === '/dashboard') {
          // Find first allowed module
          const firstAllowed = menuItems.find(item => {
            if (item.id === ViewState.DASHBOARD) return false;
            // Map permission logic again here strictly for redirect
            let reqPerm = '';
            if (item.id === 'USERS') reqPerm = 'users';
            else if (item.id === 'B2B') reqPerm = 'b2b';
            else if (item.id === ViewState.ORDERS) reqPerm = 'orders';
            else if (item.id === 'FINANCE') reqPerm = 'finance';
            else if (item.id === 'REPORTS') reqPerm = 'reports';
            else if (item.id === 'DELIVERY' || item.id === 'PORTER') reqPerm = 'delivery';
            else if (item.id === 'REFUNDS' || item.id === 'EXCHANGES') reqPerm = 'refunds';
            else if (item.id === ViewState.PRODUCTS || item.id === 'CATEGORIES' || item.id === 'PRICING') reqPerm = 'products';
            else if (item.id === 'CMS') reqPerm = 'cms';
            else if (item.id === ViewState.SETTINGS) reqPerm = 'settings';

            return permissions.includes(reqPerm);
          });

          if (firstAllowed) {
            const routePath = getRoutePathFromId(firstAllowed.id);
            navigate(routePath);
          }
        }
      }
    } catch (error) {
      console.error('❌ Failed to fetch profile:', error);
      // On error, log out the user to prevent infinite loading
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      setIsAuthenticated(false);
      alert('Session expired or invalid. Please login again.');
    }
  };

  // Helper function to convert menu item ID to route path
  const getRoutePathFromId = (id: string): string => {
    const routeMap: Record<string, string> = {
      [ViewState.DASHBOARD]: '/dashboard',
      'USERS': '/users',
      'B2B': '/b2b',
      [ViewState.ORDERS]: '/orders',
      'FINANCE': '/finance',
      'REPORTS': '/reports',
      'DELIVERY': '/delivery',
      'PORTER': '/local-delivery',
      'REFUNDS': '/refunds',
      'EXCHANGES': '/exchanges',
      [ViewState.PRODUCTS]: '/products',
      'PRICING': '/campaigns',
      'CMS': '/cms',
      [ViewState.SETTINGS]: '/settings',
    };
    return routeMap[id] || '/dashboard';
  };

<<<<<<< HEAD
  // Sidebar Menu Items configuration
  const menuItems = [
    { id: ViewState.DASHBOARD, label: "Dashboard", icon: LayoutDashboard },
    { id: "USERS", label: "Users", icon: Users },
    { id: "B2B", label: "B2B Management", icon: Briefcase },
    { id: ViewState.ORDERS, label: "Orders", icon: ShoppingCart },
    { id: "FINANCE", label: "Payments & Finance", icon: DollarSign },
    { id: "REPORTS", label: "Reports", icon: BarChart3 },
    { id: "DELIVERY", label: "Delivery (Outstation)", icon: Truck },
    { id: "PORTER", label: "Local Delivery (Chennai)", icon: MapPin },
    { id: "REFUNDS", label: "Refunds", icon: RotateCcw },
    { id: "EXCHANGES", label: "Exchanges", icon: RefreshCw },
    { id: ViewState.PRODUCTS, label: "Products", icon: Package },

    { id: "PRICING", label: "Campaigns", icon: CreditCard },
    { id: "CMS", label: "CMS", icon: Layout },
    { id: ViewState.SETTINGS, label: "Settings", icon: Settings },
  ];

  // Filter menu items based on user permissions
  const filteredMenuItems = menuItems.filter(item => {
    // If no profile yet, return true (or false depending on strategy, but true avoids flicker)
    if (!userProfile) return true;

    // STRICT Mapping based on AVAILABLE_PERMISSIONS in UsersView
    switch (item.id) {
      case ViewState.DASHBOARD: return hasPermission('Dashboard');
      case 'USERS': return hasPermission('Users');
      case 'B2B': return hasPermission('B2B');
      case ViewState.ORDERS: return hasPermission('Orders');
      case 'FINANCE': return hasPermission('Finance');
      case 'REPORTS': return hasPermission('Reports');
      case 'DELIVERY':
      case 'PORTER': return hasPermission('Delivery');
      case 'REFUNDS': return hasPermission('Refunds');
      case 'EXCHANGES': return hasPermission('Exchanges');
      case ViewState.PRODUCTS:
      case 'PRICING': return hasPermission('Products');
      case 'CMS': return hasPermission('CMS');
      case ViewState.SETTINGS: return hasPermission('Settings');
      default: return false;
    }
  });
=======
  // Get current user from localStorage
  const getCurrentUser = () => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch (e) {
        console.error("Error parsing user data:", e);
        return null;
      }
    }
    return null;
  };

  const currentUser = getCurrentUser();

  // Sidebar Menu Items configuration (all available modules)
  const allMenuItems = [
    { id: ViewState.DASHBOARD, label: "Dashboard", icon: LayoutDashboard, permission: "Dashboard" },
    { id: "USERS", label: "Users", icon: Users, permission: "Users" },
    { id: "B2B", label: "B2B Management", icon: Briefcase, permission: "B2B" },
    { id: ViewState.ORDERS, label: "Orders", icon: ShoppingCart, permission: "Orders" },
    { id: "FINANCE", label: "Payments & Finance", icon: DollarSign, permission: "Finance" },
    { id: "REPORTS", label: "Reports", icon: BarChart3, permission: "Reports" },
    { id: "DELIVERY", label: "Delivery (Outstation)", icon: Truck, permission: "Delivery" },
    { id: "PORTER", label: "Local Delivery (Chennai)", icon: MapPin, permission: "Porter" },
    { id: "REFUNDS", label: "Refunds", icon: RotateCcw, permission: "Refunds" },
    { id: "EXCHANGES", label: "Exchanges", icon: RefreshCw, permission: "Exchanges" },
    { id: ViewState.PRODUCTS, label: "Products", icon: Package, permission: "Products" },
    { id: "CATEGORIES", label: "Categories", icon: FolderTree, permission: "Categories" },
    { id: "PRICING", label: "Campaigns", icon: CreditCard, permission: "Campaigns" },
    { id: "CMS", label: "CMS", icon: Layout, permission: "CMS" },
    { id: ViewState.SETTINGS, label: "Settings", icon: Settings, permission: "Settings" },
  ];

  // Filter menu items based on user role and permissions
  const menuItems = React.useMemo(() => {
    if (!currentUser) return allMenuItems;

    // Admin users see all modules
    if (currentUser.role === "admin") {
      return allMenuItems;
    }

    // Staff users see only modules they have permission for
    if (currentUser.role === "staff") {
      const userPermissions = currentUser.permissions || [];

      // Always show Dashboard for all users
      return allMenuItems.filter(item =>
        item.permission === "Dashboard" || userPermissions.includes(item.permission)
      );
    }

    // Default: show all items (fallback)
    return allMenuItems;
  }, [currentUser]);
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7

  const handleLogin = () => {
    setIsAuthenticated(true);
    navigate('/dashboard');
  };

  const handleLogout = () => {
    if (window.confirm("Are you sure you want to logout?")) {
      apiService.logout();
      setIsAuthenticated(false);
    }
  };

<<<<<<< HEAD
  // Protected Route Component
  const ProtectedRoute: React.FC<{ children: React.ReactElement; permission: string }> = ({ children, permission }) => {
    if (!userProfile) {
      return <div className="p-8">Loading profile...</div>;
=======
  const renderContent = () => {
    switch (activeView) {
      case ViewState.DASHBOARD:
        return <DashboardView onNavigate={setActiveView} />;
      case ViewState.PRODUCTS:
        return <ProductsView />;
      case "USERS":
        return <UsersView />;
      case "B2B":
        return <B2BView />;
      case ViewState.ORDERS:
        return <OrdersView />;
      case "FINANCE":
        return <FinanceView />;
      case "REPORTS":
        return <ReportsView />;
      case "DELIVERY":
        return <DeliveryView />;
      case "PORTER":
        return <PorterView />;
      case "REFUNDS":
        return <RefundsView />;
      case "EXCHANGES":
        return <ExchangesView />;
      case "CATEGORIES":
        return <CategoriesView />;
      case "PRICING":
        return <CampaignsView />;
      case "CMS":
        return <CMSView activeView={activeView} />;
      case ViewState.SETTINGS:
        return <SettingsView activeView={activeView} />;
      default:
        return (
          <div className="flex flex-col items-center justify-center h-[60vh] bg-white rounded-lg border border-dashed border-gray-300 m-4">
            <div className="p-4 rounded-full bg-gray-50 mb-4">
              <Package size={32} className="text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900">
              Work in Progress
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              This module is currently under development.
            </p>
          </div>
        );
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
    }

    if (permission && !hasPermission(permission)) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-gray-500">
          <Package size={48} className="mb-4 text-gray-300" />
          <h2 className="text-xl font-semibold text-gray-700">Access Denied</h2>
          <p className="text-sm mt-2">You do not have permission to view the {permission} module.</p>
        </div>
      );
    }

    return children;
  };

  if (!isAuthenticated) {
    return <LoginView onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen flex bg-[#f3f4f6]">
      {/* Mobile Sidebar Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
        fixed md:sticky top-0 left-0 z-50 h-screen w-64 bg-[#222a2d] text-white flex flex-col
        transform transition-transform duration-300 ease-in-out
        ${isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"}
        md:translate-x-0
        overflow-hidden shadow-xl
      `}
      >
        {/* Sidebar Header - Admin Box - Black */}
        <div className="h-24 flex items-center justify-between px-6 bg-black shrink-0">
          <div className="flex items-center">
            <img
              src={logo}
              alt="Logo"
              className="h-full w-full object-cover"
            />
          </div >
          <button
            onClick={() => setIsMobileMenuOpen(false)}
            className="md:hidden text-white/80 hover:text-white"
          >
            <X size={24} />
          </button>
        </div >

        {/* Navigation - Dark Ace */}
<<<<<<< HEAD
        <nav className="flex-1 px-3 space-y-1 py-4 bg-[#000000] overflow-y-auto no-scrollbar">
          {filteredMenuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                const routePath = getRoutePathFromId(item.id);
                navigate(routePath);
                setIsMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${location.pathname === getRoutePathFromId(item.id)
                ? "bg-[#DC2626] text-white shadow-sm ring-1 ring-white/10" /* Active Red */
                : "text-gray-300 hover:bg-white/5 hover:text-white"
                }`}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
=======
        < nav className="flex-1 px-3 space-y-1 py-4 bg-[#000000] overflow-y-auto no-scrollbar" >
          {
            menuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setActiveView(item.id);
                  setIsMobileMenuOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeView === item.id
                  ? "bg-[#DC2626] text-white shadow-sm ring-1 ring-white/10" /* Active Red */
                  : "text-gray-300 hover:bg-white/5 hover:text-white"
                  }`}
              >
                <item.icon size={20} />
                <span>{item.label}</span>
              </button>
            ))
          }
        </nav >
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7

        {/* User Profile Footer */}
        < div className="p-4 border-t border-white/10 mt-auto bg-[#222a2d] " >
          <div className="flex items-center justify-between p-2 rounded-lg hover:bg-white/5 transition-colors">
            <div
              className="flex items-center gap-3 cursor-pointer flex-1 min-w-0"
              onClick={() => navigate('/settings')}
            >
<<<<<<< HEAD
              {userProfile?.profile_picture ? (
                <img
                  src={`${API_BASE_URL}${userProfile.profile_picture}`}
                  alt="Profile"
                  className="h-9 w-9 rounded-full object-cover border-2 border-white/20"
                />
              ) : (
                <div className="h-9 w-9 rounded-full bg-[#DC2626] flex items-center justify-center text-white font-semibold border-2 border-white/20">
                  {userProfile?.name?.split(' ').map((n: string) => n[0]).join('').toUpperCase() || 'SA'}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {userProfile?.name || 'Super Admin'}
                </p>
                <p className="text-xs text-gray-400 truncate">
                  {userProfile?.email || 'admin@ecommerce.com'}
=======
              <div className="h-9 w-9 rounded-full bg-[#DC2626] flex items-center justify-center text-white font-semibold border-2 border-white/20">
                {currentUser?.name ? currentUser.name.substring(0, 2).toUpperCase() : 'SA'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {currentUser?.name || 'Super Admin'}
                </p>
                <p className="text-xs text-gray-400 truncate">
                  {currentUser?.email || 'admin@ecommerce.com'}
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="text-gray-400 hover:text-white p-1.5 hover:bg-white/10 rounded-full transition-colors"
              title="Logout"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div >
      </aside >

      {/* Main Content */}
      < main className="flex-1 flex flex-col min-w-0 overflow-hidden" >
        {/* Header */}
        < header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4 sm:px-6 lg:px-8 sticky top-0 z-30" >
          <div className="flex items-center gap-4">
            <button
              className="md:hidden text-gray-500 hover:text-gray-900"
              onClick={() => setIsMobileMenuOpen(true)}
            >
              <Menu size={24} />
            </button>
            {/* Branding Text Removed based on request to keep header clean */}
          </div>

          <div className="flex items-center gap-4">
            {/* Search */}
            <div className="hidden md:flex items-center relative">
              {/* <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" /> */}
              {/* <input
                type="text"
                placeholder="Search..."
                className="pl-10 pr-4 py-2 rounded-full bg-gray-100 border-none focus:ring-2 focus:ring-[#DC2626] text-sm w-64 outline-none text-gray-900"
                onKeyDown={(e) =>
                  e.key === "Enter" &&
                  alert(`Searching for: ${e.currentTarget.value}`)
                }
              /> */}
            </div >

            <button
              onClick={() => navigate('/settings')}
              className="relative p-2 text-gray-500 hover:bg-gray-100 rounded-full"
            >
              <Bell size={20} />
              <span className="absolute top-1.5 right-1.5 h-2.5 w-2.5 bg-red-500 rounded-full border-2 border-white"></span>
            </button>

            <div
              onClick={() => navigate('/settings')}
              className="flex items-center gap-2 cursor-pointer pl-2 border-l border-gray-200 group"
              title="Edit Profile"
            >
              {userProfile?.profile_picture ? (
                <img
                  src={`${API_BASE_URL}${userProfile.profile_picture}`}
                  alt="Profile"
                  className="h-8 w-8 rounded-full object-cover"
                />
              ) : (
                <div className="h-8 w-8 rounded-full bg-gradient-to-r from-[#DC2626] to-red-600"></div>
              )}
              <span className="text-sm font-medium text-gray-700 hidden sm:block group-hover:text-gray-900">
<<<<<<< HEAD
                {userProfile?.name || 'Super Admin'}
=======
                {currentUser?.name || 'Super Admin'}
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
              </span>
              <ChevronDown
                size={16}
                className="text-gray-400 hidden sm:block group-hover:text-gray-600"
              />
            </div>
          </div >
        </header >

        {/* Dashboard Content Area */}
        < div className="flex-1 overflow-auto p-4 sm:p-6 lg:p-8" >
<<<<<<< HEAD
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={
              <ProtectedRoute permission="Dashboard">
                <DashboardView onNavigate={(id) => navigate(getRoutePathFromId(id))} />
              </ProtectedRoute>
            } />
            <Route path="/users" element={<ProtectedRoute permission="Users"><UsersView /></ProtectedRoute>} />
            <Route path="/b2b" element={<ProtectedRoute permission="B2B"><B2BView /></ProtectedRoute>} />
            <Route path="/orders" element={<ProtectedRoute permission="Orders"><OrdersView /></ProtectedRoute>} />
            <Route path="/finance" element={<ProtectedRoute permission="Finance"><FinanceView /></ProtectedRoute>} />
            <Route path="/reports" element={<ProtectedRoute permission="Reports"><ReportsView /></ProtectedRoute>} />
            <Route path="/delivery" element={<ProtectedRoute permission="Delivery"><DeliveryView /></ProtectedRoute>} />
            <Route path="/local-delivery" element={<ProtectedRoute permission="Delivery"><PorterView /></ProtectedRoute>} />
            <Route path="/refunds" element={<ProtectedRoute permission="Refunds"><RefundsView /></ProtectedRoute>} />
            <Route path="/exchanges" element={<ProtectedRoute permission="Exchanges"><ExchangesView /></ProtectedRoute>} />
            <Route path="/products" element={<ProtectedRoute permission="Products"><ProductsView /></ProtectedRoute>} />
            <Route path="/campaigns" element={<ProtectedRoute permission="Products"><CampaignsView /></ProtectedRoute>} />
            <Route path="/cms" element={<ProtectedRoute permission="CMS"><CMSView activeView={location.pathname.substring(1)} /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute permission="Settings"><SettingsView activeView={location.pathname.substring(1)} /></ProtectedRoute>} />
          </Routes>
=======
          {renderContent()}
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
        </div >
      </main >
    </div >
  );
};

export default App;