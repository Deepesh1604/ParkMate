// API Service for ParkMate - handles all API calls with JWT authentication
import { apiRequest, tokenManager } from './auth.js';

const API_ENDPOINTS = {
  // Authentication
  LOGIN: '/login',
  REGISTER: '/register',
  LOGOUT: '/logout',
  REFRESH_TOKEN: '/refresh-token',
  VERIFY_TOKEN: '/verify-token',

  // Admin - Parking Lots
  ADMIN_PARKING_LOTS: '/admin/parking-lots',
  ADMIN_PARKING_LOT: (id) => `/admin/parking-lots/${id}`,

  // Admin - Parking Spots
  ADMIN_PARKING_SPOTS: '/admin/parking-spots',
  ADMIN_FREE_SPOT: (id) => `/admin/parking-spots/${id}/free`,

  // Admin - Users
  ADMIN_USERS: '/admin/users',
  ADMIN_USER: (id) => `/admin/users/${id}`,

  // Admin - Analytics
  ADMIN_ANALYTICS: '/admin/analytics',
  ADMIN_DASHBOARD_DATA: '/admin/analytics/dashboard-data',

  // User - Parking
  PARKING_LOTS: '/parking-lots',
  PARKING_LOT_SPOTS: (id) => `/parking-lots/${id}/spots`,
  RESERVE_SPOT: '/reserve-spot',
  USER_RESERVATIONS: '/user/reservations',
  USER_HISTORY: '/user/history',

  // User - Profile
  USER_PROFILE: '/user/profile',
  UPDATE_PROFILE: '/user/profile',
  EXPORT_CSV: '/export-csv'
};

/**
 * Authentication API calls
 */
export const authAPI = {
  async login(username, password) {
    return await apiRequest(API_ENDPOINTS.LOGIN, {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
  },

  async register(userData) {
    return await apiRequest(API_ENDPOINTS.REGISTER, {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  },

  async logout() {
    return await apiRequest(API_ENDPOINTS.LOGOUT, {
      method: 'POST'
    });
  },

  async refreshToken(refreshToken) {
    return await apiRequest(API_ENDPOINTS.REFRESH_TOKEN, {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken })
    });
  },

  async verifyToken(accessToken) {
    return await apiRequest(API_ENDPOINTS.VERIFY_TOKEN, {
      method: 'POST',
      body: JSON.stringify({ access_token: accessToken })
    });
  }
};

/**
 * Admin API calls
 */
export const adminAPI = {
  // Parking Lots Management
  async getParkingLots() {
    return await apiRequest(API_ENDPOINTS.ADMIN_PARKING_LOTS);
  },

  async createParkingLot(lotData) {
    return await apiRequest(API_ENDPOINTS.ADMIN_PARKING_LOTS, {
      method: 'POST',
      body: JSON.stringify(lotData)
    });
  },

  async updateParkingLot(lotId, lotData) {
    return await apiRequest(API_ENDPOINTS.ADMIN_PARKING_LOT(lotId), {
      method: 'PUT',
      body: JSON.stringify(lotData)
    });
  },

  async deleteParkingLot(lotId) {
    return await apiRequest(API_ENDPOINTS.ADMIN_PARKING_LOT(lotId), {
      method: 'DELETE'
    });
  },

  // Parking Spots Management
  async getParkingSpots(lotId = null) {
    const url = lotId ? 
      `${API_ENDPOINTS.ADMIN_PARKING_SPOTS}?lot_id=${lotId}` : 
      API_ENDPOINTS.ADMIN_PARKING_SPOTS;
    return await apiRequest(url);
  },

  async freeParkingSpot(spotId) {
    return await apiRequest(API_ENDPOINTS.ADMIN_FREE_SPOT(spotId), {
      method: 'PATCH'
    });
  },

  // Users Management
  async getUsers() {
    return await apiRequest(API_ENDPOINTS.ADMIN_USERS);
  },

  async deleteUser(userId) {
    return await apiRequest(API_ENDPOINTS.ADMIN_USER(userId), {
      method: 'DELETE'
    });
  },

  // Analytics
  async getAnalytics() {
    return await apiRequest(API_ENDPOINTS.ADMIN_ANALYTICS);
  },

  async getDashboardData() {
    return await apiRequest(API_ENDPOINTS.ADMIN_DASHBOARD_DATA);
  }
};

/**
 * User API calls
 */
export const userAPI = {
  // Parking Operations
  async getParkingLots() {
    return await apiRequest(API_ENDPOINTS.PARKING_LOTS);
  },

  async getParkingLotSpots(lotId) {
    return await apiRequest(API_ENDPOINTS.PARKING_LOT_SPOTS(lotId));
  },

  async reserveSpot(reservationData) {
    return await apiRequest(API_ENDPOINTS.RESERVE_SPOT, {
      method: 'POST',
      body: JSON.stringify(reservationData)
    });
  },

  async getUserReservations() {
    return await apiRequest(API_ENDPOINTS.USER_RESERVATIONS);
  },

  async getUserHistory() {
    return await apiRequest(API_ENDPOINTS.USER_HISTORY);
  },

  // Profile Management
  async getUserProfile() {
    return await apiRequest(API_ENDPOINTS.USER_PROFILE);
  },

  async updateProfile(profileData) {
    return await apiRequest(API_ENDPOINTS.UPDATE_PROFILE, {
      method: 'PUT',
      body: JSON.stringify(profileData)
    });
  },

  async exportUserData() {
    return await apiRequest(API_ENDPOINTS.EXPORT_CSV, {
      method: 'POST'
    });
  }
};

/**
 * Generic API helper functions
 */
export const apiHelpers = {
  // Check if user has required permissions
  canAccessAdminRoutes() {
    return tokenManager.isAuthenticated() && tokenManager.isAdmin();
  },

  canAccessUserRoutes() {
    return tokenManager.isAuthenticated() && !tokenManager.isAdmin();
  },

  // Get current user data
  getCurrentUser() {
    return tokenManager.getUser();
  },

  // Check authentication status
  isLoggedIn() {
    return tokenManager.isAuthenticated();
  },

  // Handle API errors consistently
  handleAPIError(error) {
    if (error.message.includes('401')) {
      // Unauthorized - redirect to login
      tokenManager.clearTokens();
      window.location.href = '/login';
    } else if (error.message.includes('403')) {
      // Forbidden - show access denied message
      return 'Access denied. You do not have permission to perform this action.';
    } else if (error.message.includes('404')) {
      return 'Resource not found.';
    } else if (error.message.includes('500')) {
      return 'Server error. Please try again later.';
    }
    return error.message || 'An unexpected error occurred.';
  }
};

export default {
  authAPI,
  adminAPI,
  userAPI,
  apiHelpers
};
