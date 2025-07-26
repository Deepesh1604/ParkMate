<template>
  <div class="user-overview">
    <div class="overview-header">
      <h2>📊 Dashboard Overview</h2>
      <button @click="refreshData" class="refresh-btn" :disabled="refreshing">
        <span v-if="refreshing">🔄 Refreshing...</span>
        <span v-else>🔄 Refresh</span>
      </button>
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading your dashboard...</p>
    </div>
    
    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
      <button @click="refreshData" class="retry-btn">Try Again</button>
    </div>
    
    <!-- Content -->
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">📋</div>
          <div class="stat-content">
            <h3>{{ userAnalytics.summary?.total_reservations || 0 }}</h3>
            <p>Total Reservations</p>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">🚗</div>
          <div class="stat-content">
            <h3>{{ userAnalytics.summary?.active_reservations || 0 }}</h3>
            <p>Active Reservations</p>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">✅</div>
          <div class="stat-content">
            <h3>{{ userAnalytics.summary?.completed_reservations || 0 }}</h3>
            <p>Completed Reservations</p>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">💰</div>
          <div class="stat-content">
            <h3>${{ formatCurrency(userAnalytics.summary?.total_spent || 0) }}</h3>
            <p>Total Spent</p>
          </div>
        </div>
        
      </div>

      <div class="charts-section">
        <h3>📈 Recent Activity (Last 30 Days)</h3>
        <div class="activity-chart">
          <div v-if="userAnalytics.recent_activity?.length > 0" class="activity-list">
            <div v-for="activity in userAnalytics.recent_activity" :key="activity.date" class="activity-item">
              <div class="activity-date">{{ formatDate(activity.date) }}</div>
              <div class="activity-count">
                {{ activity.count }} reservation{{ activity.count !== 1 ? 's' : '' }}
              </div>
            </div>
          </div>
          <div v-else class="no-activity">
            <div class="no-activity-icon">📊</div>
            <h4>No Recent Activity</h4>
            <p>You haven't made any reservations in the last 30 days.</p>
            <button @click="$emit('change-tab', 'parking-lots')" class="find-parking-btn">
              🏢 Find Parking Now
            </button>
          </div>
        </div>
      </div>

      <div class="quick-actions">
        <h3>🚀 Quick Actions</h3>
        <div class="action-buttons">
          <button @click="$emit('change-tab', 'parking-lots')" class="action-btn primary">
            🏢 Find Parking
          </button>
          <button @click="$emit('change-tab', 'reservations')" class="action-btn secondary">
            📋 My Reservations
          </button>
          <button @click="$emit('change-tab', 'active-parking')" class="action-btn success">
            🅿️ Active Parking
          </button>
          <button @click="$emit('change-tab', 'history')" class="action-btn info">
            📈 History
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, defineEmits } from 'vue';
import axios from 'axios';

const emit = defineEmits(['change-tab']);

const userAnalytics = ref({});
const loading = ref(false);
const refreshing = ref(false);
const error = ref(null);

const loadUserAnalytics = async () => {
  try {
    const response = await axios.get('/api/user/analytics');
    userAnalytics.value = response.data;
    error.value = null;
  } catch (err) {
    console.error('Error loading user analytics:', err);
    error.value = 'Failed to load dashboard data. Please try again.';
    // Set default data structure to prevent errors
    userAnalytics.value = {
      summary: {
        total_reservations: 0,
        active_reservations: 0,
        completed_reservations: 0,
        total_spent: 0,
        average_duration_hours: 0
      },
      recent_activity: []
    };
  }
};

const refreshData = async () => {
  if (refreshing.value) return;
  
  try {
    refreshing.value = true;
    await loadUserAnalytics();
  } finally {
    refreshing.value = false;
  }
};

const formatCurrency = (amount) => {
  if (!amount || isNaN(amount)) return '0.00';
  return parseFloat(amount).toFixed(2);
};

const formatDuration = (hours) => {
  if (!hours || isNaN(hours)) return '0.0';
  return parseFloat(hours).toFixed(1);
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
};

onMounted(() => {
  loading.value = true;
  loadUserAnalytics().finally(() => {
    loading.value = false;
  });
});
</script>

<style scoped>
.overview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e9ecef;
}

.overview-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.8rem;
}

.refresh-btn {
  background: linear-gradient(135deg, #42b883, #369870);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(66, 184, 131, 0.3);
}

.refresh-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #369870, #2d7a5f);
  transform: translateY(-1px);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Loading and Error States */
.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  text-align: center;
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

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.retry-btn {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 1rem;
}

.retry-btn:hover {
  background-color: #c0392b;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.stat-card {
  background: linear-gradient(135deg, #42b883 0%, #38a169 100%);
  color: white;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 12px rgba(66, 184, 131, 0.3);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(66, 184, 131, 0.4);
}

.stat-icon {
  font-size: 2rem;
  min-width: 50px;
  text-align: center;
  opacity: 0.9;
}

.stat-content h3 {
  margin: 0;
  font-size: 1.8rem;
  color: white;
  font-weight: bold;
}

.stat-content p {
  margin: 0.5rem 0 0 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
  font-weight: 500;
}

.charts-section {
  margin-top: 2rem;
  margin-bottom: 3rem;
}

.charts-section h3 {
  margin-bottom: 1rem;
  color: #2c3e50;
  font-size: 1.3rem;
}

.activity-chart {
  background-color: #f8f9fa;
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid #e9ecef;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.activity-list {
  display: grid;
  gap: 1rem;
  max-height: 300px;
  overflow-y: auto;
}

.activity-item {
  background-color: white;
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.activity-item:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.activity-date {
  font-weight: bold;
  color: #2c3e50;
}

.activity-count {
  color: #42b883;
  font-weight: bold;
  background-color: rgba(66, 184, 131, 0.1);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
}

.no-activity {
  text-align: center;
  color: #7f8c8d;
  padding: 3rem 2rem;
}

.no-activity-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-activity h4 {
  margin: 0 0 0.5rem 0;
  color: #6c757d;
  font-size: 1.2rem;
}

.no-activity p {
  margin: 0 0 1.5rem 0;
  color: #95a5a6;
}

.find-parking-btn {
  background: linear-gradient(135deg, #42b883, #369870);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
}

.find-parking-btn:hover {
  background: linear-gradient(135deg, #369870, #2d7a5f);
  transform: translateY(-2px);
}

.quick-actions h3 {
  margin-bottom: 1.5rem;
  color: #2c3e50;
  font-size: 1.3rem;
}

.action-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.action-btn {
  padding: 1rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: bold;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.action-btn.primary {
  background: linear-gradient(135deg, #42b883, #369870);
  color: white;
}

.action-btn.secondary {
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: white;
}

.action-btn.success {
  background: linear-gradient(135deg, #27ae60, #219a52);
  color: white;
}

.action-btn.info {
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  color: white;
}

@media (max-width: 768px) {
  .overview-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    grid-template-columns: 1fr;
  }
  
  .activity-item {
    flex-direction: column;
    text-align: center;
    gap: 0.5rem;
  }
}

/* Smooth animations */
.user-overview {
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
