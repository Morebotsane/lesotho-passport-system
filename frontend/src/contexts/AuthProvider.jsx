import { useState, useEffect } from 'react';
import { AuthContext } from './AuthContext';
import { login as apiLogin, logout as apiLogout, register as apiRegister, getCurrentUser } from '../api/auth';
import { setAuthToken, setUserData, getUserData, clearAuthData } from '../utils/storage';
import toast from 'react-hot-toast';

// AuthProvider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Initialize: Check if user is already logged in
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedUser = getUserData();
        if (storedUser) {
          // Verify token is still valid by fetching current user
          const currentUser = await getCurrentUser();
          setUser(currentUser);
          setIsAuthenticated(true);
        }
      } catch {
        // Token invalid or expired, clear auth data
        clearAuthData();
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  // Login function
// Login function
const login = async (credentials) => {
  try {
    console.log('🔑 AuthProvider: Calling login API...');
    const response = await apiLogin(credentials);
    
    console.log('🔑 AuthProvider: Response received:', response);
    console.log('🔑 AuthProvider: access_token exists?', !!response.access_token);
    
    // Backend returns 'access_token', not 'token'
    if (response.access_token) {
      setAuthToken(response.access_token);
      console.log('💾 AuthProvider: Token saved ✅');
    } else {
      console.error('❌ No access_token in response!');
    }
    
    if (response.user) {
      setUserData(response.user);
      setUser(response.user);
      setIsAuthenticated(true);
      console.log('👤 AuthProvider: User set ✅');
    }
    
    // Construct full name from first_name and last_name 
    const fullName = `${response.user.first_name} ${response.user.last_name}`;  
    toast.success(`Welcome back, ${fullName}!`);
    
    return response;
  } catch (error) {
    console.error('❌ Login error:', error);
    toast.error(error.message || 'Login failed');
    throw error;
  }
};

  // Register function
  const register = async (userData) => {
    try {
      const user = await apiRegister(userData);
      
      toast.success('Account created successfully! Please login.');
      return user;
    } catch (error) {
      toast.error(error.message || 'Registration failed');
      throw error;
    }
  };

  // Logout function
  const logout = async () => {
    try {
      await apiLogout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local data regardless of API success
      clearAuthData();
      setUser(null);
      setIsAuthenticated(false);
      toast.success('Logged out successfully');
    }
  };

  // Refresh user data
  const refreshUser = async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setUserData(currentUser);
      return currentUser;
    } catch (error) {
      console.error('Refresh user error:', error);
      throw error;
    }
  };

  // Check if user has specific role
  const hasRole = (role) => {
    return user?.role === role;
  };

  // Check if user has any of the specified roles
  const hasAnyRole = (roles) => {
    return roles.includes(user?.role);
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUser,
    hasRole,
    hasAnyRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
