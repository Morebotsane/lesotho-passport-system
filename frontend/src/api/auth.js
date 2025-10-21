import apiClient from './axios';

/**
 * Register new user (applicants only)
 * @param {object} userData - { email, password, full_name, phone, id_number }
 * @returns {Promise<object>} User data
 */
export const register = async (userData) => {
  return await apiClient.post('/register', userData);
};

/**
 * Login user
 * @param {object} credentials - { email, password }
 * @returns {Promise<object>} { user, token }
 */
export const login = async (credentials) => {
  return await apiClient.post('/auth/login', credentials);
};

/**
 * Logout user
 * @returns {Promise<object>} Success message
 */
export const logout = async () => {
  return await apiClient.post('/auth/logout');
};

/**
 * Get current user profile
 * @returns {Promise<object>} User data
 */
export const getCurrentUser = async () => {
  return await apiClient.get('/auth/me');
};

/**
 * Update current user profile
 * @param {object} userData - Updated user data
 * @returns {Promise<object>} Updated user data
 */
export const updateProfile = async (userData) => {
  return await apiClient.put('/auth/me', userData);
};

/**
 * Change password
 * @param {object} passwords - { current_password, new_password }
 * @returns {Promise<object>} Success message
 */
export const changePassword = async (passwords) => {
  return await apiClient.post('/auth/change-password', passwords);
};

/**
 * Test protected route (for debugging)
 * @returns {Promise<object>} Test response
 */
export const testProtectedRoute = async () => {
  return await apiClient.get('/auth/test-protected');
};