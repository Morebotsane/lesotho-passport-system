import apiClient from './axios';

/**
 * Get system health status
 * @returns {Promise<object>} Health check data
 */
export const getSystemHealth = async () => {
  return await apiClient.get('/health/detailed');
};

/**
 * Get basic health check
 * @returns {Promise<object>} Basic health status
 */
export const getBasicHealth = async () => {
  return await apiClient.get('/health/');
};

/**
 * Get database health
 * @returns {Promise<object>} Database status
 */
export const getDatabaseHealth = async () => {
  return await apiClient.get('/health/database');
};

/**
 * Get Redis health
 * @returns {Promise<object>} Redis status
 */
export const getRedisHealth = async () => {
  return await apiClient.get('/health/redis');
};

/**
 * Get Celery health
 * @returns {Promise<object>} Celery worker status
 */
export const getCeleryHealth = async () => {
  return await apiClient.get('/health/celery');
};

/**
 * Get startup checklist
 * @returns {Promise<object>} Complete startup verification
 */
export const getStartupChecklist = async () => {
  return await apiClient.get('/health/startup-checklist');
};

/**
 * Get metrics overview
 * @returns {Promise<object>} System metrics overview
 */
export const getMetricsOverview = async () => {
  return await apiClient.get('/metrics/overview');
};

/**
 * Get API performance metrics
 * @param {object} params - { hours: 24 }
 * @returns {Promise<object>} API performance data
 */
export const getApiPerformance = async (params = { hours: 24 }) => {
  return await apiClient.get('/metrics/api-performance', { params });
};

/**
 * Get error statistics
 * @param {object} params - { hours: 24 }
 * @returns {Promise<object>} Error stats
 */
export const getErrorStatistics = async (params = { hours: 24 }) => {
  return await apiClient.get('/metrics/errors', { params });
};

/**
 * Get notification metrics
 * @param {object} params - { days: 7 }
 * @returns {Promise<object>} Notification metrics
 */
export const getNotificationMetrics = async (params = { days: 7 }) => {
  return await apiClient.get('/metrics/notifications', { params });
};

/**
 * Get Celery metrics
 * @returns {Promise<object>} Celery worker metrics
 */
export const getCeleryMetrics = async () => {
  return await apiClient.get('/metrics/celery');
};

/**
 * Get metrics dashboard
 * @returns {Promise<object>} Formatted dashboard with alerts
 */
export const getMetricsDashboard = async () => {
  return await apiClient.get('/metrics/dashboard');
};

/**
 * Get error patterns
 * @param {object} params - { hours: 24 }
 * @returns {Promise<object>} Error pattern analysis
 */
export const getErrorPatterns = async (params = { hours: 24 }) => {
  return await apiClient.get('/metrics/errors/patterns', { params });
};

/**
 * Get critical errors
 * @param {object} params - { hours: 24 }
 * @returns {Promise<array>} Recent critical errors
 */
export const getCriticalErrors = async (params = { hours: 24 }) => {
  return await apiClient.get('/metrics/errors/critical', { params });
};

/**
 * Get active alerts
 * @returns {Promise<array>} Active system alerts
 */
export const getActiveAlerts = async () => {
  return await apiClient.get('/metrics/alerts');
};

/**
 * Check alert status
 * @returns {Promise<object>} Quick alert status (healthy/warning/critical)
 */
export const checkAlertStatus = async () => {
  return await apiClient.get('/metrics/alerts/check');
};

/**
 * Test query performance (diagnostics)
 * @returns {Promise<object>} Query performance test results
 */
export const testQueryPerformance = async () => {
  return await apiClient.get('/diagnostics/query-performance');
};

/**
 * Get table statistics (diagnostics)
 * @returns {Promise<object>} Database table stats
 */
export const getTableStatistics = async () => {
  return await apiClient.get('/diagnostics/table-stats');
};

/**
 * Create officer account (admin only)
 * @param {object} userData - { email, password, full_name, role }
 * @returns {Promise<object>} Created user
 */
export const createOfficer = async (userData) => {
  return await apiClient.post('/auth/register', {
    ...userData,
    role: 'officer', // Force officer role
  });
};

/**
 * Create admin account (admin only)
 * @param {object} userData - { email, password, full_name, role }
 * @returns {Promise<object>} Created user
 */
export const createAdmin = async (userData) => {
  return await apiClient.post('/auth/register', {
    ...userData,
    role: 'admin', // Force admin role
  });
};

/**
 * Get all officers
 */
export const getOfficers = async () => {
  return await apiClient.get('/users/officers');
};

/**
 * Get all users (admin only)
 */
export const getAllUsers = async (params = {}) => {
  return await apiClient.get('/users/', { params });
};

/**
 * Get user by ID
 */
export const getUserById = async (userId) => {
  return await apiClient.get(`/users/${userId}`);
};

/**
 * Update user (admin only)
 */
export const updateUser = async (userId, userData) => {
  return await apiClient.put(`/users/${userId}`, userData);
};

/**
 * Deactivate user (admin only)
 */
export const deactivateUser = async (userId) => {
  return await apiClient.put(`/users/${userId}/deactivate`);
};

/**
 * Activate user (admin only)
 */
export const activateUser = async (userId) => {
  return await apiClient.put(`/users/${userId}/activate`);
};

/**
 * Reset user password (admin only)
 */
export const resetUserPassword = async (userId, newPassword) => {
  return await apiClient.put(`/users/${userId}/reset-password`, { new_password: newPassword });
};
