import { STORAGE_KEYS } from './constants';

/**
 * Check if localStorage is available
 * @returns {boolean} True if localStorage is available
 */
const isLocalStorageAvailable = () => {
  try {
    const testKey = '__localStorage_test__';
    localStorage.setItem(testKey, 'test');
    localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
};

/**
 * Safely get item from localStorage
 * @param {string} key - Storage key
 * @param {any} defaultValue - Default value if key doesn't exist
 * @returns {any} Stored value or default value
 */
export const getItem = (key, defaultValue = null) => {
  if (!isLocalStorageAvailable()) {
    console.warn('localStorage is not available');
    return defaultValue;
  }

  try {
    const item = localStorage.getItem(key);
    if (item === null) return defaultValue;
    
    // Try to parse JSON, if it fails return the raw string
    try {
      return JSON.parse(item);
    } catch {
      return item;
    }
  } catch (error) {
    console.error(`Error getting item from localStorage (${key}):`, error);
    return defaultValue;
  }
};

/**
 * Safely set item in localStorage
 * @param {string} key - Storage key
 * @param {any} value - Value to store
 * @returns {boolean} True if successful
 */
export const setItem = (key, value) => {
  if (!isLocalStorageAvailable()) {
    console.warn('localStorage is not available');
    return false;
  }

  try {
    const serializedValue = typeof value === 'string' ? value : JSON.stringify(value);
    localStorage.setItem(key, serializedValue);
    return true;
  } catch (error) {
    console.error(`Error setting item in localStorage (${key}):`, error);
    return false;
  }
};

/**
 * Safely remove item from localStorage
 * @param {string} key - Storage key
 * @returns {boolean} True if successful
 */
export const removeItem = (key) => {
  if (!isLocalStorageAvailable()) {
    console.warn('localStorage is not available');
    return false;
  }

  try {
    localStorage.removeItem(key);
    return true;
  } catch (error) {
    console.error(`Error removing item from localStorage (${key}):`, error);
    return false;
  }
};

/**
 * Clear all items from localStorage
 * @returns {boolean} True if successful
 */
export const clear = () => {
  if (!isLocalStorageAvailable()) {
    console.warn('localStorage is not available');
    return false;
  }

  try {
    localStorage.clear();
    return true;
  } catch (error) {
    console.error('Error clearing localStorage:', error);
    return false;
  }
};

/**
 * Get auth token
 * @returns {string|null} Auth token or null
 */
export const getAuthToken = () => {
  return getItem(STORAGE_KEYS.AUTH_TOKEN);
};

/**
 * Set auth token
 * @param {string} token - Auth token
 * @returns {boolean} True if successful
 */
export const setAuthToken = (token) => {
  return setItem(STORAGE_KEYS.AUTH_TOKEN, token);
};

/**
 * Remove auth token
 * @returns {boolean} True if successful
 */
export const removeAuthToken = () => {
  return removeItem(STORAGE_KEYS.AUTH_TOKEN);
};

/**
 * Get user data
 * @returns {object|null} User data or null
 */
export const getUserData = () => {
  return getItem(STORAGE_KEYS.USER_DATA);
};

/**
 * Set user data
 * @param {object} userData - User data
 * @returns {boolean} True if successful
 */
export const setUserData = (userData) => {
  return setItem(STORAGE_KEYS.USER_DATA, userData);
};

/**
 * Remove user data
 * @returns {boolean} True if successful
 */
export const removeUserData = () => {
  return removeItem(STORAGE_KEYS.USER_DATA);
};

/**
 * Clear all auth-related data
 * @returns {boolean} True if successful
 */
export const clearAuthData = () => {
  const tokenRemoved = removeAuthToken();
  const userDataRemoved = removeUserData();
  return tokenRemoved && userDataRemoved;
};

/**
 * Check if user is authenticated (has token)
 * @returns {boolean} True if authenticated
 */
export const isAuthenticated = () => {
  const token = getAuthToken();
  return !!token;
};

/**
 * Get theme preference
 * @returns {string} Theme ('light' or 'dark')
 */
export const getTheme = () => {
  return getItem(STORAGE_KEYS.THEME, 'light');
};

/**
 * Set theme preference
 * @param {string} theme - Theme ('light' or 'dark')
 * @returns {boolean} True if successful
 */
export const setTheme = (theme) => {
  return setItem(STORAGE_KEYS.THEME, theme);
};