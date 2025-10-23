import axios from "axios";
import { API_URL, ERROR_MESSAGES } from "../utils/constants";
import { clearAuthData, getAuthToken } from "../utils/storage";

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Send cookies with requests
});

// Request interceptor - Add auth token to every request
apiClient.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - Handle errors globally
apiClient.interceptors.response.use(
  (response) => {
    // Return just the data from successful responses
    return response.data;
  },
  (error) => {
    // Handle different error types
    if (!error.response) {
      // Network error (no response from server)
      return Promise.reject({
        message: ERROR_MESSAGES.NETWORK_ERROR,
        status: 0,
      });
    }

    const { status, data } = error.response;

    // Handle specific status codes
    switch (status) {
      case 401:
        // Unauthorized - clear auth data and redirect to login
        clearAuthData();
        window.location.href = "/login";
        return Promise.reject({
          message: ERROR_MESSAGES.UNAUTHORIZED,
          status,
          data,
        });

      case 403:
        // Forbidden
        return Promise.reject({
          message: ERROR_MESSAGES.FORBIDDEN,
          status,
          data,
        });

      case 404:
        // Not found
        return Promise.reject({
          message: ERROR_MESSAGES.NOT_FOUND,
          status,
          data,
        });

      case 422: {
        // Validation error - extract user-friendly message
        let validationMessage = ERROR_MESSAGES.VALIDATION_ERROR;

        if (data.detail && Array.isArray(data.detail)) {
          // Extract the first error message
          const firstError = data.detail[0];
          if (firstError.msg) {
            validationMessage = firstError.msg;
          }
        } else if (typeof data.detail === "string") {
          validationMessage = data.detail;
        }

        return Promise.reject({
          message: validationMessage,
          status,
          data,
          errors: data.detail,
        });
      }

      case 500:
      case 502:
      case 503:
        // Server errors
        return Promise.reject({
          message: ERROR_MESSAGES.SERVER_ERROR,
          status,
          data,
        });

      default:
        // Other errors
        return Promise.reject({
          message: data.detail || "An error occurred",
          status,
          data,
        });
    }
  }
);

export default apiClient;
