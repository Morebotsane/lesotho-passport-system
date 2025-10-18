import { format, formatDistanceToNow, parseISO, isValid } from 'date-fns';
import { DATE_FORMATS } from './constants';

/**
 * Format date to readable string
 * @param {string|Date} date - Date to format
 * @param {string} formatStr - Format string (default: 'MMM dd, yyyy')
 * @returns {string} Formatted date
 */
export const formatDate = (date, formatStr = DATE_FORMATS.DISPLAY) => {
  if (!date) return 'N/A';
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) return 'Invalid Date';
    return format(dateObj, formatStr);
  } catch (error) {
    console.error('Date formatting error:', error);
    return 'Invalid Date';
  }
};

/**
 * Format date to relative time (e.g., "2 hours ago")
 * @param {string|Date} date - Date to format
 * @returns {string} Relative time string
 */
export const formatRelativeTime = (date) => {
  if (!date) return 'N/A';
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) return 'Invalid Date';
    return formatDistanceToNow(dateObj, { addSuffix: true });
  } catch (error) {
    console.error('Relative time formatting error:', error);
    return 'Invalid Date';
  }
};

/**
 * Format phone number for display
 * @param {string} phone - Phone number
 * @returns {string} Formatted phone number
 */
export const formatPhoneNumber = (phone) => {
  if (!phone) return 'N/A';
  
  // Remove all non-digit characters
  const cleaned = phone.replace(/\D/g, '');
  
  // Lesotho format: +266 5XXX XXXX
  if (cleaned.startsWith('266')) {
    const number = cleaned.substring(3);
    return `+266 ${number.substring(0, 4)} ${number.substring(4)}`;
  }
  
  // If no country code, assume Lesotho
  if (cleaned.length === 8) {
    return `+266 ${cleaned.substring(0, 4)} ${cleaned.substring(4)}`;
  }
  
  return phone;
};

/**
 * Format currency (Lesotho Loti)
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency
 */
export const formatCurrency = (amount) => {
  if (amount === null || amount === undefined) return 'M 0.00';
  
  return `M ${Number(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
};

/**
 * Format application number for display
 * @param {string} appNumber - Application number
 * @returns {string} Formatted application number
 */
export const formatApplicationNumber = (appNumber) => {
  if (!appNumber) return 'N/A';
  
  // Format: PASS-2024-00001 → PASS-2024-00001 (already formatted)
  // or 202400001 → PASS-2024-00001
  if (appNumber.includes('-')) return appNumber;
  
  if (appNumber.length >= 9) {
    const year = appNumber.substring(0, 4);
    const number = appNumber.substring(4);
    return `PASS-${year}-${number}`;
  }
  
  return appNumber;
};

/**
 * Format ID number for display
 * @param {string} idNumber - ID number
 * @returns {string} Formatted ID number
 */
export const formatIdNumber = (idNumber) => {
  if (!idNumber) return 'N/A';
  
  // Format: 1234567890123 → 123 456 789 0123
  const cleaned = idNumber.replace(/\D/g, '');
  if (cleaned.length === 13) {
    return `${cleaned.substring(0, 3)} ${cleaned.substring(3, 6)} ${cleaned.substring(6, 9)} ${cleaned.substring(9)}`;
  }
  
  return idNumber;
};

/**
 * Truncate text with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
export const truncateText = (text, maxLength = 50) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return `${text.substring(0, maxLength)}...`;
};

/**
 * Format file size for display
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
export const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

/**
 * Capitalize first letter of each word
 * @param {string} text - Text to capitalize
 * @returns {string} Capitalized text
 */
export const capitalizeWords = (text) => {
  if (!text) return '';
  return text
    .toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Get initials from name
 * @param {string} name - Full name
 * @returns {string} Initials
 */
export const getInitials = (name) => {
  if (!name) return '?';
  
  return name
    .split(' ')
    .map(word => word.charAt(0).toUpperCase())
    .join('')
    .substring(0, 2);
};

/**
 * Format processing time
 * @param {number} days - Number of days
 * @returns {string} Formatted processing time
 */
export const formatProcessingTime = (days) => {
  if (!days) return 'N/A';
  
  if (days === 1) return '1 day';
  if (days < 7) return `${days} days`;
  if (days === 7) return '1 week';
  if (days < 30) return `${Math.round(days / 7)} weeks`;
  if (days === 30) return '1 month';
  return `${Math.round(days / 30)} months`;
};