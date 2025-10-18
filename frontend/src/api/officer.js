import apiClient from './axios';

/**
 * Get officer dashboard overview
 * @returns {Promise<object>} Dashboard data
 */
export const getOfficerOverview = async () => {
  return await apiClient.get('/officer/overview');
};

/**
 * Get workload assignment
 * @returns {Promise<object>} Workload data
 */
export const getWorkload = async () => {
  return await apiClient.get('/officer/workload');
};

/**
 * Get system alerts
 * @returns {Promise<array>} Array of alerts
 */
export const getAlerts = async () => {
  return await apiClient.get('/officer/alerts');
};

/**
 * Acknowledge alert
 * @param {string} alertId - Alert ID
 * @returns {Promise<object>} Acknowledgment result
 */
export const acknowledgeAlert = async (alertId) => {
  return await apiClient.post(`/officer/alerts/${alertId}/acknowledge`);
};

/**
 * Get processing statistics
 * @returns {Promise<object>} Processing stats
 */
export const getProcessingStatistics = async () => {
  return await apiClient.get('/officer/statistics/processing');
};

/**
 * Get fraud detection report
 * @returns {Promise<object>} Fraud detection data
 */
export const getFraudDetectionReport = async () => {
  return await apiClient.get('/officer/reports/fraud-detection');
};

/**
 * Get priority queue
 * @returns {Promise<array>} Priority applications
 */
export const getPriorityQueue = async () => {
  return await apiClient.get('/officer/queue/priority');
};

/**
 * Get document review queue
 * @returns {Promise<array>} Applications pending document review
 */
export const getDocumentReviewQueue = async () => {
  return await apiClient.get('/officer/queue/document-review');
};

/**
 * Get quality check queue
 * @returns {Promise<array>} Applications pending quality check
 */
export const getQualityCheckQueue = async () => {
  return await apiClient.get('/officer/queue/quality-check');
};

/**
 * Get application trends analytics
 * @returns {Promise<object>} Trends data
 */
export const getApplicationTrends = async () => {
  return await apiClient.get('/officer/analytics/trends');
};

/**
 * Export applications data
 * @param {object} params - Export parameters
 * @returns {Promise<Blob>} File blob for download
 */
export const exportApplications = async (params = {}) => {
  const response = await apiClient.get('/officer/export/applications', {
    params,
    responseType: 'blob', // Important for file download
  });
  return response;
};