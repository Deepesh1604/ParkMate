<template>
  <div class="user-dashboard">
    <!-- Animated Background -->
    <div class="animated-background">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
      <div class="floating-shape shape-4"></div>
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-container">
        <div class="spinner"></div>
        <p>Loading your dashboard...</p>
      </div>
    </div>
    
    <div v-else>
      <!-- Professional Header -->
      <div class="dashboard-header">
        <div class="header-content">
          <div class="header-left">
            <h1>🚗 My ParkMate Dashboard</h1>
            <p class="header-subtitle">Your personal parking management hub</p>
          </div>
          <div class="header-right">
            <div class="user-info">
              <div class="user-avatar">
                <span>{{ (user.username || 'U').charAt(0).toUpperCase() }}</span>
              </div>
              <div class="user-details">
                <span class="username">{{ user.username || 'User' }}</span>
                <span class="user-email">{{ user.email || 'user@example.com' }}</span>
              </div>
              <button @click="logout" class="logout-btn">
                <span class="btn-icon">🔓</span>
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Enhanced Navigation -->
      <div class="dashboard-nav">
        <div class="nav-container">
          <button 
            v-for="tab in tabs" 
            :key="tab.id" 
            :class="['nav-btn', { active: activeTab === tab.id }]"
            @click="activeTab = tab.id"
          >
            <span class="nav-icon">{{ tab.icon }}</span>
            <span class="nav-text">{{ tab.name }}</span>
          </button>
        </div>
      </div>

      <!-- Content Area -->
      <div class="dashboard-content">
        <!-- Overview Tab -->
        <div v-if="activeTab === 'overview'" class="tab-content">
          <UserOverview @change-tab="activeTab = $event" />
        </div>

        <!-- Parking Lots Tab -->
        <div v-if="activeTab === 'parking-lots'" class="tab-content">
          <ParkingLotsView @refresh="loadUserData" />
        </div>

        <!-- My Reservations Tab -->
        <div v-if="activeTab === 'reservations'" class="tab-content">
          <MyReservations @refresh="loadUserData" />
        </div>

        <!-- Active Parking Tab -->
        <div v-if="activeTab === 'active-parking'" class="tab-content">
          <ActiveParking @refresh="loadUserData" />
        </div>

        <!-- History Tab -->
        <div v-if="activeTab === 'history'" class="tab-content">
          <ParkingHistory />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import UserOverview from '../components/user/UserOverview.vue';
import ParkingLotsView from '../components/user/ParkingLotsView.vue';
import MyReservations from '../components/user/MyReservations.vue';
import ActiveParking from '../components/user/ActiveParking.vue';
import ParkingHistory from '../components/user/ParkingHistory.vue';

const router = useRouter();
const activeTab = ref('overview');
const user = ref({ username: '', email: '', id: null });
const loading = ref(true);

const tabs = [
  { id: 'overview', name: 'Overview', icon: '📊' },
  { id: 'parking-lots', name: 'Find Parking', icon: '🏢' },
  { id: 'reservations', name: 'My Reservations', icon: '📋' },
  { id: 'active-parking', name: 'Active Parking', icon: '🅿️' },
  { id: 'history', name: 'History', icon: '📈' }
];

const loadUserData = async () => {
  try {
    loading.value = true;
    
    // Fetch current user profile
    const userResponse = await axios.get('/api/user/profile');
    user.value = userResponse.data;
    
  } catch (error) {
    console.error('Error loading user data:', error);
    // If user is not authenticated, redirect to login
    if (error.response?.status === 401) {
      router.push('/login');
    }
  } finally {
    loading.value = false;
  }
};

const logout = async () => {
  try {
    await axios.post('/api/logout');
    router.push('/login');
  } catch (error) {
    console.error('Logout error:', error);
    router.push('/login');
  }
};

onMounted(() => {
  loadUserData();
});
</script>

<style scoped>
.user-dashboard {
  min-height: 100vh;
  width: 100%;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  margin: 0;
  padding: 0;
  position: relative;
  overflow-x: hidden;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Animated Background */
.animated-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.floating-shape {
  position: absolute;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  backdrop-filter: blur(10px);
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  width: 100px;
  height: 100px;
  top: 20%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 150px;
  height: 150px;
  top: 60%;
  right: 15%;
  animation-delay: 2s;
}

.shape-3 {
  width: 80px;
  height: 80px;
  bottom: 30%;
  left: 20%;
  animation-delay: 4s;
}

.shape-4 {
  width: 120px;
  height: 120px;
  top: 40%;
  right: 40%;
  animation-delay: 1s;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
  animation: float 8s ease-in-out infinite;
}

.orb-1 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(64, 123, 255, 0.15) 0%, transparent 70%);
  top: 10%;
  left: 70%;
  animation-delay: 0s;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(138, 43, 226, 0.12) 0%, transparent 70%);
  bottom: 20%;
  right: 60%;
  animation-delay: 3s;
}

.orb-3 {
  width: 150px;
  height: 150px;
  background: radial-gradient(circle, rgba(0, 191, 255, 0.08) 0%, transparent 70%);
  top: 50%;
  left: 5%;
  animation-delay: 5s;
}

@keyframes float {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(5deg); }
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  position: relative;
  z-index: 10;
}

.loading-container {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  padding: 3rem;
  border-radius: 20px;
  text-align: center;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-top: 4px solid #64b5f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1.5rem;
}

.loading-container p {
  color: white;
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Professional Header */
.dashboard-header {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(25px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  padding: 1.5rem 2rem;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
}

.header-left h1 {
  margin: 0 0 0.5rem 0;
  font-size: 2.2rem;
  background: linear-gradient(135deg, #ffffff 0%, #64b5f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.header-subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1rem;
  margin: 0;
  font-weight: 400;
}

.header-right .user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #64b5f6 0%, #1976d2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 1.2rem;
  border: 2px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 15px rgba(100, 181, 246, 0.3);
}

.user-details {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.username {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 1rem;
}

.user-email {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.85rem;
}

.logout-btn {
  background: linear-gradient(135deg, #64b5f6 0%, #1976d2 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 4px 15px rgba(100, 181, 246, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.logout-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(100, 181, 246, 0.4);
  background: linear-gradient(135deg, #1976d2 0%, #64b5f6 100%);
}

.btn-icon {
  font-size: 1rem;
}

/* Enhanced Navigation */
.dashboard-nav {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 1rem 2rem;
  position: sticky;
  top: 88px;
  z-index: 90;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.nav-container {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  max-width: 1400px;
  margin: 0 auto;
  padding-bottom: 2px;
}

.nav-btn {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  font-size: 0.95rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: fit-content;
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(100, 181, 246, 0.15);
}

.nav-btn.active {
  background: linear-gradient(135deg, #64b5f6 0%, #1976d2 100%);
  color: white;
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 6px 20px rgba(100, 181, 246, 0.3);
}

.nav-btn.active:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(100, 181, 246, 0.4);
}

.nav-icon {
  font-size: 1.1rem;
}

.nav-text {
  font-weight: 600;
}

/* Content Area */
.dashboard-content {
  padding: 2rem;
  position: relative;
  z-index: 10;
  max-width: 1400px;
  margin: 0 auto;
}

.tab-content {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 500px;
}

.tab-content:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
  box-shadow: 0 20px 50px rgba(100, 181, 246, 0.1);
}

/* Responsive Design */
@media (max-width: 1024px) {
  .dashboard-content {
    padding: 1.5rem;
  }
  
  .tab-content {
    padding: 1.5rem;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    padding: 1rem;
  }
  
  .header-content {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .header-left h1 {
    font-size: 1.8rem;
  }
  
  .user-info {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .dashboard-nav {
    padding: 1rem;
    top: auto;
    position: relative;
  }
  
  .nav-container {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .nav-btn {
    font-size: 0.9rem;
    padding: 0.6rem 1.2rem;
  }
  
  .dashboard-content {
    padding: 1rem;
  }
  
  .tab-content {
    padding: 1rem;
    border-radius: 16px;
  }
  
  .floating-shape {
    display: none;
  }
  
  .gradient-orb {
    display: none;
  }
}

@media (max-width: 480px) {
  .header-left h1 {
    font-size: 1.5rem;
  }
  
  .nav-btn {
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
  }
  
  .nav-icon {
    font-size: 1rem;
  }
  
  .logout-btn {
    padding: 0.6rem 1.2rem;
    font-size: 0.9rem;
  }
}

/* Scrollbar Styling */
.nav-container::-webkit-scrollbar {
  height: 4px;
}

.nav-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 2px;
}

.nav-container::-webkit-scrollbar-thumb {
  background: rgba(100, 181, 246, 0.4);
  border-radius: 2px;
}

.nav-container::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 181, 246, 0.6);
}
</style>
