import React, { useState, useEffect } from 'react';
import { Key, Search, CheckCircle, XCircle, Loader2, User } from 'lucide-react';
import { apiService } from '../services/api';

interface UserData {
    id: number;
    email: string;
    name: string | null;
    role: string;
    status: string;
}

export const AdminResetPasswordView: React.FC = () => {
    const [users, setUsers] = useState<UserData[]>([]);
    const [filteredUsers, setFilteredUsers] = useState<UserData[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedUser, setSelectedUser] = useState<UserData | null>(null);
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [success, setSuccess] = useState<string>('');
    const [error, setError] = useState<string>('');

    // Load users on mount
    useEffect(() => {
        loadUsers();
    }, []);

    // Filter users based on search
    useEffect(() => {
        if (searchQuery.trim() === '') {
            setFilteredUsers(users);
        } else {
            const query = searchQuery.toLowerCase();
            setFilteredUsers(
                users.filter(
                    (user) =>
                        user.email.toLowerCase().includes(query) ||
                        (user.name && user.name.toLowerCase().includes(query))
                )
            );
        }
    }, [searchQuery, users]);

    const loadUsers = async () => {
        try {
            const allUsers = await apiService.getUsers();
            // Only show admin and staff users
            const employeeUsers = allUsers.filter(
                (u) => u.role === 'admin' || u.role === 'staff'
            );
            setUsers(employeeUsers);
            setFilteredUsers(employeeUsers);
        } catch (err) {
            console.error('Failed to load users:', err);
            setError('Failed to load users');
        }
    };

    const handleResetPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        // Validation
        if (!selectedUser) {
            setError('Please select a user');
            return;
        }

        if (newPassword.length < 6) {
            setError('Password must be at least 6 characters long');
            return;
        }

        if (newPassword !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        setIsLoading(true);

        try {
            const response = await apiService.adminResetPassword(
                selectedUser.id,
                newPassword
            );

            setSuccess(
                `Password for ${response.email} has been reset successfully!`
            );
            setNewPassword('');
            setConfirmPassword('');
            setSelectedUser(null);
            setSearchQuery('');
            setIsLoading(false);

            // Clear success message after 5 seconds
            setTimeout(() => setSuccess(''), 5000);
        } catch (err) {
            console.error('Reset password error:', err);
            setError(
                err instanceof Error
                    ? err.message
                    : 'Failed to reset password. Please try again.'
            );
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                            <Key size={20} className="text-blue-600" />
                        </div>
                        <h1 className="text-2xl font-bold text-gray-900">
                            Admin Password Reset
                        </h1>
                    </div>
                    <p className="text-sm text-gray-500">
                        Reset passwords for admin and staff users
                    </p>
                </div>

                {/* Success/Error Messages */}
                {success && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 flex items-start gap-3 animate-fadeIn">
                        <CheckCircle size={20} className="text-green-600 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-green-800 font-medium">{success}</p>
                    </div>
                )}

                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3 animate-fadeIn">
                        <XCircle size={20} className="text-red-600 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-red-800 font-medium">{error}</p>
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Left: User Selection */}
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">
                            Select User
                        </h2>

                        {/* Search */}
                        <div className="relative mb-4">
                            <Search
                                size={18}
                                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                            />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search by name or email..."
                                className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                            />
                        </div>

                        {/* User List */}
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                            {filteredUsers.length === 0 ? (
                                <p className="text-sm text-gray-500 text-center py-8">
                                    No users found
                                </p>
                            ) : (
                                filteredUsers.map((user) => (
                                    <button
                                        key={user.id}
                                        onClick={() => {
                                            setSelectedUser(user);
                                            setError('');
                                            setSuccess('');
                                        }}
                                        className={`w-full text-left p-3 rounded-lg border transition-all ${selectedUser?.id === user.id
                                                ? 'bg-blue-50 border-blue-500 ring-2 ring-blue-200'
                                                : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                            }`}
                                    >
                                        <div className="flex items-start gap-3">
                                            <div
                                                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${selectedUser?.id === user.id
                                                        ? 'bg-blue-600'
                                                        : 'bg-gray-200'
                                                    }`}
                                            >
                                                <User
                                                    size={16}
                                                    className={
                                                        selectedUser?.id === user.id
                                                            ? 'text-white'
                                                            : 'text-gray-600'
                                                    }
                                                />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium text-gray-900 truncate">
                                                    {user.name || 'No Name'}
                                                </p>
                                                <p className="text-xs text-gray-500 truncate">
                                                    {user.email}
                                                </p>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <span
                                                        className={`text-xs px-2 py-0.5 rounded-full ${user.role === 'admin'
                                                                ? 'bg-purple-100 text-purple-700'
                                                                : 'bg-blue-100 text-blue-700'
                                                            }`}
                                                    >
                                                        {user.role}
                                                    </span>
                                                    <span
                                                        className={`text-xs px-2 py-0.5 rounded-full ${user.status === 'active'
                                                                ? 'bg-green-100 text-green-700'
                                                                : 'bg-gray-100 text-gray-700'
                                                            }`}
                                                    >
                                                        {user.status}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </button>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Right: Password Reset Form */}
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">
                            Reset Password
                        </h2>

                        {!selectedUser ? (
                            <div className="flex flex-col items-center justify-center py-16 text-center">
                                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                                    <User size={32} className="text-gray-400" />
                                </div>
                                <p className="text-sm text-gray-500">
                                    Select a user from the list to reset their password
                                </p>
                            </div>
                        ) : (
                            <form onSubmit={handleResetPassword} className="space-y-5">
                                {/* Selected User Info */}
                                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                                    <p className="text-xs font-semibold text-blue-900 uppercase mb-1">
                                        Selected User
                                    </p>
                                    <p className="text-sm font-medium text-blue-900">
                                        {selectedUser.name || 'No Name'}
                                    </p>
                                    <p className="text-xs text-blue-700">{selectedUser.email}</p>
                                </div>

                                {/* New Password */}
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-2">
                                        New Password
                                    </label>
                                    <div className="relative">
                                        <Key
                                            className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                                            size={18}
                                        />
                                        <input
                                            type="password"
                                            value={newPassword}
                                            onChange={(e) => setNewPassword(e.target.value)}
                                            placeholder="Enter new password"
                                            className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                                            required
                                            minLength={6}
                                        />
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        Minimum 6 characters
                                    </p>
                                </div>

                                {/* Confirm Password */}
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-2">
                                        Confirm Password
                                    </label>
                                    <div className="relative">
                                        <Key
                                            className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                                            size={18}
                                        />
                                        <input
                                            type="password"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                            placeholder="Confirm new password"
                                            className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                                            required
                                            minLength={6}
                                        />
                                    </div>
                                </div>

                                {/* Submit Button */}
                                <button
                                    type="submit"
                                    disabled={isLoading}
                                    className="w-full bg-blue-600 text-white py-3.5 rounded-lg font-bold text-sm hover:bg-blue-700 transition-all transform hover:scale-[1.02] flex items-center justify-center gap-2 shadow-lg disabled:opacity-70 disabled:cursor-not-allowed"
                                >
                                    {isLoading ? (
                                        <Loader2 size={18} className="animate-spin" />
                                    ) : (
                                        <>
                                            <Key size={18} />
                                            Reset Password
                                        </>
                                    )}
                                </button>
                            </form>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
