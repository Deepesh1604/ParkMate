<template>
  <div class="admin-overview">
    <div style="display: flex; align-items: center; justify-content: space-between;">
      <h2>Dashboard Overview</h2>
      <button @click="$emit('refresh')" class="refresh-btn" title="Refresh Stats">🔄 Refresh</button>
    </div>
    
    <!-- Debug info -->
    <div v-if="!analytics || !analytics.summary" class="debug-info">
      <p>Analytics data: {{ JSON.stringify(analytics) }}</p>
    </div>
    
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">🏢</div>
        <div class="stat-content">
          <h3>{{ analytics.summary?.total_lots || 0 }}</h3>
          <p>Total Parking Lots</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">🅿️</div>
        <div class="stat-content">
          <h3>{{ analytics.summary?.total_spots || 0 }}</h3>
          <p>Total Parking Spots</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">🚗</div>
        <div class="stat-content">
          <h3>{{ analytics.summary?.occupied_spots || 0 }}</h3>
          <p>Occupied Spots</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <h3>{{ analytics.summary?.available_spots || 0 }}</h3>
          <p>Available Spots</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-content">
          <h3>{{ analytics.summary?.total_users || 0 }}</h3>
          <p>Registered Users</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-content">
          <h3>{{ analytics.summary?.active_reservations || 0 }}</h3>
          <p>Active Reservations</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">💰</div>
        <div class="stat-content">
          <h3>${{( analytics.summary?.total_revenue || 0 ).toFixed(2)}}</h3>
          <p>Total Revenue</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <h3>{{ analytics.summary?.occupancy_rate || 0 }}%</h3>
          <p>Occupancy Rate</p>
        </div>
      </div>
    </div>

    <div class="charts-section">
      <h3>Parking Lot Occupancy</h3>
      <div class="occupancy-chart">
        <div v-if="analytics.lot_occupancy?.length > 0" class="lot-cards">
          <div v-for="lot in analytics.lot_occupancy" :key="lot.id" class="lot-card">
            <h4>{{ lot.prime_location_name }}</h4>
            <div class="occupancy-bar">
              <div 
                class="occupancy-fill" 
                :style="{ width: lot.occupancy_rate + '%' }"
              ></div>
            </div>
            <div class="occupancy-details">
              <span>{{ lot.occupied_spots }}/{{ lot.total_spots }} spots</span>
              <span class="occupancy-rate">{{ lot.occupancy_rate }}%</span>
            </div>
          </div>
        </div>
        <div v-else class="no-data">
          <p>No parking lots available</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, watch } from 'vue';

defineEmits(['refresh']);

const props = defineProps({
  analytics: {
    type: Object,
    default: () => ({})
  }
});

// Debug: Watch analytics changes
watch(() => props.analytics, (newVal) => {
  console.log('Analytics data received:', newVal);
}, { immediate: true, deep: true });
</script>

<style scoped>
.admin-overview h2 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.debug-info {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 1rem;
  margin-bottom: 1rem;
  font-family: monospace;
  font-size: 0.875rem;
  color: #6c757d;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.stat-card {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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
  color: #2c3e50;
}

.stat-content p {
  margin: 0.5rem 0 0 0;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.charts-section {
  margin-top: 2rem;
}

.charts-section h3 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

.occupancy-chart {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
}

.lot-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.lot-card {
  background-color: white;
  border-radius: 6px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.lot-card h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.occupancy-bar {
  background-color: #e9ecef;
  height: 20px;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.occupancy-fill {
  height: 100%;
  background: linear-gradient(90deg, #42b883 0%, #f39c12 70%, #e74c3c 100%);
  transition: width 0.3s ease;
}

.occupancy-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: #7f8c8d;
}

.occupancy-rate {
  font-weight: bold;
  color: #2c3e50;
}

.no-data {
  text-align: center;
  color: #7f8c8d;
  padding: 2rem;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .lot-cards {
    grid-template-columns: 1fr;
  }
}
</style>

/* Add refresh button styles */
.refresh-btn {
  background: #42b883;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
  margin-left: 1rem;
}
.refresh-btn:hover {
  background: #369870;
}
