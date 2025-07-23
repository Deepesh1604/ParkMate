<template>
  <div class="user-dashboard">
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading your dashboard...</p>
    </div>
    
    <div v-else>
      <div class="dashboard-header">
        <h1>🚗 My ParkMate Dashboard</h1>
        <div class="user-info">
          <span>Welcome, {{ user.username || 'User' }}</span>
          <button @click="logout" class="logout-btn">Logout</button>
        </div>
      </div>

    <div class="dashboard-nav">
      <button 
        v-for="tab in tabs" 
        :key="tab.id" 
        :class="['nav-btn', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        {{ tab.name }}
      </button>
    </div>

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
  { id: 'overview', name: '📊 Overview' },
  { id: 'parking-lots', name: '🏢 Find Parking' },
  { id: 'reservations', name: '📋 My Reservations' },
  { id: 'active-parking', name: '🅿️ Active Parking' },
  { id: 'history', name: '📈 History' }
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
  background-color: #f8f9fa;
  margin: 0;
  padding: 0;
}

.dashboard-header {
  background-color: #2c3e50;
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.dashboard-header h1 {
  margin: 0;
  font-size: 1.8rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logout-btn {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.logout-btn:hover {
  background-color: #c0392b;
}

.dashboard-nav {
  background-color: white;
  padding: 1rem 2rem;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  gap: 1rem;
  overflow-x: auto;
}

.nav-btn {
  background-color: transparent;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
  font-size: 1rem;
}

.nav-btn:hover {
  background-color: #f8f9fa;
}

.nav-btn.active {
  background-color: #42b883;
  color: white;
}

.dashboard-content {
  padding: 2rem;
}

.tab-content {
  background-color: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  color: #6c757d;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #42b883;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .dashboard-nav {
    padding: 1rem;
  }
  
  .dashboard-content {
    padding: 1rem;
  }
  
  .tab-content {
    padding: 1rem;
  }
}
</style>
