<template>
  <div class="admin-dashboard">
    <div class="dashboard-header">
      <h1>🚗 Admin Dashboard</h1>
      <div class="admin-info">
        <span>Welcome, {{ admin.username || 'Admin' }}</span>
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
        <AdminOverview :analytics="analytics" @refresh="loadAnalytics" />
      </div>

      <!-- Parking Lots Tab -->
      <div v-if="activeTab === 'parking-lots'" class="tab-content">
        <ParkingLotsManagement @refresh="loadParkingLots" />
      </div>

      <!-- Parking Spots Tab -->
      <div v-if="activeTab === 'parking-spots'" class="tab-content">
        <ParkingSpotsView />
      </div>

      <!-- Users Tab -->
      <div v-if="activeTab === 'users'" class="tab-content">
        <UsersManagement />
      </div>

      <!-- Reports Tab -->
      <div v-if="activeTab === 'reports'" class="tab-content">
        <ReportsView />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import AdminOverview from '../components/admin/AdminOverview.vue';
import ParkingLotsManagement from '../components/admin/ParkingLotsManagement.vue';
import ParkingSpotsView from '../components/admin/ParkingSpotsView.vue';
import UsersManagement from '../components/admin/UsersManagement.vue';
import ReportsView from '../components/admin/ReportsView.vue';

const router = useRouter();
const activeTab = ref('overview');
const admin = ref({ username: '', email: '', id: null });
const analytics = ref({});
const loading = ref(true);

const tabs = [
  { id: 'overview', name: '📊 Overview' },
  { id: 'parking-lots', name: '🏢 Parking Lots' },
  { id: 'parking-spots', name: '🅿️ Parking Spots' },
  { id: 'users', name: '👥 Users' },
  { id: 'reports', name: '📈 Reports' }
];

const loadAnalytics = async () => {
  try {
    loading.value = true;
    console.log('Loading analytics...');
    
    // Fetch admin analytics
    const analyticsResponse = await axios.get('/api/admin/analytics');
    console.log('Analytics response:', analyticsResponse.data);
    analytics.value = analyticsResponse.data;
    
    // Set admin info from session if available
    admin.value = { 
      username: 'Admin', 
      email: 'admin@parkmate.com', 
      id: 1 
    };
    
  } catch (error) {
    console.error('Error loading admin data:', error);
    console.error('Error response:', error.response?.data);
    console.error('Error status:', error.response?.status);
    
    // If admin is not authenticated, redirect to login
    if (error.response?.status === 401 || error.response?.status === 403) {
      router.push('/login');
    }
  } finally {
    loading.value = false;
  }
};

const loadParkingLots = async () => {
  // This function can be called to refresh data when needed
  await loadAnalytics();
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
  loadAnalytics();
});
</script>

<style scoped>
.admin-dashboard {
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

.admin-info {
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
