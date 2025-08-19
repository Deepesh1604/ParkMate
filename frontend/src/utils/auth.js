// JWT Authentication utilities for ParkMate frontend

const API_BASE_URL = 'http://localhost:5000/api';

/**
 * JWT Token Management
 */
export const tokenManager = {
  // Get access token from localStorage
  getAccessToken() {
    return localStorage.getItem('parkmate_access_token');
  },

  // Get refresh token from localStorage
  getRefreshToken() {
    return localStorage.getItem('parkmate_refresh_token');
  },

  // Set tokens in localStorage
  setTokens(accessToken, refreshToken) {
    localStorage.setItem('parkmate_access_token', accessToken);
    if (refreshToken) {
      localStorage.setItem('parkmate_refresh_token', refreshToken);
    }
  },

  // Remove tokens from localStorage
  clearTokens() {
    localStorage.removeItem('parkmate_access_token');
    localStorage.removeItem('parkmate_refresh_token');
    localStorage.removeItem('parkmate_user');
  },

  // Check if user is authenticated
  isAuthenticated() {
    const token = this.getAccessToken();
    if (!token) return false;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp > Date.now() / 1000;
    } catch (error) {
      return false;
    }
  },

  // Check if user is admin
  isAdmin() {
    const user = this.getUser();
    return user && user.is_admin === true;
  },

  // Get user data from localStorage
  getUser() {
    const userStr = localStorage.getItem('parkmate_user');
    return userStr ? JSON.parse(userStr) : null;
  },

  // Set user data in localStorage
  setUser(user) {
    localStorage.setItem('parkmate_user', JSON.stringify(user));
  }
};

/**
 * API Request Helper with JWT
 */
export const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = tokenManager.getAccessToken();

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  };

  // Add authorization header if token exists
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  try {
    let response = await fetch(url, config);

    // If token expired, try to refresh
    if (response.status === 401 && token) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        // Retry with new token
        config.headers.Authorization = `Bearer ${tokenManager.getAccessToken()}`;
        response = await fetch(url, config);
      } else {
        // Refresh failed, redirect to login
        logout();
        window.location.href = '/login';
        return null;
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API Request failed:', error);
    throw error;
  }
};

/**
 * Authentication Functions
 */
export const login = async (username, password) => {
  try {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Login failed');
    }

    const data = await response.json();
    
    // Store tokens and user data
    tokenManager.setTokens(data.access_token, data.refresh_token);
    tokenManager.setUser(data.user);

    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const register = async (userData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Registration failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
};

export const logout = () => {
  // Call logout endpoint
  fetch(`${API_BASE_URL}/logout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${tokenManager.getAccessToken()}`
    }
  }).catch(console.error);

  // Clear local storage
  tokenManager.clearTokens();
};

export const refreshAccessToken = async () => {
  const refreshToken = tokenManager.getRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE_URL}/refresh-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    tokenManager.setTokens(data.access_token);
    return true;
  } catch (error) {
    console.error('Token refresh failed:', error);
    return false;
  }
};

export const verifyToken = async () => {
  const token = tokenManager.getAccessToken();
  if (!token) return false;

  try {
    const response = await fetch(`${API_BASE_URL}/verify-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ access_token: token })
    });

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    return data.valid;
  } catch (error) {
    console.error('Token verification failed:', error);
    return false;
  }
};

/**
 * Route Guards
 */
export const requireAuth = (to, from, next) => {
  if (tokenManager.isAuthenticated()) {
    next();
  } else {
    next('/login');
  }
};

export const requireAdmin = (to, from, next) => {
  if (tokenManager.isAuthenticated() && tokenManager.isAdmin()) {
    next();
  } else if (tokenManager.isAuthenticated()) {
    next('/user-dashboard');
  } else {
    next('/login');
  }
};

export const requireUser = (to, from, next) => {
  if (tokenManager.isAuthenticated() && !tokenManager.isAdmin()) {
    next();
  } else if (tokenManager.isAuthenticated()) {
    next('/admin-dashboard');
  } else {
    next('/login');
  }
};

export const redirectIfAuthenticated = (to, from, next) => {
  if (tokenManager.isAuthenticated()) {
    const user = tokenManager.getUser();
    if (user.is_admin) {
      next('/admin-dashboard');
    } else {
      next('/user-dashboard');
    }
  } else {
    next();
  }
};
