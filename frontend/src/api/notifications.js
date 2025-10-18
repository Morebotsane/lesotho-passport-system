import apiClient from './axios';

/**
 * Send passport ready notification
 * @param {string} applicationId - Application ID
 * @returns {Promise<object>} Notification result
 */
export const sendReadyNotification = async (applicationId) => {
  return await apiClient.post(`/notifications/${applicationId}/send-ready-notification`);
};

/**
 * Send status update notification
 * @param {string} applicationId - Application ID
 * @param {object} data - { message }
 * @returns {Promise<object>} Notification result
 */
export const sendStatusUpdate = async (applicationId, data) => {
  return await apiClient.post(`/notifications/${applicationId}/send-status-update`, data);
};

/**
 * Send pickup reminder
 * @param {string} applicationId - Application ID
 * @returns {Promise<object>} Notification result
 */
export const sendPickupReminder = async (applicationId) => {
  return await apiClient.post(`/notifications/${applicationId}/send-pickup-reminder`);
};

/**
 * Send bulk notifications
 * @param {object} data - { application_ids, message, notification_type }
 * @returns {Promise<object>} Bulk send result
 */
export const sendBulkNotifications = async (data) => {
  return await apiClient.post('/notifications/bulk-send', data);
};

/**
 * Get notifications for application
 * @param {string} applicationId - Application ID
 * @returns {Promise<array>} Array of notifications
 */
export const getApplicationNotifications = async (applicationId) => {
  return await apiClient.get(`/notifications/${applicationId}/notifications`);
};

/**
 * Check notification delivery status
 * @param {string} notificationId - Notification ID
 * @returns {Promise<object>} Delivery status
 */
export const getNotificationStatus = async (notificationId) => {
  return await apiClient.get(`/notifications/notification/${notificationId}/status`);
};

/**
 * Retry failed notification
 * @param {string} notificationId - Notification ID
 * @returns {Promise<object>} Retry result
 */
export const retryNotification = async (notificationId) => {
  return await apiClient.post(`/notifications/notification/${notificationId}/retry`);
};

/**
 * Send test SMS
 * @param {object} data - { phone, message }
 * @returns {Promise<object>} Test result
 */
export const sendTestSMS = async (data) => {
  return await apiClient.post('/notifications/test-sms', data);
};