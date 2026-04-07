import React, { useState, useRef, useEffect } from 'react';
import { apiService } from '../services/api';
import { Search, MoreVertical, Plus, Activity, CheckCircle, XCircle, AlertTriangle, X, ShieldAlert, Lock, Eye, Package, Edit, Trash2, UserX, UserCheck, MapPin, ShoppingCart, Heart, RotateCcw, FileText } from 'lucide-react';
import { MOCK_PRODUCTS } from '../constants';
import { User } from '../types';
import { exportToExcel } from '../utils/excelExport';

export const UsersView: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'B2B Users' | 'B2C Users' | 'Admin Users' | 'Staff Users' | 'Activity Logs'>('Admin Users');
    const [searchTerm, setSearchTerm] = useState('');
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchUsers = async () => {
            try {
                const data = await apiService.getUsers();
                console.log("Raw API Data:", data);

                // Map API response to User interface
                const mappedUsers: User[] = data.map((u: any) => {
                    // Map roles to UI types
                    let type: 'B2B' | 'B2C' | 'Admin' | 'Staff' = 'Staff';
                    const role = (u.role || '').toLowerCase();

                    if (u.origin === 'employee') {
                        if (role === 'admin' || role === 'super_admin') type = 'Admin';
                        else type = 'Staff';
                    } else if (u.origin === 'b2b') {
                        type = 'B2B';
                    } else if (u.origin === 'b2c') {
                        type = 'B2C';
                    }

                    return {
                        id: `${type}-${u.id}`,
                        name: u.full_name || u.business_name || u.name || 'Unknown',
                        email: u.email,
                        phone: u.phone_number || u.phone || '',
                        status: (u.status && u.status.toLowerCase() === 'active') ? 'Active' : (u.status ? u.status : 'Inactive'),
                        joinDate: u.created_at ? new Date(u.created_at).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
                        type: type,
                        permissions: u.permissions || [],
                        address: u.address || '',
                        city: u.city || '',
                        state: u.state || '',
                        pincode: u.pincode || ''
                    };
                });

                console.log("Mapped Users:", mappedUsers);
                setUsers(mappedUsers);
            } catch (error) {
                console.error("Failed to fetch users:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchUsers();
    }, []);

    // Modal State
    const [isAddUserModalOpen, setIsAddUserModalOpen] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [newUser, setNewUser] = useState({
        name: '', email: '', password: '', role: 'Staff', status: 'Active',
        address: '', city: '', state: '', pincode: ''
    });
    const [newPermissions, setNewPermissions] = useState<string[]>([]);

    // User Details Modal State
    const [historyModalOpen, setHistoryModalOpen] = useState(false);
    const [selectedHistoryUser, setSelectedHistoryUser] = useState<User | null>(null);
    const [activeModalTab, setActiveModalTab] = useState<'Orders' | 'Cart' | 'Wishlist' | 'Returns'>('Orders');

    // Action Menu State
    const [openActionMenuId, setOpenActionMenuId] = useState<string | null>(null);
    const actionMenuRef = useRef<HTMLDivElement>(null);

    const tabs = ['Admin Users', 'Staff Users', 'B2B Users', 'B2C Users', 'Activity Logs'];
    const AVAILABLE_PERMISSIONS = ['Dashboard', 'Orders', 'Products', 'Users', 'B2B', 'Finance', 'Reports', 'Delivery', 'Refunds', 'Exchanges', 'CMS', 'Settings'];

    // Click outside to close action menu
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (actionMenuRef.current && !actionMenuRef.current.contains(event.target as Node)) {
                setOpenActionMenuId(null);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    // Filter users based on the selected tab AND search term
    const filteredUsers = users.filter(user => {
        const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            user.email.toLowerCase().includes(searchTerm.toLowerCase());

        let matchesType = false;

        switch (activeTab) {
            case 'B2B Users':
                matchesType = user.type === 'B2B';
                break;
            case 'B2C Users':
                matchesType = user.type === 'B2C';
                break;
            case 'Admin Users':
                matchesType = user.type === 'Admin';
                break;
            case 'Staff Users':
                matchesType = user.type === 'Staff';
                break;
            default:
                matchesType = false;
        }

        return matchesSearch && matchesType;
    });

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'Success': return <CheckCircle size={14} className="text-green-500" />;
            case 'Failed': return <XCircle size={14} className="text-red-500" />;
            case 'Warning': return <AlertTriangle size={14} className="text-amber-500" />;
            default: return <Activity size={14} className="text-gray-500" />;
        }
    };

    const handleExport = () => {
        // Exclude internal fields or format data if necessary
        const dataToExport = filteredUsers.map(user => ({
            Name: user.name,
            Email: user.email,
            Phone: user.phone,
            Type: user.type,
            Status: user.status,
            'Join Date': user.joinDate,
            Address: user.address,
            City: user.city,
            State: user.state,
            Pincode: user.pincode,
            Permissions: (user.permissions || []).join(', ')
        }));
        exportToExcel(dataToExport, `${activeTab.replace(' ', '_')}_Export`, activeTab);
    };

    const handleSaveUser = async () => {
        if (newUser.name && newUser.email) {
            // Validate password for new users
            if (!editingId && !newUser.password) {
                alert("Please enter a password");
                return;
            }

            if (editingId) {
                // Update existing user
                try {
                    const userToUpdate = users.find(u => u.id === editingId);
                    if (!userToUpdate) return;

                    await apiService.updateUser(editingId, userToUpdate.type, {
                        name: newUser.name,
                        email: newUser.email,
                        role: newUser.role,
                        status: newUser.status,
                        address: newUser.address,
                        city: newUser.city,
                        state: newUser.state,
                        pincode: newUser.pincode,
                        permissions: newUser.role === 'Staff' ? newPermissions : undefined
                    });

                    setUsers(prev => prev.map(u => u.id === editingId ? {
                        ...u,
                        name: newUser.name,
                        email: newUser.email,
                        type: newUser.role as any,
                        status: newUser.status as any,
                        address: newUser.address,
                        city: newUser.city,
                        state: newUser.state,
                        pincode: newUser.pincode,
                        permissions: newUser.role === 'Staff' ? newPermissions : undefined
                    } : u));
                    closeUserModal();
                    alert("User updated successfully");
                } catch (error) {
                    console.error("Failed to update user:", error);
                    alert("Failed to update user");
                }
            } else {
                // Create new user - Call API
                try {
                    const createdUser = await apiService.createUser({
                        name: newUser.name,
                        email: newUser.email,
                        password: newUser.password,
                        role: newUser.role.toLowerCase(),
                        status: newUser.status.toLowerCase(),
                        address: newUser.address || undefined,
                        city: newUser.city || undefined,
                        state: newUser.state || undefined,
                        pincode: newUser.pincode || undefined,
                        permissions: newUser.role === 'Staff' ? newPermissions : undefined
                    });

                    // Add the created user to the local state
                    const user: User = {
                        id: `${newUser.role}-${createdUser.id}`,
                        name: createdUser.name || newUser.name,
                        email: createdUser.email,
                        type: newUser.role as any,
                        status: newUser.status as any,
                        joinDate: new Date().toISOString().split('T')[0],
                        address: newUser.address,
                        city: newUser.city,
                        state: newUser.state,
                        pincode: newUser.pincode,
                        permissions: newUser.role === 'Staff' ? newPermissions : undefined
                    };
                    setUsers([user, ...users]);
                    alert(`${newUser.role} user created successfully!`);
                    closeUserModal();
                } catch (error: any) {
                    console.error('Error creating user:', error);
                    alert(`Failed to create user: ${error.message || 'Unknown error'}`);
                }
            }
        } else {
            alert("Please fill in Name and Email");
        }
    };

    const closeUserModal = () => {
        setIsAddUserModalOpen(false);
        setEditingId(null);
        setNewUser({ name: '', email: '', password: '', role: 'Staff', status: 'Active', address: '', city: '', state: '', pincode: '' });
        setNewPermissions([]);
    };

    const openCreateModal = () => {
        setEditingId(null);
        setNewUser({
            name: '', email: '', password: '', role: activeTab.split(' ')[0] as any, status: 'Active',
            address: '', city: '', state: '', pincode: ''
        });
        setNewPermissions([]);
        setIsAddUserModalOpen(true);
    };

    const togglePermission = (perm: string) => {
        setNewPermissions(prev =>
            prev.includes(perm)
                ? prev.filter(p => p !== perm)
                : [...prev, perm]
        );
    };

    const handleViewHistory = (user: User) => {
        setSelectedHistoryUser(user);
        setActiveModalTab('Orders');
        setHistoryModalOpen(true);
    };

    // Action Handlers
    const handleEditUser = (user: User) => {
        setEditingId(user.id);
        setNewUser({
            name: user.name,
            email: user.email,
            password: '', // Don't show existing password
            role: user.type,
            status: user.status,
            address: user.address || '',
            city: user.city || '',
            state: user.state || '',
            pincode: user.pincode || ''
        });
        setNewPermissions(user.permissions || []);
        setIsAddUserModalOpen(true);
        setOpenActionMenuId(null);
    };

    const handleDeactivateUser = async (user: User) => {
        const newStatus = user.status === 'Active' ? 'Inactive' : 'Active';
        try {
            await apiService.updateUser(user.id, user.type, { status: newStatus });
            setUsers(prev => prev.map(u => u.id === user.id ? { ...u, status: newStatus } : u));
            setOpenActionMenuId(null);
        } catch (error) {
            console.error("Failed to update user status:", error);
            alert("Failed to update user status");
        }
    };

    const handleDeleteUser = async (user: User) => {
        if (!confirm(`Are you sure you want to delete ${user.name}?`)) return;

        try {
            await apiService.deleteUser(user.id, user.type);
            setUsers(prev => prev.filter(u => u.id !== user.id));
            setOpenActionMenuId(null);
        } catch (error) {
            console.error("Failed to delete user:", error);
            alert("Failed to delete user");
        }
    };

    // Mock Data Generators for Modal (Empty for now)
    const getMockHistory = (user: User) => [];
    const getMockCart = (user: User) => [];
    const getMockWishlist = (user: User) => [];
    const getMockReturns = (user: User) => [];

    // Explicitly show access level column for Admin OR Staff tabs
    const showAccessLevel = activeTab === 'Admin Users' || activeTab === 'Staff Users';

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
                <p className="text-gray-500 mt-1">Manage admin and staff users</p>
            </div>

            {/* Tabs */}
            <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8 overflow-x-auto no-scrollbar">
                    {tabs.map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab as any)}
                            className={`
                whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${activeTab === tab
                                    ? 'border-gray-900 text-gray-900'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
              `}
                        >
                            {tab}
                        </button>
                    ))}
                </nav>
            </div>

            {/* Content Switch */}
            {activeTab === 'Activity Logs' ? (
                /* Activity Logs View */
                <ActivityLogsSection />
            ) : (
                /* Users List View */
                <>
                    {/* Controls */}
                    <div className="flex flex-col sm:flex-row justify-between gap-4">
                        <div className="relative flex-1 max-w-2xl">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Search className="h-5 w-5 text-gray-400" />
                            </div>
                            <input
                                type="text"
                                placeholder={`Search ${activeTab.toLowerCase()}...`}
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="block w-full pl-10 pr-3 py-2 border border-gray-200 rounded-lg leading-5 bg-white placeholder-gray-400 focus:outline-none focus:placeholder-gray-500 focus:ring-1 focus:ring-gray-500 focus:border-gray-500 sm:text-sm text-gray-900"
                            />
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={handleExport}
                                className="inline-flex items-center justify-center px-4 py-2 border border-slate-200 text-sm font-medium rounded-lg shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
                            >
                                <FileText size={16} className="mr-2" />
                                Export
                            </button>
                            {(activeTab !== 'Activity Logs' && activeTab !== 'B2B Users' && activeTab !== 'B2C Users') && (
                                <button
                                    onClick={openCreateModal}
                                    className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
                                >
                                    <Plus size={16} className="mr-2" />
                                    Add New {activeTab.split(' ')[0]} User
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Table Card */}
                    <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
                        <div className="overflow-x-auto" style={{ minHeight: '300px' }}>
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-200/50">
                                    <tr>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                                            Name
                                        </th>

                                        {/* Conditional Columns based on Tab */}
                                        {activeTab === 'B2B Users' && (
                                            <>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Email</th>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Phone Number</th>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Status</th>
                                            </>
                                        )}

                                        {activeTab === 'B2C Users' && (
                                            <>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Phone Number</th>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Email</th>
                                            </>
                                        )}

                                        {(activeTab === 'Admin Users' || activeTab === 'Staff Users') && (
                                            <>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Email</th>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Status</th>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Access Level</th>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Join Date</th>
                                            </>
                                        )}

                                        <th scope="col" className="px-6 py-3 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">
                                            Action
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {filteredUsers.map((user) => (
                                        <tr key={user.id} className="hover:bg-gray-50 transition-colors relative">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="text-sm font-medium text-gray-900">{user.name}</div>
                                            </td>

                                            {/* B2B Columns */}
                                            {activeTab === 'B2B Users' && (
                                                <>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.email}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.phone || '-'}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium 
                                                            ${user.status === 'Active' || user.status === 'approved' ? 'bg-green-100 text-green-800' :
                                                                user.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                                                    user.status === 'rejected' ? 'bg-red-100 text-red-800' :
                                                                        'bg-gray-100 text-gray-800'}`}>
                                                            {user.status}
                                                        </span>
                                                    </td>
                                                </>
                                            )}

                                            {/* B2C Columns */}
                                            {activeTab === 'B2C Users' && (
                                                <>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.phone || '-'}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.email}</td>
                                                </>
                                            )}

                                            {/* Admin/Staff Columns */}
                                            {(activeTab === 'Admin Users' || activeTab === 'Staff Users') && (
                                                <>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.email}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium 
                                                            ${user.status === 'Active' || user.status === 'approved' ? 'bg-green-100 text-green-800' :
                                                                user.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                                                    user.status === 'rejected' ? 'bg-red-100 text-red-800' :
                                                                        'bg-gray-100 text-gray-800'}`}>
                                                            {user.status}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-normal max-w-[250px]">
                                                        {user.type === 'Admin' ? (
                                                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 border border-purple-200">
                                                                <ShieldAlert size={10} /> All Access
                                                            </span>
                                                        ) : (
                                                            <div className="flex flex-col items-start gap-2">
                                                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 border border-orange-200">
                                                                    <Activity size={10} /> Limited Access
                                                                </span>
                                                                <div className="flex flex-wrap gap-1.5">
                                                                    {user.permissions && user.permissions.length > 0 ? (
                                                                        user.permissions.map((perm, idx) => (
                                                                            <span key={idx} className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-100">
                                                                                {perm}
                                                                            </span>
                                                                        ))
                                                                    ) : (
                                                                        <span className="text-xs text-gray-400 italic">No specific permissions</span>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                        {user.joinDate}
                                                    </td>
                                                </>
                                            )}

                                            <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium relative">
                                                <div className="flex items-center justify-center gap-2">
                                                    {(user.type === 'B2B' || user.type === 'B2C') && (
                                                        <button
                                                            onClick={() => handleViewHistory(user)}
                                                            className="text-gray-400 hover:text-blue-600 p-1 rounded hover:bg-blue-50 transition-colors"
                                                            title="View Details"
                                                        >
                                                            <Eye className="h-5 w-5" />
                                                        </button>
                                                    )}
                                                    <div className="relative">
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                setOpenActionMenuId(openActionMenuId === user.id ? null : user.id);
                                                            }}
                                                            className={`p-1 rounded transition-colors ${openActionMenuId === user.id ? 'text-gray-900 bg-gray-100' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'}`}
                                                        >
                                                            <MoreVertical className="h-5 w-5" />
                                                        </button>

                                                        {/* Dropdown Menu */}
                                                        {openActionMenuId === user.id && (
                                                            <div
                                                                ref={actionMenuRef}
                                                                className="absolute right-0 mt-2 w-40 bg-white rounded-lg shadow-xl border border-gray-200 z-50 animate-in fade-in zoom-in-95 duration-100 origin-top-right"
                                                            >
                                                                <div className="py-1">
                                                                    <button
                                                                        onClick={() => handleEditUser(user)}
                                                                        className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                                                                    >
                                                                        <Edit size={14} /> Edit
                                                                    </button>
                                                                    <button
                                                                        onClick={() => handleDeactivateUser(user)}
                                                                        className="w-full text-left px-4 py-2 text-sm text-orange-600 hover:bg-orange-50 flex items-center gap-2"
                                                                    >
                                                                        {user.status === 'Active' ? <UserX size={14} /> : <UserCheck size={14} />}
                                                                        {user.status === 'Active' ? 'Deactivate' : 'Activate'}
                                                                    </button>
                                                                    <button
                                                                        onClick={() => handleDeleteUser(user)}
                                                                        className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                                                                    >
                                                                        <Trash2 size={14} /> Delete
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                    {filteredUsers.length === 0 && (
                                        <tr>
                                            <td colSpan={showAccessLevel ? 6 : 5} className="px-6 py-10 text-center text-gray-500">
                                                No {activeTab.toLowerCase()} found matching your criteria.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}

            {/* Add/Edit User Modal */}
            {isAddUserModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                    <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto">
                        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center sticky top-0 bg-white z-10">
                            <h3 className="font-bold text-lg text-slate-900">{editingId ? 'Edit User' : 'Create New User'}</h3>
                            <button onClick={closeUserModal} className="text-slate-400 hover:text-slate-600">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
                                <input
                                    type="text"
                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900 bg-white"
                                    value={newUser.name}
                                    onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
                                <input
                                    type="email"
                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900 bg-white"
                                    value={newUser.email}
                                    onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                                />
                            </div>

                            {/* Password Field - Only for new users or when editing */}
                            {!editingId && (
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
                                    <input
                                        type="password"
                                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900 bg-white"
                                        value={newUser.password}
                                        onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                                        placeholder="Enter password"
                                    />
                                </div>
                            )}

                            {/* Role and Status */}
                            <div className="grid grid-cols-2 gap-4">
                                {/* Show role selector only for B2B/B2C users, hide for Admin/Staff */}
                                {(newUser.role === 'B2B' || newUser.role === 'B2C') ? (
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Role</label>
                                        <select
                                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900 bg-white"
                                            value={newUser.role}
                                            onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                                        >
                                            <option value="B2B">B2B Customer</option>
                                            <option value="B2C">B2C Customer</option>
                                        </select>
                                    </div>
                                ) : (
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Role</label>
                                        <div className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 text-gray-700 flex items-center gap-2">
                                            <ShieldAlert size={16} className={newUser.role === 'Admin' ? 'text-purple-600' : 'text-orange-600'} />
                                            <span className="font-medium">{newUser.role === 'Admin' ? 'Administrator (All Access)' : 'Staff User (Limited Access)'}</span>
                                        </div>
                                    </div>
                                )}
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Status</label>
                                    <select
                                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900 bg-white"
                                        value={newUser.status}
                                        onChange={(e) => setNewUser({ ...newUser, status: e.target.value })}
                                    >
                                        <option value="Active">Active</option>
                                        <option value="Inactive">Inactive</option>
                                    </select>
                                </div>
                            </div>

                            {/* Address Fields - Only for Staff users */}
                            {(newUser.role === 'Staff' || newUser.role === 'Admin') && (
                                <div className="border-t border-slate-100 pt-4">
                                    <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                                        <MapPin size={16} className="text-slate-400" /> Address Details
                                    </label>
                                    <div className="space-y-3">
                                        <div>
                                            <label className="block text-xs font-medium text-slate-500 mb-1">Address</label>
                                            <input
                                                type="text"
                                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900 bg-white"
                                                placeholder="Street address, apartment, suite, unit, etc."
                                                value={newUser.address}
                                                onChange={(e) => setNewUser({ ...newUser, address: e.target.value })}
                                            />
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="block text-xs font-medium text-slate-500 mb-1">City</label>
                                                <input
                                                    type="text"
                                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900 bg-white"
                                                    value={newUser.city}
                                                    onChange={(e) => setNewUser({ ...newUser, city: e.target.value })}
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-xs font-medium text-slate-500 mb-1">State</label>
                                                <input
                                                    type="text"
                                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900 bg-white"
                                                    value={newUser.state}
                                                    onChange={(e) => setNewUser({ ...newUser, state: e.target.value })}
                                                />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-slate-500 mb-1">Pincode</label>
                                            <input
                                                type="text"
                                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-gray-900 bg-white"
                                                value={newUser.pincode}
                                                onChange={(e) => setNewUser({ ...newUser, pincode: e.target.value })}
                                            />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Permission Selection for Staff */}
                            {newUser.role === 'Staff' && (
                                <div className="border-t border-slate-100 pt-4">
                                    <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                                        <Lock size={16} className="text-slate-400" /> Access Permissions
                                    </label>
                                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 grid grid-cols-2 gap-2">
                                        {AVAILABLE_PERMISSIONS.map(perm => (
                                            <label key={perm} className="flex items-center gap-2 cursor-pointer hover:bg-white p-1.5 rounded transition-colors">
                                                <input
                                                    type="checkbox"
                                                    className="rounded border-slate-300 text-gray-900 focus:ring-gray-900"
                                                    checked={newPermissions.includes(perm)}
                                                    onChange={() => togglePermission(perm)}
                                                />
                                                <span className="text-sm text-slate-700">{perm}</span>
                                            </label>
                                        ))}
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">Select modules this staff member can access.</p>
                                </div>
                            )}

                            <div className="pt-2">
                                <button
                                    onClick={handleSaveUser}
                                    className="w-full py-2.5 bg-gray-900 text-white font-bold rounded-lg hover:bg-gray-800 transition-colors shadow-sm"
                                >
                                    {editingId ? 'Update User' : 'Create User'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* User Details & History Modal */}
            {historyModalOpen && selectedHistoryUser && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                    <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl overflow-hidden animate-in zoom-in-95 duration-200 max-h-[90vh] flex flex-col">
                        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 sticky top-0 bg-white z-10">
                            <div>
                                <h3 className="font-bold text-lg text-slate-900">User Details</h3>
                                <p className="text-sm text-slate-500">Customer: <span className="font-medium text-slate-900">{selectedHistoryUser.name}</span></p>
                            </div>
                            <button onClick={() => setHistoryModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                                <X size={20} />
                            </button>
                        </div>

                        {/* Modal Navigation */}
                        <div className="border-b border-slate-200 px-6 bg-white">
                            <nav className="-mb-px flex space-x-6">
                                {['Orders', 'Cart', 'Wishlist', 'Returns'].map((tab) => (
                                    <button
                                        key={tab}
                                        onClick={() => setActiveModalTab(tab as any)}
                                        className={`
                                    whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2
                                    ${activeModalTab === tab
                                                ? 'border-indigo-600 text-indigo-600'
                                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                                `}
                                    >
                                        {tab === 'Orders' && <FileText size={16} />}
                                        {tab === 'Cart' && <ShoppingCart size={16} />}
                                        {tab === 'Wishlist' && <Heart size={16} />}
                                        {tab === 'Returns' && <RotateCcw size={16} />}
                                        {tab}
                                    </button>
                                ))}
                            </nav>
                        </div>

                        <div className="overflow-y-auto bg-slate-50 flex-1 p-6">
                            {/* Address Card */}
                            <div className="bg-white p-4 rounded-lg border border-slate-200 mb-6 shadow-sm">
                                <h4 className="text-sm font-bold text-gray-900 mb-2 flex items-center gap-2">
                                    <MapPin size={16} className="text-blue-600" /> Registered Address
                                </h4>
                                {selectedHistoryUser.address ? (
                                    <div className="text-sm text-gray-700">
                                        <p className="font-medium">{selectedHistoryUser.address}</p>
                                        <p>{selectedHistoryUser.city}, {selectedHistoryUser.state}</p>
                                        <p className="font-mono text-xs text-gray-500 mt-1">PIN: {selectedHistoryUser.pincode}</p>
                                    </div>
                                ) : (
                                    <p className="text-sm text-gray-400 italic">No address details available.</p>
                                )}
                            </div>

                            {/* Tab Content */}
                            <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">

                                {/* ORDERS TAB */}
                                {activeModalTab === 'Orders' && (
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-slate-50">
                                            <tr>
                                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Order ID</th>
                                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Date</th>
                                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase">Items</th>
                                                <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase">Amount</th>
                                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {getMockHistory(selectedHistoryUser).map((order) => (
                                                <tr key={order.id} className="hover:bg-slate-50">
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600">{order.id}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{order.date}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-center">{order.items}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900 text-right">{order.amount}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${order.status === 'Delivered' ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'
                                                            }`}>
                                                            {order.status}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}

                                {/* CART TAB */}
                                {activeModalTab === 'Cart' && (
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-slate-50">
                                            <tr>
                                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Product</th>
                                                <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase">Price</th>
                                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase">Qty</th>
                                                <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase">Total</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {getMockCart(selectedHistoryUser).map((item) => (
                                                <tr key={item.id} className="hover:bg-slate-50">
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className="flex items-center gap-3">
                                                            <img src={item.image} alt="" className="h-8 w-8 rounded object-cover bg-gray-100" />
                                                            <div className="text-sm font-medium text-gray-900">{item.name}</div>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">₹{item.b2cPrice}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center font-bold">{(item as any).qty}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-indigo-600 text-right">₹{item.b2cPrice * (item as any).qty}</td>
                                                </tr>
                                            ))}
                                            {getMockCart(selectedHistoryUser).length === 0 && (
                                                <tr><td colSpan={4} className="px-6 py-8 text-center text-gray-500">Cart is empty</td></tr>
                                            )}
                                        </tbody>
                                    </table>
                                )}

                                {/* WISHLIST TAB */}
                                {activeModalTab === 'Wishlist' && (
                                    <div className="p-4 grid grid-cols-2 gap-4">
                                        {getMockWishlist(selectedHistoryUser).map((item) => (
                                            <div key={item.id} className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-slate-50 transition-colors">
                                                <img src={item.image} alt="" className="h-12 w-12 rounded object-cover bg-gray-100" />
                                                <div className="flex-1 min-w-0">
                                                    <h5 className="text-sm font-medium text-gray-900 truncate">{item.name}</h5>
                                                    <p className="text-xs text-gray-500">{item.brand}</p>
                                                    <p className="text-sm font-bold text-indigo-600 mt-1">₹{item.b2cPrice}</p>
                                                </div>
                                                <div className="text-right">
                                                    {item.stock > 0
                                                        ? <span className="text-[10px] bg-green-100 text-green-700 px-2 py-1 rounded font-bold">In Stock</span>
                                                        : <span className="text-[10px] bg-red-100 text-red-700 px-2 py-1 rounded font-bold">Out of Stock</span>
                                                    }
                                                </div>
                                            </div>
                                        ))}
                                        {getMockWishlist(selectedHistoryUser).length === 0 && (
                                            <div className="col-span-2 text-center py-8 text-gray-500">No items in wishlist</div>
                                        )}
                                    </div>
                                )}

                                {/* RETURNS TAB */}
                                {activeModalTab === 'Returns' && (
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-slate-50">
                                            <tr>
                                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Return ID</th>
                                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Product</th>
                                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Reason</th>
                                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Date</th>
                                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {getMockReturns(selectedHistoryUser).map((ret) => (
                                                <tr key={ret.id} className="hover:bg-slate-50">
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">{ret.id}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{ret.product}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{ret.reason}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{ret.date}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${ret.status === 'Processed' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                                            }`}>
                                                            {ret.status}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                            {getMockReturns(selectedHistoryUser).length === 0 && (
                                                <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">No returns found</td></tr>
                                            )}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>

                        <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end sticky bottom-0 z-10">
                            <button
                                onClick={() => setHistoryModalOpen(false)}
                                className="px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 font-medium text-sm"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// Activity Logs Section Component
const ActivityLogsSection: React.FC = () => {
    const [activityLogs, setActivityLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [filterUserType, setFilterUserType] = useState<string>('');
    const [filterModule, setFilterModule] = useState<string>('');
    const [filterStatus, setFilterStatus] = useState<string>('');
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchActivityLogs();
    }, [filterUserType, filterModule, filterStatus, searchTerm]);

    const fetchActivityLogs = async () => {
        try {
            setLoading(true);
            const logs = await apiService.getActivityLogs({
                limit: 100,
                user_type: filterUserType || undefined,
                module: filterModule || undefined,
                status: filterStatus || undefined,
                search: searchTerm || undefined
            });

            // Show both Admin and Staff activities
            setActivityLogs(logs);
        } catch (error) {
            console.error('Failed to fetch activity logs:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async () => {
        try {
            const blob = await apiService.exportActivityLogs({
                user_type: filterUserType || undefined,
                module: filterModule || undefined,
                status: filterStatus || undefined,
                search: searchTerm || undefined
            });

            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `activity_logs_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Failed to export activity logs:', error);
            alert('Failed to export activity logs');
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'Success': return <CheckCircle size={14} className="text-green-500" />;
            case 'Failed': return <XCircle size={14} className="text-red-500" />;
            case 'Warning': return <AlertTriangle size={14} className="text-amber-500" />;
            default: return <Activity size={14} className="text-gray-500" />;
        }
    };

    const formatTimestamp = (timestamp: string) => {
        const date = new Date(timestamp);
        return date.toLocaleString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="space-y-4">
            {/* Filters */}
            <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Search</label>
                        <input
                            type="text"
                            placeholder="Search logs..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-gray-500 text-gray-900"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">User Type</label>
                        <select
                            value={filterUserType}
                            onChange={(e) => setFilterUserType(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-gray-500 text-gray-900"
                        >
                            <option value="">All Types</option>
                            <option value="Admin">Admin</option>
                            <option value="Staff">Staff</option>
                            {/* <option value="B2B">B2B</option>
                            <option value="B2C">B2C</option> */}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Module</label>
                        <select
                            value={filterModule}
                            onChange={(e) => setFilterModule(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-gray-500 text-gray-900"
                        >
                            <option value="">All Modules</option>
                            <option value="Users">Users</option>
                            <option value="Orders">Orders</option>
                            <option value="Products">Products</option>
                            <option value="Delivery">Delivery</option>
                            <option value="Refunds">Refunds</option>
                            <option value="Authentication">Authentication</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
                        <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-gray-500 text-gray-900"
                        >
                            <option value="">All Status</option>
                            <option value="Success">Success</option>
                            <option value="Failed">Failed</option>
                            <option value="Warning">Warning</option>
                        </select>
                    </div>
                </div>
                <div className="mt-4 flex justify-end">
                    <button
                        onClick={handleExport}
                        className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                    >
                        <FileText size={16} className="mr-2" />
                        Export CSV
                    </button>
                </div>
            </div>

            {/* Activity Logs Table */}
            <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                    <h3 className="text-sm font-bold text-gray-700 uppercase">Activity Logs</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-white">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">User</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Role</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Action</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Module</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Details</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Timestamp</th>
                                <th className="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase">Status</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {loading ? (
                                <tr>
                                    <td colSpan={7} className="px-6 py-10 text-center text-gray-500">
                                        Loading activity logs...
                                    </td>
                                </tr>
                            ) : activityLogs.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="px-6 py-10 text-center text-gray-500">
                                        No activity logs found.
                                    </td>
                                </tr>
                            ) : (
                                activityLogs.map((log) => (
                                    <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900">{log.user_name || 'System'}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                                                ${log.user_type === 'Admin' ? 'bg-purple-100 text-purple-800' :
                                                    log.user_type === 'Staff' ? 'bg-blue-100 text-blue-800' :
                                                        log.user_type === 'B2B' ? 'bg-green-100 text-green-800' :
                                                            log.user_type === 'B2C' ? 'bg-orange-100 text-orange-800' :
                                                                'bg-gray-100 text-gray-800'}`}>
                                                {log.user_type || 'N/A'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{log.action}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{log.module}</td>
                                        <td className="px-6 py-4 text-sm text-gray-500 max-w-md truncate">{log.details || '-'}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {formatTimestamp(log.timestamp)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-center">
                                            <div className="flex items-center justify-center gap-1">
                                                {getStatusIcon(log.status)}
                                                <span className="text-xs text-gray-600">{log.status}</span>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
