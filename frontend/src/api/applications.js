import apiClient from './axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Get document URL
 */
export const getDocumentUrl = (applicationId, documentType) => {
  const token = localStorage.getItem('token');
  return `${API_BASE_URL}/passport-applications/${applicationId}/documents/${documentType}?token=${token}`;
};

/**
 * Get document (returns blob for viewing)
 */
export const getDocument = async (applicationId, documentType) => {
  const response = await apiClient.get(
    `/passport-applications/${applicationId}/documents/${documentType}`,
    { responseType: 'blob' }
  );
  return URL.createObjectURL(response);
};

/**
 * Create new passport application
 */
export const createApplication = async (applicationData) => {
  return await apiClient.post('/passport-applications/', applicationData);
};

/**
 * Search applications with filters
 */
export const searchApplications = async (params = {}) => {
  const response = await apiClient.get('/passport-applications/', { params });
  // Backend returns object with applications array, extract it
  return response.applications || [];
};

/**
 * Get all applications (officers only)
 */
export const getAllApplications = async () => {
  return await apiClient.get('/passport-applications/all');
};

/**
 * Get my applications (for logged-in user)
 */
export const getMyApplications = async () => {
  return await apiClient.get('/passport-applications/my-applications');
};

/**
 * Get application by ID
 */
export const getApplicationById = async (applicationId) => {
  return await apiClient.get(`/passport-applications/${applicationId}`);
};

/**
 * Update application status (officers/admins only)
 */
export const updateApplicationStatus = async (applicationId, statusData) => {
  return await apiClient.put(`/passport-applications/${applicationId}/status`, statusData);
};

/**
 * Send SMS notification to applicant
 */
export const sendNotification = async (applicationId, message) => {
  return await apiClient.post(`/passport-applications/${applicationId}/notify`, { message });
};

/**
 * Request fast track processing
 */
export const requestFastTrack = async (applicationId, data) => {
  return await apiClient.post(`/passport-applications/${applicationId}/fast-track`, data);
};

/**
 * Get application statistics (overview)
 */
export const getApplicationStatistics = async () => {
  return await apiClient.get('/passport-applications/overview');
};

/**
 * Get overdue applications list
 */
export const getOverdueApplications = async () => {
  return await apiClient.get('/passport-applications/overdue/list');
};

/**
 * Track application by application number (public)
 */
export const trackApplicationByNumber = async (applicationNumber) => {
  return await apiClient.get(`/passport-applications/track/${applicationNumber}`);
};

/**
 * Warm application cache (admin only)
 */
export const warmApplicationCache = async () => {
  return await apiClient.post('/passport-applications/admin/warm-cache');
};

/**
 * Get cache health status (admin only)
 */
export const getCacheHealth = async () => {
  return await apiClient.get('/passport-applications/admin/cache-health');
};

/**
 * Upload documents for an application
 */
export const uploadDocuments = async (applicationId, formData) => {
  return await apiClient.post(`/passport-applications/${applicationId}/documents`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

// Group all functions into one object for easier importing
const applicationsApi = {
  create: createApplication,
  search: searchApplications,
  getAll: getAllApplications,
  getMyApplications,
  getById: getApplicationById,
  updateStatus: updateApplicationStatus,
  sendNotification,
  requestFastTrack,
  getStatistics: getApplicationStatistics,
  getOverdue: getOverdueApplications,
  track: trackApplicationByNumber,
  warmCache: warmApplicationCache,
  getCacheHealth,
  uploadDocuments, 
  getDocumentUrl,
  getDocument   
};

export default applicationsApi;
