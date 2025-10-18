import apiClient from './axios';

/**
 * Get all pickup locations
 */
export const getLocations = async (activeOnly = true) => {
  return await apiClient.get('/appointments/locations', { params: { active_only: activeOnly } });
};

/**
 * Check appointment availability
 */
export const checkAvailability = async (data) => {
  return await apiClient.post('/appointments/check-availability', data);
};

/**
 * Generate time slots (admin only)
 */
export const generateTimeSlots = async (daysAhead = 30) => {
  return await apiClient.post('/appointments/admin/generate-slots', null, {
    params: { days_ahead: daysAhead }
  });
};

/**
 * Create new appointment
 */
export const createAppointment = async (data) => {
  return await apiClient.post('/appointments/', data);
};

/**
 * Get officer daily schedule (officers only)
 */
export const getOfficerSchedule = async (date) => {
  return await apiClient.get('/appointments/officer/daily-schedule', { 
    params: { date } 
  });
};

/**
 * Get my appointments
 */
export const getMyAppointments = async (includeCompleted = false) => {
  return await apiClient.get('/appointments/my-appointments', { 
    params: { include_completed: includeCompleted } 
  });
};

/**
 * Reschedule an appointment
 */
export const rescheduleAppointment = async (appointmentId, newTimeSlotId, reason) => {
  return await apiClient.put(`/appointments/${appointmentId}/reschedule`, null, {
    params: { 
      new_time_slot_id: newTimeSlotId,
      reason: reason 
    }
  });
};

/**
 * Cancel an appointment
 */
export const cancelAppointment = async (appointmentId, reason = 'User cancelled') => {
  return await apiClient.delete(`/appointments/${appointmentId}/cancel`, {
    params: { reason }
  });
};

/**
 * Check in an appointment (officers only)
 */
export const checkInAppointment = async (appointmentId) => {
  return await apiClient.post(`/appointments/${appointmentId}/check-in`);
};

/**
 * Complete an appointment (officers only)
 */
export const completeAppointment = async (appointmentId) => {
  return await apiClient.post(`/appointments/${appointmentId}/complete`);
};

/**
 * Create new location (admin only)
 */
export const createLocation = async (data) => {
  return await apiClient.post('/appointments/admin/locations', data);
};

/**
 * Update location (admin only)
 */
export const updateLocation = async (locationId, data) => {
  return await apiClient.put(`/appointments/admin/locations/${locationId}`, data);
};

/**
 * Deactivate location (admin only)
 */
export const deleteLocation = async (locationId) => {
  return await apiClient.delete(`/appointments/admin/locations/${locationId}`);
};

const appointmentsApi = {
  getLocations,
  checkAvailability,
  createAppointment,
  getMyAppointments,
  rescheduleAppointment,
  cancelAppointment,
  checkInAppointment,
  completeAppointment,
  createLocation,   
  updateLocation,      
  deleteLocation,
  getOfficerSchedule,
  generateTimeSlots  
};

export default appointmentsApi;