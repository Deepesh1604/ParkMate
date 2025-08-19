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
  color: white;
  background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.debug-info {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
  font-family: monospace;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.8);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover {
  transform: translateY(-5px);
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 15px 40px rgba(102, 126, 234, 0.2);
}

.stat-icon {
  font-size: 2rem;
  min-width: 50px;
  text-align: center;
  filter: drop-shadow(0 2px 4px rgba(102, 126, 234, 0.3));
}

.stat-content h3 {
  margin: 0;
  font-size: 1.8rem;
  background: linear-gradient(135deg, #ffffff 0%, #e0e0e0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.stat-content p {
  margin: 0.5rem 0 0 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
  font-weight: 500;
}

.charts-section {
  margin-top: 2rem;
}

.charts-section h3 {
  margin-bottom: 1rem;
  color: white;
  background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 600;
}

.occupancy-chart {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.1);
}

.lot-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.lot-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 12px;
  padding: 1rem;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.lot-card:hover {
  transform: translateY(-3px);
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.35);
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.15);
}

.lot-card h4 {
  margin: 0 0 1rem 0;
  color: white;
  font-weight: 600;
}

.occupancy-bar {
  background: rgba(255, 255, 255, 0.2);
  height: 20px;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 0.5rem;
  backdrop-filter: blur(5px);
}

.occupancy-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 70%, #f093fb 100%);
  transition: width 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.occupancy-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

.occupancy-rate {
  font-weight: bold;
  color: white;
}

.no-data {
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  padding: 2rem;
}

.refresh-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 0.5rem 1rem;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-left: 1rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
  font-weight: 500;
}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
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
