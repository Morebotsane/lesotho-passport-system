import { Lock, LogIn, Mail } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

const handleSubmit = async (e) => {
  e.preventDefault();
  setLoading(true);
  
  try {
    console.log('🔐 Step 1: Attempting login with:', formData.email);
    
    const response = await login(formData);
    
    console.log('🔐 Step 2: Login function returned:', response);
    console.log('🎫 Step 3: Token in response?', response?.token ? 'YES ✅' : 'NO ❌');
    console.log('👤 Step 4: User in response?', response?.user ? 'YES ✅' : 'NO ❌');
    
    // Check localStorage immediately
    const savedToken = localStorage.getItem('token');
    console.log('💾 Step 5: Token in localStorage?', savedToken ? 'YES ✅' : 'NO ❌');
    console.log('💾 Token value:', savedToken);
    
    // Redirect based on user role
    if (response.user.role === 'applicant') {
      console.log('🚀 Redirecting to applicant dashboard...');
      navigate('/applicant/dashboard');
    } else if (response.user.role === 'officer') {
      console.log('🚀 Redirecting to officer dashboard...');
      navigate('/officer/dashboard');
    } else if (response.user.role === 'admin') {
      console.log('🚀 Redirecting to admin dashboard...');
      navigate('/admin/dashboard');
    } else {
      console.log('🚀 Redirecting to home...');
      navigate('/');
    }
  } catch (error) {
    console.error('❌ Login error:', error);
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center p-4">
      <div className="card w-full max-w-md p-8 animate-fade-in">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
            <span className="text-3xl">🇱🇸</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome Back
          </h1>
          <p className="text-gray-600">
            Sign in to Lesotho Passport System
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email Field */}
          <div>
            <label htmlFor="email" className="label">
              Email Address
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="input-field pl-10"
                placeholder="you@example.com"
                disabled={loading}
              />
            </div>
          </div>

          {/* Password Field */}
          <div>
            <label htmlFor="password" className="label">
              Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                className="input-field pl-10"
                placeholder="••••••••"
                disabled={loading}
              />
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Signing in...
              </>
            ) : (
              <>
                <LogIn className="h-5 w-5" />
                Sign In
              </>
            )}
          </button>
        </form>

        {/* Divider */}
        <div className="divider"></div>

        {/* Signup Link */}
        <p className="text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <Link
            to="/signup"
            className="font-medium text-primary-600 hover:text-primary-500 transition-colors"
          >
            Create one now
          </Link>
        </p>

        {/* Test Credentials (Remove in production!) */}
        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-xs text-yellow-800 font-medium mb-2">
            🧪 Development Mode - Test Credentials:
          </p>
          <p className="text-xs text-yellow-700">
            <strong>Applicant:</strong> test@applicant.com / Password#123
          </p>
        </div>
      </div>
    </div>
  );
}
