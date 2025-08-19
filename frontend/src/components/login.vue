<template>
  <div class="login-page">
    <!-- Animated background matching HomeView -->
    <div class="background-animation">
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
        <div class="shape shape-5"></div>
      </div>
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <div class="login-container">
      <div class="login-card">
        <div class="card-header">
          <div class="logo-section">
            <router-link to="/" class="logo-link">
              <h1 class="brand-title">🚗 ParkMate</h1>
            </router-link>
          </div>
          <h2 class="login-title">Welcome Back</h2>
          <p class="login-subtitle">Sign in to your account to continue</p>
        </div>

        <form @submit.prevent="handleLogin" class="login-form">
          <div class="form-group">
            <label for="username" class="form-label">
              <span class="label-text">Username</span>
            </label>
            <div class="input-wrapper">
              <input 
                type="text" 
                id="username" 
                v-model="username" 
                required 
                class="form-input"
                placeholder="Enter your username"
              />
              <div class="input-glow"></div>
            </div>
          </div>

          <div class="form-group">
            <label for="password" class="form-label">
              <span class="label-text">Password</span>
            </label>
            <div class="input-wrapper">
              <input 
                type="password" 
                id="password" 
                v-model="password" 
                required 
                class="form-input"
                placeholder="Enter your password"
              />
              <div class="input-glow"></div>
            </div>
          </div>

          <div class="form-actions">
            <button type="submit" class="login-btn" :disabled="isLoading">
              <span class="btn-text">{{ isLoading ? 'Signing In...' : 'Sign In' }}</span>
              <div class="btn-glow"></div>
            </button>
          </div>
        </form>

        <div v-if="errorMessage" class="error-message">
          <span class="error-icon">!</span>
          {{ errorMessage }}
        </div>

        <div class="card-footer">
          <div class="divider">
            <span class="divider-text">Don't have an account?</span>
          </div>
          <router-link to="/register" class="register-link">
            <span class="link-text">Create Account</span>
            <div class="link-glow"></div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

const username = ref('');
const password = ref('');
const errorMessage = ref('');
const isLoading = ref(false);
const router = useRouter();

const handleLogin = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  
  try {
    const response = await axios.post('/api/login', {
      username: username.value,
      password: password.value,
    });
    if (response.status === 200) {
      const user = response.data.user;
      if (user.is_admin) {
        router.push('/admin');
      } else {
        router.push('/dashboard');
      }
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Login failed';
  } finally {
    isLoading.value = false;
  }
};

// Initialize animations on mount
onMounted(() => {
  // Add floating animation to shapes with random delays
  const shapes = document.querySelectorAll('.shape');
  shapes.forEach((shape, index) => {
    shape.style.animationDelay = `${index * 0.8}s`;
  });

  // Add floating animation to gradient orbs
  const orbs = document.querySelectorAll('.gradient-orb');
  orbs.forEach((orb, index) => {
    orb.style.animationDelay = `${index * 3}s`;
  });
});
</script>

<style scoped>
/* CSS Variables for consistent theming */
:root {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --accent-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  --glass-bg: rgba(255, 255, 255, 0.1);
  --glass-bg-strong: rgba(255, 255, 255, 0.15);
  --glass-border: rgba(255, 255, 255, 0.2);
  --shadow-soft: 0 8px 32px rgba(31, 38, 135, 0.15);
  --shadow-hover: 0 15px 35px rgba(31, 38, 135, 0.25);
  --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Global Page Styles */
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

/* Background Animation (same as HomeView) */
.background-animation {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.floating-shapes {
  position: relative;
  width: 100%;
  height: 100%;
}

.shape {
  position: absolute;
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: 50%;
  animation: float 8s ease-in-out infinite;
}

.shape-1 {
  width: 60px;
  height: 60px;
  top: 15%;
  left: 10%;
  animation-duration: 6s;
}

.shape-2 {
  width: 80px;
  height: 80px;
  top: 25%;
  right: 15%;
  animation-duration: 8s;
}

.shape-3 {
  width: 50px;
  height: 50px;
  bottom: 20%;
  left: 20%;
  animation-duration: 7s;
}

.shape-4 {
  width: 70px;
  height: 70px;
  bottom: 30%;
  right: 25%;
  animation-duration: 9s;
}

.shape-5 {
  width: 90px;
  height: 90px;
  top: 60%;
  left: 70%;
  animation-duration: 10s;
  opacity: 0.7;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.4;
  animation: orbFloat 15s ease-in-out infinite;
}

.orb-1 {
  width: 300px;
  height: 300px;
  top: 10%;
  left: 10%;
  background: radial-gradient(circle, rgba(103, 126, 234, 0.4), rgba(118, 75, 162, 0.2));
}

.orb-2 {
  width: 250px;
  height: 250px;
  bottom: 10%;
  right: 10%;
  background: radial-gradient(circle, rgba(240, 147, 251, 0.4), rgba(245, 87, 108, 0.2));
}

.orb-3 {
  width: 200px;
  height: 200px;
  top: 50%;
  left: 50%;
  background: radial-gradient(circle, rgba(79, 172, 254, 0.3), rgba(0, 242, 254, 0.1));
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-15px) rotate(180deg);
  }
}

@keyframes orbFloat {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(20px, -20px) scale(1.1);
  }
  66% {
    transform: translate(-15px, 15px) scale(0.9);
  }
}

/* Login Container */
.login-container {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 450px;
}

/* Login Card */
.login-card {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(30px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 24px;
  padding: 3rem 2.5rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  transition: var(--transition-smooth);
}

.login-card:hover {
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
  border-color: rgba(255, 255, 255, 0.4);
}

/* Card Header */
.card-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.logo-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.logo-icon {
  width: 60px;
  height: 60px;
  font-size: 2rem;
  font-weight: bold;
  background: var(--accent-gradient);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(79, 172, 254, 0.3);
}

.logo-section {
  text-align: center;
  margin-bottom: 1rem;
}

.logo-link {
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 8px;
  padding: 0.5rem;
  display: inline-block;
}

.logo-link:hover {
  transform: scale(1.05);
  background: rgba(255, 255, 255, 0.05);
}

.brand-title {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #fff 0%, #e0e0e0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.login-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: white;
  margin: 0 0 0.5rem 0;
}

.login-subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1rem;
  margin: 0;
}

/* Form Styles */
.login-form {
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  margin-bottom: 0.75rem;
  color: #ffffff;
  font-weight: 600;
  font-size: 0.95rem;
  text-align: left;
}

.label-text {
  font-weight: 600;
}

.label-icon {
  font-size: 1.1rem;
  opacity: 0.8;
}

.input-wrapper {
  position: relative;
}

.form-input {
  width: 100%;
  padding: 1rem 1.25rem;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  transition: var(--transition-smooth);
  box-sizing: border-box;
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.65);
  font-weight: 400;
}

.form-input:focus {
  outline: none;
  border-color: rgba(79, 172, 254, 0.8);
  background: rgba(255, 255, 255, 0.25);
  box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.15);
}

.form-input:hover {
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.22);
}

.input-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), transparent);
  border-radius: 12px;
  pointer-events: none;
  opacity: 0;
  transition: var(--transition-smooth);
}

.form-input:focus + .input-glow {
  opacity: 1;
}

/* Form Actions */
.form-actions {
  margin: 2rem 0;
}

.login-btn {
  position: relative;
  width: 100%;
  padding: 1.25rem;
  background: var(--accent-gradient);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition-smooth);
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(79, 172, 254, 0.4);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-text {
  position: relative;
  z-index: 2;
}

.btn-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent);
  transition: var(--transition-smooth);
  z-index: 1;
}

.login-btn:hover:not(:disabled) .btn-glow {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.05));
}

/* Error Message */
.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: rgba(255, 71, 87, 0.1);
  border: 1px solid rgba(255, 71, 87, 0.3);
  border-radius: 12px;
  color: #ff6b7d;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
  backdrop-filter: blur(10px);
}

.error-icon {
  font-size: 1.1rem;
}

/* Card Footer */
.card-footer {
  text-align: center;
}

.divider {
  position: relative;
  margin: 1.5rem 0;
}

.divider-text {
  background: var(--glass-bg-strong);
  padding: 0 1rem;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
}

.register-link {
  position: relative;
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  font-weight: 500;
  transition: var(--transition-smooth);
  overflow: hidden;
}

.register-link:hover {
  color: white;
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(255, 255, 255, 0.1);
}

.link-text {
  position: relative;
  z-index: 2;
}

.link-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), transparent);
  transition: var(--transition-smooth);
  opacity: 0;
  z-index: 1;
}

.register-link:hover .link-glow {
  opacity: 1;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
}

/* Responsive Design */
@media (max-width: 480px) {
  .login-page {
    padding: 1rem 0.5rem;
  }
  
  .login-card {
    padding: 2rem 1.5rem;
  }
  
  .logo-icon {
    font-size: 2rem;
  }
  
  .brand-title {
    font-size: 1.5rem;
  }
  
  .login-title {
    font-size: 1.5rem;
  }
}
</style>

