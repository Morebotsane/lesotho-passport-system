import { VALIDATION } from './constants';

/**
 * Validate email address
 * @param {string} email - Email to validate
 * @returns {boolean} True if valid
 */
export const isValidEmail = (email) => {
  if (!email) return false;
  return VALIDATION.EMAIL_REGEX.test(email.trim());
};

/**
 * Validate Lesotho phone number
 * @param {string} phone - Phone number to validate
 * @returns {boolean} True if valid
 */
export const isValidPhone = (phone) => {
  if (!phone) return false;
  const cleaned = phone.replace(/\s/g, '');
  return VALIDATION.PHONE_REGEX.test(cleaned);
};

/**
 * Validate password strength
 * @param {string} password - Password to validate
 * @returns {object} { isValid, errors }
 */
export const validatePassword = (password) => {
  const errors = [];
  
  if (!password) {
    return { isValid: false, errors: ['Password is required'] };
  }
  
  if (password.length < VALIDATION.MIN_PASSWORD_LENGTH) {
    errors.push(`Password must be at least ${VALIDATION.MIN_PASSWORD_LENGTH} characters`);
  }
  
  if (password.length > VALIDATION.MAX_PASSWORD_LENGTH) {
    errors.push(`Password must be less than ${VALIDATION.MAX_PASSWORD_LENGTH} characters`);
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (!/[0-9]/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Validate ID number (13 digits)
 * @param {string} idNumber - ID number to validate
 * @returns {boolean} True if valid
 */
export const isValidIdNumber = (idNumber) => {
  if (!idNumber) return false;
  const cleaned = idNumber.replace(/\s/g, '');
  return VALIDATION.ID_NUMBER_REGEX.test(cleaned);
};

/**
 * Validate required field
 * @param {any} value - Value to validate
 * @returns {boolean} True if not empty
 */
export const isRequired = (value) => {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return value.trim().length > 0;
  if (Array.isArray(value)) return value.length > 0;
  return true;
};

/**
 * Validate minimum length
 * @param {string} value - Value to validate
 * @param {number} minLength - Minimum length
 * @returns {boolean} True if meets minimum
 */
export const minLength = (value, minLength) => {
  if (!value) return false;
  return value.length >= minLength;
};

/**
 * Validate maximum length
 * @param {string} value - Value to validate
 * @param {number} maxLength - Maximum length
 * @returns {boolean} True if within maximum
 */
export const maxLength = (value, maxLength) => {
  if (!value) return true; // Empty is valid for max length
  return value.length <= maxLength;
};

/**
 * Validate date is in the future
 * @param {string|Date} date - Date to validate
 * @returns {boolean} True if future date
 */
export const isFutureDate = (date) => {
  if (!date) return false;
  const dateObj = new Date(date);
  return dateObj > new Date();
};

/**
 * Validate date is in the past
 * @param {string|Date} date - Date to validate
 * @returns {boolean} True if past date
 */
export const isPastDate = (date) => {
  if (!date) return false;
  const dateObj = new Date(date);
  return dateObj < new Date();
};

/**
 * Validate date is not too old (for birth dates, etc.)
 * @param {string|Date} date - Date to validate
 * @param {number} maxYears - Maximum years in the past
 * @returns {boolean} True if within range
 */
export const isDateNotTooOld = (date, maxYears = 150) => {
  if (!date) return false;
  const dateObj = new Date(date);
  const yearsAgo = new Date();
  yearsAgo.setFullYear(yearsAgo.getFullYear() - maxYears);
  return dateObj >= yearsAgo;
};

/**
 * Validate age is above minimum (for passport applications)
 * @param {string|Date} birthDate - Birth date
 * @param {number} minAge - Minimum age required
 * @returns {boolean} True if age is sufficient
 */
export const isAgeAboveMinimum = (birthDate, minAge = 0) => {
  if (!birthDate) return false;
  const today = new Date();
  const birth = new Date(birthDate);
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  
  return age >= minAge;
};

/**
 * Validate file type
 * @param {File} file - File to validate
 * @param {string[]} allowedTypes - Allowed MIME types
 * @returns {boolean} True if allowed type
 */
export const isValidFileType = (file, allowedTypes = ['image/jpeg', 'image/png', 'application/pdf']) => {
  if (!file) return false;
  return allowedTypes.includes(file.type);
};

/**
 * Validate file size
 * @param {File} file - File to validate
 * @param {number} maxSizeMB - Maximum size in MB
 * @returns {boolean} True if within size limit
 */
export const isValidFileSize = (file, maxSizeMB = 5) => {
  if (!file) return false;
  const maxBytes = maxSizeMB * 1024 * 1024;
  return file.size <= maxBytes;
};

/**
 * Validate passport number format (example: P123456)
 * @param {string} passportNumber - Passport number to validate
 * @returns {boolean} True if valid format
 */
export const isValidPassportNumber = (passportNumber) => {
  if (!passportNumber) return false;
  // Lesotho passport format: P followed by 6 digits
  return /^P[0-9]{6}$/.test(passportNumber.trim().toUpperCase());
};

/**
 * Validate application number format
 * @param {string} appNumber - Application number
 * @returns {boolean} True if valid format
 */
export const isValidApplicationNumber = (appNumber) => {
  if (!appNumber) return false;
  // Format: PASS-YYYY-NNNNN or just numbers
  return /^(PASS-\d{4}-\d{5}|\d{9,})$/.test(appNumber.trim());
};

/**
 * Comprehensive form validation
 * @param {object} values - Form values to validate
 * @param {object} rules - Validation rules
 * @returns {object} { isValid, errors }
 */
export const validateForm = (values, rules) => {
  const errors = {};
  
  Object.keys(rules).forEach(field => {
    const fieldRules = rules[field];
    const value = values[field];
    
    // Required validation
    if (fieldRules.required && !isRequired(value)) {
      errors[field] = fieldRules.requiredMessage || `${field} is required`;
      return;
    }
    
    // Skip other validations if field is empty and not required
    if (!isRequired(value)) return;
    
    // Email validation
    if (fieldRules.email && !isValidEmail(value)) {
      errors[field] = 'Invalid email address';
      return;
    }
    
    // Phone validation
    if (fieldRules.phone && !isValidPhone(value)) {
      errors[field] = 'Invalid phone number (format: +266 XXXX XXXX)';
      return;
    }
    
    // Min length validation
    if (fieldRules.minLength && !minLength(value, fieldRules.minLength)) {
      errors[field] = `Must be at least ${fieldRules.minLength} characters`;
      return;
    }
    
    // Max length validation
    if (fieldRules.maxLength && !maxLength(value, fieldRules.maxLength)) {
      errors[field] = `Must be less than ${fieldRules.maxLength} characters`;
      return;
    }
    
    // Custom validation function
    if (fieldRules.custom) {
      const customError = fieldRules.custom(value, values);
      if (customError) {
        errors[field] = customError;
      }
    }
  });
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
};

/**
 * Get error message for field
 * @param {object} errors - Errors object
 * @param {string} field - Field name
 * @returns {string|null} Error message or null
 */
export const getFieldError = (errors, field) => {
  return errors[field] || null;
};

/**
 * Check if field has error
 * @param {object} errors - Errors object
 * @param {string} field - Field name
 * @returns {boolean} True if field has error
 */
export const hasFieldError = (errors, field) => {
  return !!errors[field];
};