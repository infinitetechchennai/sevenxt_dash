import React, { useState } from 'react';
import { Mail, Lock, ArrowRight, Loader2, ArrowLeft, CheckCircle, KeyRound } from 'lucide-react';
import logo from '../assets/logo.jpg';
import { apiService } from '../services/api';

interface LoginViewProps {
  onLogin: () => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onLogin }) => {
  const [view, setView] = useState<'login' | 'forgot' | 'otp' | 'success'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [devOtp, setDevOtp] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      console.log('Attempting login with:', { email, password: '***' });
      const response = await apiService.login({ email, password });
      console.log('Login successful:', response);
      setIsLoading(false);
      setError('');
      onLogin();
    } catch (err) {
      console.error('Login error:', err);
      setError(err instanceof Error ? err.message : 'Invalid email or password. Please try again.');
      setIsLoading(false);
    }
  };

  const handleRequestOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Please enter your email address.');
      return;
    }
    setError('');
    setIsLoading(true);

    try {
      const response = await apiService.forgotPassword(email);
      setDevOtp(response.dev_otp);
      setIsLoading(false);
      setView('otp');
    } catch (err) {
      console.error('Forgot password error:', err);
      setError(err instanceof Error ? err.message : 'Email not found. Please try again.');
      setIsLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

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
      await apiService.resetPasswordWithOTP(email, otp, newPassword);
      setIsLoading(false);
      setView('success');
    } catch (err) {
      console.error('Reset password error:', err);
      setError(err instanceof Error ? err.message : 'Invalid OTP. Please try again.');
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
              <img src={logo} className="w-[250px]  h-[170px]    shadow" />
            </div>
            <h2 className="text-4xl font-bold mb-4 leading-tight">Manage your<br />Digital Empire.</h2>
            <p className="text-gray-400 text-sm leading-relaxed">
              Complete dashboard for eCommerce, inventory & financial management.
            </p>
          </div>

          <div className="relative z-10 mt-12 md:mt-0">
            <p className="text-xs text-gray-500">© 2025 Sevenxt Inc. All rights reserved.</p>
          </div>
        </div>

        {/* Right Form UI */}
        <div className="w-full md:w-1/2 p-12 flex flex-col justify-center relative">

          {/* Login View */}
          {view === 'login' && (
            <div className="animate-fadeIn">
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-1">Admin Login</h3>
                <p className="text-sm text-gray-500">Please enter your details to sign in.</p>
              </div>

              <form onSubmit={handleLogin} className="space-y-5">
                {error && (
                  <p className="text-xs text-red-500 font-medium animate-pulse flex items-center gap-1">
                    <span className="w-1 h-1 bg-red-500 rounded-full"></span>
                    {error}
                  </p>
                )}

                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Email Address</label>
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Enter your email"
                      className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black transition-all"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Password</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black transition-all"
                      required
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <label className="flex items-center gap-2 cursor-pointer text-gray-600">
                    <input type="checkbox" className="rounded border-gray-300 text-black focus:ring-black" defaultChecked />
                    Remember me
                  </label>
                  <button type="button" onClick={() => { setView('forgot'); setError(''); }}
                    className="font-bold text-black hover:underline">
                    Forgot Password?
                  </button>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-black text-white py-3.5 rounded-lg font-bold text-sm hover:bg-gray-900 transition-all transform hover:scale-[1.02] flex items-center justify-center gap-2 shadow-lg disabled:opacity-70 disabled:cursor-not-allowed"
                >
                  {isLoading ? <Loader2 size={18} className="animate-spin" /> : <>Sign In <ArrowRight size={16} /></>}
                </button>
              </form>
            </div>
          )}

          {/* Forgot Password - Step 1: Request OTP */}
          {view === 'forgot' && (
            <div className="animate-fadeIn">
              <button
                onClick={() => { setView('login'); setError(''); }}
                className="absolute top-8 left-8 p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ArrowLeft size={20} className="text-gray-500" />
              </button>

              <div className="mb-8 mt-8">
                <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mb-4">
                  <KeyRound size={24} className="text-blue-600" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-1">Forgot Password?</h3>
                <p className="text-sm text-gray-500">Enter your email to receive a 6-digit OTP code.</p>
              </div>

              <form onSubmit={handleRequestOTP} className="space-y-6">
                {error && (
                  <p className="text-xs text-red-500 font-medium animate-pulse flex items-center gap-1">
                    {error}
                  </p>
                )}

                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Email Address</label>
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black transition-all"
                      placeholder="Enter your email"
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-black text-white py-3.5 rounded-lg font-bold text-sm hover:bg-gray-900 transition-all flex items-center justify-center gap-2"
                >
                  {isLoading ? <Loader2 size={18} className="animate-spin" /> : 'Send OTP Code'}
                </button>
              </form>
            </div>
          )}

          {/* Forgot Password - Step 2: Verify OTP & Reset */}
          {view === 'otp' && (
            <div className="animate-fadeIn">
              <button
                onClick={() => { setView('forgot'); setError(''); }}
                className="absolute top-8 left-8 p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ArrowLeft size={20} className="text-gray-500" />
              </button>

              <div className="mb-6 mt-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-1">Enter OTP</h3>
                <p className="text-sm text-gray-500">We sent a code to <span className="font-semibold text-gray-900">{email}</span></p>
              </div>

              {/* Dev OTP Display (For testing without email) */}
              {devOtp && (
                <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-lg mb-6">
                  <p className="text-xs text-yellow-800 font-semibold uppercase mb-1">Development Mode</p>
                  <p className="text-sm text-yellow-900">Your OTP is: <span className="font-mono font-bold text-lg">{devOtp}</span></p>
                </div>
              )}

              <form onSubmit={handleResetPassword} className="space-y-5">
                {error && (
                  <p className="text-xs text-red-500 font-medium animate-pulse flex items-center gap-1">
                    {error}
                  </p>
                )}

                {/* OTP Input */}
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">6-Digit OTP Code</label>
                  <input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="w-full px-4 py-3.5 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-black text-center text-2xl tracking-widest font-mono"
                    placeholder="000000"
                    maxLength={6}
                    required
                  />
                </div>

                {/* New Password */}
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">New Password</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black"
                      placeholder="Min 6 characters"
                      required
                      minLength={6}
                    />
                  </div>
                </div>

                {/* Confirm Password */}
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Confirm Password</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black"
                      placeholder="Confirm new password"
                      required
                      minLength={6}
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-black text-white py-3.5 rounded-lg font-bold text-sm hover:bg-gray-900 transition-all flex items-center justify-center gap-2"
                >
                  {isLoading ? <Loader2 size={18} className="animate-spin" /> : 'Reset Password'}
                </button>
              </form>
            </div>
          )}

          {/* Success View */}
          {view === 'success' && (
            <div className="animate-fadeIn text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle size={32} className="text-green-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Password Reset!</h3>
              <p className="text-gray-500 mb-8 text-sm">
                Your password has been successfully updated. You can now login with your new password.
              </p>

              <button
                onClick={() => { setView('login'); setPassword(''); setOtp(''); setDevOtp(undefined); }}
                className="w-full bg-black text-white py-3.5 rounded-lg font-bold text-sm hover:bg-gray-900 transition-all"
              >
                Return to Login
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
