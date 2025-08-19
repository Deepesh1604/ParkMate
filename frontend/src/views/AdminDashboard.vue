<template>
  <div class="admin-dashboard">
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

    <!-- Professional Header -->
    <div class="dashboard-header">
      <div class="header-content">
        <div class="brand-section">
          <div class="logo-icon">P</div>
          <h1>ParkMate Admin</h1>
        </div>
        <div class="admin-info">
          <div class="admin-details">
            <span class="welcome-text">Welcome back,</span>
            <span class="admin-name">{{ admin.username || 'Admin' }}</span>
          </div>
          <button @click="logout" class="logout-btn">
            <span class="logout-icon">⚡</span>
            Logout
          </button>
        </div>
      </div>
    </div>

    <!-- Glass Morphism Navigation -->
    <div class="dashboard-nav">
      <div class="nav-container">
        <button 
          v-for="tab in tabs" 
          :key="tab.id" 
          :class="['nav-btn', { active: activeTab === tab.id }]"
          @click="setActiveTab(tab.id)"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-name">{{ tab.name }}</span>
        </button>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div class="dashboard-content">
      <div class="content-wrapper">
        <!-- Overview Tab -->
        <div v-if="activeTab === 'overview'" class="tab-content" ref="overviewTab">
          <div class="tab-header">
            <h2>📊 Dashboard Overview</h2>
            <p>Monitor your parking system performance and key metrics</p>
          </div>
          <AdminOverview :analytics="analytics" @refresh="loadAnalytics" />
        </div>

        <!-- Parking Lots Tab -->
        <div v-if="activeTab === 'parking-lots'" class="tab-content" ref="parkingLotsTab">
          <div class="tab-header">
            <h2>🏢 Parking Lots Management</h2>
            <p>Manage and configure your parking lot locations</p>
          </div>
          <ParkingLotsManagement @refresh="loadParkingLots" />
        </div>

        <!-- Parking Spots Tab -->
        <div v-if="activeTab === 'parking-spots'" class="tab-content" ref="parkingSpotsTab">
          <div class="tab-header">
            <h2>🅿️ Parking Spots Overview</h2>
            <p>Monitor individual parking spot status and availability</p>
          </div>
          <ParkingSpotsView />
        </div>

        <!-- Users Tab -->
        <div v-if="activeTab === 'users'" class="tab-content" ref="usersTab">
          <div class="tab-header">
            <h2>👥 User Management</h2>
            <p>Manage user accounts and permissions</p>
          </div>
          <UsersManagement />
        </div>

        <!-- Reports Tab -->
        <div v-if="activeTab === 'reports'" class="tab-content" ref="reportsTab">
          <div class="tab-header">
            <h2>📈 Analytics & Reports</h2>
            <p>Generate insights and performance reports</p>
          </div>
          <ReportsView />
        </div>
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
  { id: 'overview', name: 'Overview', icon: '📊' },
  { id: 'parking-lots', name: 'Parking Lots', icon: '🏢' },
  { id: 'parking-spots', name: 'Parking Spots', icon: '🅿️' },
  { id: 'users', name: 'Users', icon: '👥' },
  { id: 'reports', name: 'Reports', icon: '📈' }
];

const setActiveTab = (tabId) => {
  activeTab.value = tabId;
  
  // Add smooth transition animation
  const content = document.querySelector('.tab-content');
  if (content) {
    content.style.opacity = '0';
    content.style.transform = 'translateY(10px)';
    
    setTimeout(() => {
      content.style.opacity = '1';
      content.style.transform = 'translateY(0)';
    }, 150);
  }
};

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
/* CSS Variables for consistent theming */
:root {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  --accent-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  --admin-gradient: linear-gradient(135deg, #8B2BDA 0%, #6A1B9A 50%, #4A148C 100%);
  --glass-bg: rgba(255, 255, 255, 0.1);
  --glass-bg-strong: rgba(255, 255, 255, 0.25);
  --glass-border: rgba(255, 255, 255, 0.2);
  --shadow-soft: 0 8px 32px rgba(31, 38, 135, 0.15);
  --shadow-hover: 0 15px 35px rgba(31, 38, 135, 0.25);
  --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Global Dashboard Styles */
.admin-dashboard {
  min-height: 100vh;
  background: var(--primary-gradient);
  position: relative;
  overflow-x: hidden;
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
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 50px;
  height: 50px;
  top: 20%;
  right: 20%;
  animation-delay: 2s;
}

.shape-3 {
  width: 90px;
  height: 90px;
  bottom: 20%;
  left: 15%;
  animation-delay: 4s;
}

.shape-4 {
  width: 60px;
  height: 60px;
  top: 60%;
  right: 10%;
  animation-delay: 1s;
}

.shape-5 {
  width: 80px;
  height: 80px;
  bottom: 10%;
  right: 30%;
  animation-delay: 3s;
}

.shape-6 {
  width: 45px;
  height: 45px;
  top: 40%;
  left: 5%;
  animation-delay: 5s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -30px) scale(1.1);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.9);
  }
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
  animation: float 12s ease-in-out infinite;
}

.orb-1 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.4) 0%, transparent 70%);
  top: 20%;
  left: 80%;
  animation-delay: 0s;
}

.orb-2 {
  width: 150px;
  height: 150px;
  background: radial-gradient(circle, rgba(118, 75, 162, 0.4) 0%, transparent 70%);
  bottom: 30%;
  left: 10%;
  animation-delay: 4s;
}

.orb-3 {
  width: 180px;
  height: 180px;
  background: radial-gradient(circle, rgba(79, 172, 254, 0.3) 0%, transparent 70%);
  top: 60%;
  right: 20%;
  animation-delay: 8s;
}

/* Dashboard Header */
.dashboard-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(25px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.25);
  padding: 1.5rem 0;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.1);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  font-weight: bold;
  box-shadow: 0 12px 30px rgba(102, 126, 234, 0.4);
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.dashboard-header h1 {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #fff 0%, #e0e0e0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.admin-info {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.admin-details {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.welcome-text {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

.admin-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 16px;
  cursor: pointer;
  transition: var(--transition-smooth);
  font-weight: 500;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1);
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.28);
  border-color: rgba(255, 255, 255, 0.4);
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
}

.logout-icon {
  font-size: 1rem;
}

/* Dashboard Navigation */
.dashboard-nav {
  position: sticky;
  top: 88px;
  z-index: 99;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  padding: 1rem 0;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.08);
}

.nav-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.nav-container::-webkit-scrollbar {
  display: none;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: rgba(255, 255, 255, 0.95);
  padding: 0.875rem 1.5rem;
  border-radius: 16px;
  cursor: pointer;
  transition: var(--transition-smooth);
  white-space: nowrap;
  font-weight: 500;
  min-width: fit-content;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.08);
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.35);
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
}

.nav-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: rgba(102, 126, 234, 0.6);
  color: white;
  box-shadow: 0 12px 30px rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
}

.tab-icon {
  font-size: 1.1rem;
}

.tab-name {
  font-size: 0.95rem;
}

/* Dashboard Content */
.dashboard-content {
  position: relative;
  z-index: 2;
  padding: 2rem 0;
  min-height: calc(100vh - 200px);
}

.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
}

.tab-content {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(30px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 24px;
  padding: 2.5rem;
  box-shadow: 0 20px 40px rgba(102, 126, 234, 0.15), 0 8px 32px rgba(118, 75, 162, 0.1);
  transition: var(--transition-smooth);
  opacity: 1;
  transform: translateY(0);
}

.tab-content:hover {
  box-shadow: 0 25px 50px rgba(102, 126, 234, 0.25), 0 15px 35px rgba(118, 75, 162, 0.15);
  border-color: rgba(255, 255, 255, 0.35);
  transform: translateY(-5px);
}

.tab-header {
  margin-bottom: 2rem;
  text-align: center;
}

.tab-header h2 {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
  text-shadow: 0 2px 10px rgba(102, 126, 234, 0.1);
}

.tab-header p {
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .header-content,
  .nav-container,
  .content-wrapper {
    padding: 0 1.5rem;
  }
  
  .dashboard-header h1 {
    font-size: 1.75rem;
  }
  
  .tab-content {
    padding: 2rem;
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .admin-info {
    flex-direction: column;
    gap: 1rem;
  }
  
  .admin-details {
    align-items: center;
  }
  
  .nav-container {
    padding: 0 1rem;
    gap: 0.75rem;
  }
  
  .nav-btn {
    padding: 0.75rem 1.25rem;
    font-size: 0.9rem;
  }
  
  .tab-icon {
    font-size: 1rem;
  }
  
  .dashboard-content {
    padding: 1.5rem 0;
  }
  
  .content-wrapper {
    padding: 0 1rem;
  }
  
  .tab-content {
    padding: 1.5rem;
  }
  
  .tab-header h2 {
    font-size: 1.75rem;
  }
  
  .tab-header p {
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .dashboard-header {
    padding: 1rem 0;
  }
  
  .dashboard-header h1 {
    font-size: 1.5rem;
  }
  
  .logo-icon {
    width: 40px;
    height: 40px;
    font-size: 1.25rem;
  }
  
  .nav-btn {
    flex-direction: column;
    gap: 0.5rem;
    padding: 1rem;
    text-align: center;
  }
  
  .tab-name {
    font-size: 0.85rem;
  }
  
  .tab-content {
    padding: 1.25rem;
  }
  
  .tab-header h2 {
    font-size: 1.5rem;
  }
}
</style>
