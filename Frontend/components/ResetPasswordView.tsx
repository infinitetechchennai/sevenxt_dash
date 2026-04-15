import React, { useState, useEffect } from 'react';
import { Lock, Loader2, CheckCircle, XCircle, ArrowLeft } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { apiService } from '../services/api';
import logo from '../assets/logo.jpg';

export const ResetPasswordView: React.FC = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const token = searchParams.get('token');

    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        if (!token) {
            setError('Invalid or missing reset token');
        }
    }, [token]);

    const handleResetPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        // Validation
        if (newPassword.length < 6) {
            setError('Password must be at least 6 characters long');
            return;
        }

        if (newPassword !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (!token) {
            setError('Invalid reset token');
            return;
        }

        setIsLoading(true);

        try {
            await apiService.resetPassword(token, newPassword);
            setSuccess(true);
            setIsLoading(false);

            // Redirect to login after 3 seconds
            setTimeout(() => {
                navigate('/login');
            }, 3000);
        } catch (err) {
            console.error('Reset password error:', err);
            setError(err instanceof Error ? err.message : 'Failed to reset password. The link may have expired.');
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#f3f4f6] flex items-center justify-center p-4">
            <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl overflow-hidden flex flex-col md:flex-row animate-fadeIn min-h-[600px]">

                {/* Left Branding */}
                <div className="w-full md:w-1/2 bg-black p-12 flex flex-col justify-between text-white relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-gray-900 to-black z-0"></div>
                    <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-red-600 rounded-full opacity-20 blur-3xl"></div>
                    <div className="absolute top-12 right-12 w-32 h-32 bg-blue-600 rounded-full opacity-10 blur-2xl"></div>

                    <div className="relative z-10">
                        <div className="flex items-center gap-2 mb-8">
                            <img src={logo} className="w-[250px] h-[170px] shadow" alt="Logo" />
                        </div>
                        <h2 className="text-4xl font-bold mb-4 leading-tight">Secure Your<br />Account.</h2>
                        <p className="text-gray-400 text-sm leading-relaxed">
                            Create a strong password to protect your account.
                        </p>
                    </div>

                    <div className="relative z-10 mt-12 md:mt-0">
                        <p className="text-xs text-gray-500">© 2025 Sevenxt Inc. All rights reserved.</p>
                    </div>
                </div>

                {/* Right Form UI */}
                <div className="w-full md:w-1/2 p-12 flex flex-col justify-center relative">

                    {!success ? (
                        <div className="animate-fadeIn">
                            <button
                                onClick={() => navigate('/login')}
                                className="absolute top-8 left-8 p-2 hover:bg-gray-100 rounded-full transition-colors"
                            >
                                <ArrowLeft size={20} className="text-gray-500" />
                            </button>

                            <div className="mb-8 mt-8">
                                <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mb-4">
                                    <Lock size={24} className="text-blue-600" />
                                </div>
                                <h3 className="text-2xl font-bold text-gray-900 mb-1">Create New Password</h3>
                                <p className="text-sm text-gray-500">Enter your new password below.</p>
                            </div>

                            <form onSubmit={handleResetPassword} className="space-y-5">
                                {error && (
                                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                                        <XCircle size={18} className="text-red-500 mt-0.5 flex-shrink-0" />
                                        <p className="text-xs text-red-600 font-medium">{error}</p>
                                    </div>
                                )}

                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-2">New Password</label>
                                    <div className="relative">
                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                        <input
                                            type="password"
                                            value={newPassword}
                                            onChange={(e) => setNewPassword(e.target.value)}
                                            placeholder="••••••••"
                                            className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black transition-all"
                                            required
                                            minLength={6}
                                        />
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">Minimum 6 characters</p>
                                </div>

                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Confirm Password</label>
                                    <div className="relative">
                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                        <input
                                            type="password"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                            placeholder="••••••••"
                                            className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black transition-all"
                                            required
                                            minLength={6}
                                        />
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={isLoading || !token}
                                    className="w-full bg-black text-white py-3.5 rounded-lg font-bold text-sm hover:bg-gray-900 transition-all transform hover:scale-[1.02] flex items-center justify-center gap-2 shadow-lg disabled:opacity-70 disabled:cursor-not-allowed"
                                >
                                    {isLoading ? <Loader2 size={18} className="animate-spin" /> : 'Reset Password'}
                                </button>
                            </form>
                        </div>
                    ) : (
                        <div className="animate-fadeIn text-center">
                            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                                <CheckCircle size={32} className="text-green-600" />
                            </div>
                            <h3 className="text-2xl font-bold text-gray-900 mb-2">Password Reset Successful!</h3>
                            <p className="text-sm text-gray-500 mb-8">
                                Your password has been updated. Redirecting to login...
                            </p>

                            <button
                                onClick={() => navigate('/login')}
                                className="w-full bg-black text-white py-3.5 rounded-lg font-bold text-sm hover:bg-gray-900 transition-all flex items-center justify-center gap-2"
                            >
                                <ArrowLeft size={16} /> Go to Login
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
