<template>
  <div class="register-page">
    <!-- Animated background matching theme -->
    <div class="background-animation">
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
        <div class="shape shape-5"></div>
        <div class="shape shape-6"></div>
      </div>
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <div class="register-container">
      <div class="register-card">
        <div class="card-header">
          <div class="logo-section">
            <router-link to="/" class="logo-link">
              <h1 class="brand-title">🚗 ParkMate</h1>
            </router-link>
          </div>
          <h2 class="register-title">Create Account</h2>
          <p class="register-subtitle">Join ParkMate and start your smart parking journey</p>
        </div>

        <form @submit.prevent="handleRegister" class="register-form">
          <div class="form-group">
            <label for="username" class="form-label">Username</label>
            <div class="input-wrapper">
              <input 
                type="text" 
                id="username" 
                v-model="username" 
                required 
                class="form-input"
                placeholder="Choose a username"
              />
              <div class="input-glow"></div>
            </div>
          </div>

          <div class="form-group">
            <label for="email" class="form-label">Email</label>
            <div class="input-wrapper">
              <input 
                type="email" 
                id="email" 
                v-model="email" 
                required 
                class="form-input"
                placeholder="Enter your email address"
              />
              <div class="input-glow"></div>
            </div>
          </div>

          <div class="form-group">
            <label for="phone" class="form-label">Phone </label>
            <div class="input-wrapper">
              <input 
                type="tel" 
                id="phone" 
                v-model="phone" 
                class="form-input"
                placeholder="Enter your phone number"
              />
              <div class="input-glow"></div>
            </div>
          </div>

          <div class="form-group">
            <label for="password" class="form-label">Password</label>
            <div class="input-wrapper">
              <input 
                type="password" 
                id="password" 
                v-model="password" 
                required 
                class="form-input"
                placeholder="Create a strong password"
              />
              <div class="input-glow"></div>
            </div>
          </div>

          <div class="form-group">
            <label for="confirmPassword" class="form-label">Confirm Password</label>
            <div class="input-wrapper">
              <input 
                type="password" 
                id="confirmPassword" 
                v-model="confirmPassword" 
                required 
                class="form-input"
                placeholder="Confirm your password"
              />
              <div class="input-glow"></div>
            </div>
          </div>

          <div class="form-actions">
            <button type="submit" class="register-btn" :disabled="isLoading">
              <span class="btn-text">{{ isLoading ? 'Creating Account...' : 'Create Account' }}</span>
              <div class="btn-glow"></div>
            </button>
          </div>
        </form>

        <div v-if="errorMessage" class="error-message">
          <span class="error-icon">!</span>
          {{ errorMessage }}
        </div>

        <div v-if="successMessage" class="success-message">
          <span class="success-icon">✓</span>
          {{ successMessage }}
        </div>

        <div class="card-footer">
          <div class="divider">
            <span class="divider-text">Already have an account?</span>
          </div>
          <router-link to="/login" class="login-link">
            <span class="link-text">Sign In</span>
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
const email = ref('');
const phone = ref('');
const password = ref('');
const confirmPassword = ref('');
const errorMessage = ref('');
const successMessage = ref('');
const isLoading = ref(false);
const router = useRouter();

const handleRegister = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';
  
  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match';
    isLoading.value = false;
    return;
  }
  
  if (password.value.length < 6) {
    errorMessage.value = 'Password must be at least 6 characters long';
    isLoading.value = false;
    return;
  }
  
  try {
    const response = await axios.post('/api/register', {
      username: username.value,
      email: email.value,
      phone: phone.value,
      password: password.value,
    });
    
    if (response.status === 201) {
      successMessage.value = 'Account created successfully! Redirecting to login...';
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Registration failed. Please try again.';
  } finally {
    isLoading.value = false;
  }
};

// Initialize animations on mount
onMounted(() => {
  // Add floating animation to shapes with random delays
  const shapes = document.querySelectorAll('.shape');
  shapes.forEach((shape, index) => {
    shape.style.animationDelay = `${index * 0.7}s`;
  });

  // Add floating animation to gradient orbs
  const orbs = document.querySelectorAll('.gradient-orb');
  orbs.forEach((orb, index) => {
    orb.style.animationDelay = `${index * 2.5}s`;
  });
});
</script>

<style scoped>
/* CSS Variables for consistent theming */
:root {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --accent-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  --success-gradient: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
  --glass-bg: rgba(255, 255, 255, 0.1);
  --glass-bg-strong: rgba(255, 255, 255, 0.15);
  --glass-border: rgba(255, 255, 255, 0.2);
  --shadow-soft: 0 8px 32px rgba(31, 38, 135, 0.15);
  --shadow-hover: 0 15px 35px rgba(31, 38, 135, 0.25);
  --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Global Page Styles */
.register-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

/* Background Animation (same as login/home) */
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
  width: 70px;
  height: 70px;
  top: 10%;
  left: 15%;
  animation-duration: 7s;
}

.shape-2 {
  width: 90px;
  height: 90px;
  top: 20%;
  right: 10%;
  animation-duration: 9s;
}

.shape-3 {
  width: 55px;
  height: 55px;
  bottom: 25%;
  left: 25%;
  animation-duration: 6s;
}

.shape-4 {
  width: 75px;
  height: 75px;
  bottom: 15%;
  right: 20%;
  animation-duration: 8s;
}

.shape-5 {
  width: 85px;
  height: 85px;
  top: 50%;
  left: 5%;
  animation-duration: 10s;
  opacity: 0.7;
}

.shape-6 {
  width: 65px;
  height: 65px;
  top: 70%;
  right: 30%;
  animation-duration: 11s;
  opacity: 0.6;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.4;
  animation: orbFloat 16s ease-in-out infinite;
}

.orb-1 {
  width: 320px;
  height: 320px;
  top: 5%;
  left: 5%;
  background: radial-gradient(circle, rgba(103, 126, 234, 0.4), rgba(118, 75, 162, 0.2));
}

.orb-2 {
  width: 280px;
  height: 280px;
  bottom: 5%;
  right: 5%;
  background: radial-gradient(circle, rgba(240, 147, 251, 0.4), rgba(245, 87, 108, 0.2));
}

.orb-3 {
  width: 240px;
  height: 240px;
  top: 45%;
  left: 60%;
  background: radial-gradient(circle, rgba(79, 172, 254, 0.3), rgba(0, 242, 254, 0.1));
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-18px) rotate(180deg);
  }
}

@keyframes orbFloat {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(25px, -25px) scale(1.1);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.9);
  }
}

/* Register Container */
.register-container {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 450px;
}

/* Register Card */
.register-card {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(30px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 24px;
  padding: 2rem 2rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  transition: var(--transition-smooth);
}

.register-card:hover {
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
  border-color: rgba(255, 255, 255, 0.4);
}

/* Card Header */
.card-header {
  text-align: center;
  margin-bottom: 1.5rem;
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

.register-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: white;
  margin: 0 0 0.5rem 0;
}

.register-subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1rem;
  margin: 0;
}

/* Form Styles */
.register-form {
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1rem;
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
  padding: 0.75rem 1rem;
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
  margin: 1.5rem 0 1rem;
}

.register-btn {
  position: relative;
  width: 100%;
  padding: 1rem;
  background: var(--success-gradient);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition-smooth);
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
}

.register-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 255, 136, 0.4);
}

.register-btn:disabled {
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

.register-btn:hover:not(:disabled) .btn-glow {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.05));
}

/* Error & Success Messages */
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

.success-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.3);
  border-radius: 12px;
  color: #00ff88;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
  backdrop-filter: blur(10px);
}

.error-icon,
.success-icon {
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

.login-link {
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

.login-link:hover {
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

.login-link:hover .link-glow {
  opacity: 1;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
}

/* Responsive Design */
@media (max-width: 480px) {
  .register-page {
    padding: 0.5rem;
  }
  
  .register-card {
    padding: 1.5rem 1.25rem;
  }
  
  .card-header {
    margin-bottom: 1rem;
  }
  
  .form-group {
    margin-bottom: 0.875rem;
  }
  
  .form-input {
    padding: 0.625rem 0.875rem;
    font-size: 0.95rem;
  }
  
  .form-actions {
    margin: 1rem 0 0.5rem;
  }
  
  .logo-icon {
    font-size: 2rem;
  }
  
  .brand-title {
    font-size: 1.5rem;
  }
  
  .register-title {
    font-size: 1.5rem;
  }
}
</style>
