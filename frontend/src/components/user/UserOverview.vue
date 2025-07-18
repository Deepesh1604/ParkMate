<template>
  <div class="user-overview">
    <h2>Dashboard Overview</h2>
    
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-content">
          <h3>{{ analytics.summary?.total_reservations || 0 }}</h3>
          <p>Total Reservations</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">🚗</div>
        <div class="stat-content">
          <h3>{{ analytics.summary?.active_reservations || 0 }}</h3>
          <p>Active Reservations</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <h3>{{ analytics.summary?.completed_reservations || 0 }}</h3>
          <p>Completed Reservations</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">💰</div>
        <div class="stat-content">
          <h3>${{ analytics.summary?.total_spent || 0 }}</h3>
          <p>Total Spent</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">⏱️</div>
        <div class="stat-content">
          <h3>{{ analytics.summary?.average_duration_hours || 0 }}h</h3>
          <p>Average Duration</p>
        </div>
      </div>
    </div>

    <div class="charts-section">
      <h3>Recent Activity</h3>
      <div class="activity-chart">
        <div v-if="analytics.recent_activity?.length > 0" class="activity-list">
          <div v-for="activity in analytics.recent_activity" :key="activity.date" class="activity-item">
            <div class="activity-date">{{ formatDate(activity.date) }}</div>
            <div class="activity-count">{{ activity.count }} reservations</div>
          </div>
        </div>
        <div v-else class="no-activity">
          <p>No recent activity</p>
        </div>
      </div>
    </div>

    <div class="quick-actions">
      <h3>Quick Actions</h3>
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
  analytics: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits(['change-tab']);

const formatDate = (dateString) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString();
};
</script>

<style scoped>
.user-overview h2 {
  margin-bottom: 2rem;
  color: #2c3e50;
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
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-icon {
  font-size: 2rem;
  min-width: 50px;
  text-align: center;
}

.stat-content h3 {
  margin: 0;
  font-size: 1.8rem;
  color: white;
}

.stat-content p {
  margin: 0.5rem 0 0 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.charts-section {
  margin-top: 2rem;
  margin-bottom: 3rem;
}

.charts-section h3 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

.activity-chart {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e9ecef;
}

.activity-list {
  display: grid;
  gap: 1rem;
}

.activity-item {
  background-color: white;
  padding: 1rem;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.activity-date {
  font-weight: bold;
  color: #2c3e50;
}

.activity-count {
  color: #42b883;
  font-weight: bold;
}

.no-activity {
  text-align: center;
  color: #7f8c8d;
  padding: 2rem;
}

.quick-actions h3 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

.action-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.action-btn {
  padding: 1rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: bold;
  transition: all 0.3s;
}

.action-btn.primary {
  background-color: #42b883;
  color: white;
}

.action-btn.primary:hover {
  background-color: #38a169;
}

.action-btn.secondary {
  background-color: #3498db;
  color: white;
}

.action-btn.secondary:hover {
  background-color: #2980b9;
}

.action-btn.success {
  background-color: #27ae60;
  color: white;
}

.action-btn.success:hover {
  background-color: #219a52;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    grid-template-columns: 1fr;
  }
}
</style>
