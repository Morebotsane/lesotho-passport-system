import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useState } from 'react';

export default function ApplicantLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navbar */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo & Brand */}
            <div className="flex items-center space-x-8">
              <Link to="/applicant/dashboard" className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-[#00209F] to-[#009543] rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-xl">L</span>
                </div>
                <span className="text-xl font-semibold text-gray-900">
                  Lesotho Passport
                </span>
              </Link>

              {/* Navigation Links */}
              <div className="hidden md:flex space-x-6">
                <Link
                  to="/applicant/dashboard"
                  className="text-gray-700 hover:text-[#00209F] font-medium transition"
                >
                  Dashboard
                </Link>
                <Link
                  to="/applicant/applications/new"
                  className="text-gray-700 hover:text-[#00209F] font-medium transition"
                >
                  New Application
                </Link>
                <Link
                  to="/applicant/applications"
                  className="text-gray-700 hover:text-[#00209F] font-medium transition"
                >
                  My Applications
                </Link>
                <Link
                  to="/applicant/appointments"
                  className="text-gray-700 hover:text-[#00209F] font-medium transition"
                >
                  My Appointments
                </Link>
              </div>
            </div>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-3 focus:outline-none"
              >
                <div className="w-10 h-10 bg-[#00209F] rounded-full flex items-center justify-center">
                  <span className="text-white font-semibold">
                    {user?.first_name?.[0]}{user?.last_name?.[0]}
                  </span>
                </div>
                <div className="hidden md:block text-left">
                  <p className="text-sm font-medium text-gray-900">
                    {user?.first_name} {user?.last_name}
                  </p>
                  <p className="text-xs text-gray-500">Applicant</p>
                </div>
              </button>

              {/* Dropdown Menu */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 z-50">
                  <Link
                    to="/applicant/profile"
                    className="block px-4 py-2 text-gray-700 hover:bg-gray-50"
                  >
                    My Profile
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-red-600 hover:bg-gray-50"
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Page Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center text-gray-600 text-sm">
          © 2025 Lesotho Ministry of Home Affairs. All rights reserved.
        </div>
      </footer>
    </div>
  );
}