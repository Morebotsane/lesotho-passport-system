// API Configuration
export const API_BASE_URL = '';
export const API_VERSION = '/api/v1';

// Full API URL
export const API_URL = `${API_BASE_URL}${API_VERSION}`;

// User Roles
export const USER_ROLES = {
  APPLICANT: 'applicant',
  OFFICER: 'officer',
  ADMIN: 'admin',
};

// Application Status
export const APPLICATION_STATUS = {
  SUBMITTED: 'submitted',
  UNDER_REVIEW: 'under_review',
  DOCUMENTS_REQUIRED: 'documents_required',
  APPROVED: 'approved',
  REJECTED: 'rejected',
  READY_FOR_PICKUP: 'ready_for_pickup',
  COLLECTED: 'collected',
  FAST_TRACK: 'fast_track',
};

// Status Display Names (for UI)
export const STATUS_LABELS = {
  [APPLICATION_STATUS.SUBMITTED]: 'Submitted',
  [APPLICATION_STATUS.UNDER_REVIEW]: 'Under Review',
  [APPLICATION_STATUS.DOCUMENTS_REQUIRED]: 'Documents Required',
  [APPLICATION_STATUS.APPROVED]: 'Approved',
  [APPLICATION_STATUS.REJECTED]: 'Rejected',
  [APPLICATION_STATUS.READY_FOR_PICKUP]: 'Ready for Pickup',
  [APPLICATION_STATUS.COLLECTED]: 'Collected',
  [APPLICATION_STATUS.FAST_TRACK]: 'Fast Track',
};

// Status Colors (for badges)
export const STATUS_COLORS = {
  [APPLICATION_STATUS.SUBMITTED]: 'info',
  [APPLICATION_STATUS.UNDER_REVIEW]: 'warning',
  [APPLICATION_STATUS.DOCUMENTS_REQUIRED]: 'warning',
  [APPLICATION_STATUS.APPROVED]: 'success',
  [APPLICATION_STATUS.REJECTED]: 'error',
  [APPLICATION_STATUS.READY_FOR_PICKUP]: 'success',
  [APPLICATION_STATUS.COLLECTED]: 'info',
  [APPLICATION_STATUS.FAST_TRACK]: 'warning',
};

// Notification Types
export const NOTIFICATION_TYPES = {
  STATUS_UPDATE: 'status_update',
  READY_FOR_PICKUP: 'ready_for_pickup',
  PICKUP_REMINDER: 'pickup_reminder',
  DOCUMENTS_REQUIRED: 'documents_required',
};

// Appointment Status
export const APPOINTMENT_STATUS = {
  SCHEDULED: 'scheduled',
  CONFIRMED: 'confirmed',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
  NO_SHOW: 'no_show',
};

// Passport Types
export const PASSPORT_TYPES = {
  STANDARD: 'standard',
  FAST_TRACK: 'fast_track',
  EMERGENCY: 'emergency',
};

// Processing Times (in days)
export const PROCESSING_TIMES = {
  [PASSPORT_TYPES.STANDARD]: 30,
  [PASSPORT_TYPES.FAST_TRACK]: 7,
  [PASSPORT_TYPES.EMERGENCY]: 2,
};

// Pickup Locations
export const PICKUP_LOCATIONS = [
  { id: 1, name: 'Maseru Office', address: 'Constitution Road, Maseru' },
  { id: 2, name: 'Teyateyaneng Office', address: 'Main Street, Teyateyaneng' },
  { id: 3, name: 'Mafeteng Office', address: 'Central Mafeteng' },
  { id: 4, name: 'Leribe Office', address: 'Hlotse Town, Leribe' },
];

// Pagination
export const DEFAULT_PAGE_SIZE = 10;
export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

// Local Storage Keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'passport_auth_token',
  USER_DATA: 'passport_user_data',
  THEME: 'passport_theme',
};

// Date Formats
export const DATE_FORMATS = {
  DISPLAY: 'MMM dd, yyyy',
  DISPLAY_LONG: 'MMMM dd, yyyy',
  DISPLAY_WITH_TIME: 'MMM dd, yyyy HH:mm',
  ISO: 'yyyy-MM-dd',
  TIME: 'HH:mm',
};

// Validation Rules
export const VALIDATION = {
  MIN_PASSWORD_LENGTH: 8,
  MAX_PASSWORD_LENGTH: 128,
  PHONE_REGEX: /^(\+266|266)?[0-9]{8}$/,
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  ID_NUMBER_REGEX: /^[0-9]{13}$/,
};

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'Session expired. Please login again.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  SERVER_ERROR: 'Server error. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
};