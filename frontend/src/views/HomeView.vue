<template>
  <div class="home">
    <div class="hero-section">
      <h1>Welcome to ParkMate</h1>
      <p>Your smart parking solution</p>
      <div class="action-buttons">
        <router-link to="/login" class="btn login-btn">Login</router-link>
        <router-link to="/register" class="btn register-btn">Register</router-link>
      </div>
    </div>
    
    <div class="features">
      <div class="feature">
        <h3>🚗 Easy Parking</h3>
        <p>Find and reserve parking spots quickly</p>
      </div>
      <div class="feature">
        <h3>📱 Mobile Friendly</h3>
        <p>Access from anywhere, anytime</p>
      </div>
      <div class="feature">
        <h3>💰 Cost Effective</h3>
        <p>Transparent pricing with no hidden fees</p>
      </div>
    </div>
  </div>
</template>

<script setup>
// This is a simple home page component
</script>

<style scoped>
.home {
  padding: 2rem;
  text-align: center;
}

.hero-section {
  margin-bottom: 3rem;
}

.hero-section h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #2c3e50;
}

.hero-section p {
  font-size: 1.2rem;
  color: #7f8c8d;
  margin-bottom: 2rem;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-block;
  padding: 1rem 2rem;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-size: 1.1rem;
  transition: background-color 0.3s;
  min-width: 120px;
}

.login-btn {
  background-color: #42b883;
}

.login-btn:hover {
  background-color: #38a169;
}

.register-btn {
  background-color: #3498db;
}

.register-btn:hover {
  background-color: #2980b9;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 3rem;
}

.feature {
  background-color: #f8f9fa;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.feature h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.feature p {
  color: #7f8c8d;
  line-height: 1.6;
}
</style>
