<template>
  <div class="parking-history">
    <h2>Parking History</h2>
    
    <div class="history-stats">
      <div class="stat-card">
        <h3>{{ totalSessions }}</h3>
        <p>Total Sessions</p>
      </div>
      <div class="stat-card">
        <h3>${{ totalSpent }}</h3>
        <p>Total Spent</p>
      </div>
      <div class="stat-card">
        <h3>{{ averageDuration }}h</h3>
        <p>Average Duration</p>
      </div>
    </div>

    <div class="filter-section">
      <select v-model="selectedFilter" @change="filterHistory">
        <option value="all">All History</option>
        <option value="completed">Completed</option>
        <option value="expired">Expired</option>
        <option value="last-month">Last Month</option>
      </select>
    </div>

    <div v-if="filteredHistory.length === 0" class="no-history">
      <p>No parking history found.</p>
    </div>

    <div v-else class="history-list">
      <div v-for="reservation in filteredHistory" :key="reservation.id" class="history-card">
        <div class="history-header">
          <h3>{{ reservation.prime_location_name }}</h3>
          <span :class="['status-badge', getStatusClass(reservation.status)]">
            {{ reservation.status }}
          </span>
        </div>
        
        <div class="history-details">
          <div class="detail-row">
            <span class="detail-label">Spot:</span>
            <span class="detail-value">{{ reservation.spot_number }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Date:</span>
            <span class="detail-value">{{ formatDate(reservation.created_at) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Duration:</span>
            <span class="detail-value">{{ calculateSessionDuration(reservation) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Cost:</span>
            <span class="detail-value">${{ reservation.parking_cost || '0.00' }}</span>
          </div>
        </div>

        <div class="history-timeline">
          <div class="timeline-item">
            <div class="timeline-dot active"></div>
            <div class="timeline-content">
              <strong>Reserved</strong>
              <p>{{ formatDateTime(reservation.created_at) }}</p>
            </div>
          </div>
          
          <div v-if="reservation.parking_timestamp" class="timeline-item">
            <div class="timeline-dot active"></div>
            <div class="timeline-content">
              <strong>Parked</strong>
              <p>{{ formatDateTime(reservation.parking_timestamp) }}</p>
            </div>
          </div>
          
          <div v-if="reservation.leaving_timestamp" class="timeline-item">
            <div class="timeline-dot active"></div>
            <div class="timeline-content">
              <strong>Released</strong>
              <p>{{ formatDateTime(reservation.leaving_timestamp) }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Summary Chart -->
    <div class="chart-section">
      <h3>Monthly Spending</h3>
      <div class="chart-container">
        <div class="chart-bars">
          <div v-for="month in monthlyData" :key="month.month" class="chart-bar">
            <div class="bar-fill" :style="{ height: (month.amount / maxAmount * 100) + '%' }"></div>
            <span class="bar-label">{{ month.month }}</span>
            <span class="bar-amount">${{ month.amount }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const reservations = ref([]);
const selectedFilter = ref('all');

const loadHistory = async () => {
  try {
    const response = await axios.get('/api/user/my-reservations');
    reservations.value = response.data.reservations;
  } catch (error) {
    console.error('Error loading history:', error);
  }
};

const filteredHistory = computed(() => {
  let filtered = reservations.value;
  
  switch (selectedFilter.value) {
    case 'completed':
      filtered = filtered.filter(r => r.status === 'completed');
      break;
    case 'expired':
      filtered = filtered.filter(r => r.status === 'expired');
      break;
    case 'last-month':
      const lastMonth = new Date();
      lastMonth.setMonth(lastMonth.getMonth() - 1);
      filtered = filtered.filter(r => new Date(r.created_at) >= lastMonth);
      break;
  }
  
  return filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
});

const totalSessions = computed(() => {
  return reservations.value.filter(r => r.status === 'completed').length;
});

const totalSpent = computed(() => {
  return reservations.value
    .filter(r => r.parking_cost)
    .reduce((sum, r) => sum + parseFloat(r.parking_cost || 0), 0)
    .toFixed(2);
});

const averageDuration = computed(() => {
  const completedReservations = reservations.value.filter(r => 
    r.status === 'completed' && r.parking_timestamp && r.leaving_timestamp
  );
  
  if (completedReservations.length === 0) return '0';
  
  const totalDuration = completedReservations.reduce((sum, r) => {
    const start = new Date(r.parking_timestamp);
    const end = new Date(r.leaving_timestamp);
    return sum + (end - start) / (1000 * 60 * 60);
  }, 0);
  
  return (totalDuration / completedReservations.length).toFixed(1);
});

const monthlyData = computed(() => {
  const months = {};
  const now = new Date();
  
  // Initialize last 6 months
  for (let i = 5; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const monthKey = date.toLocaleDateString('en-US', { month: 'short' });
    months[monthKey] = 0;
  }
  
  // Calculate spending per month
  reservations.value.forEach(r => {
    if (r.parking_cost) {
      const date = new Date(r.created_at);
      const monthKey = date.toLocaleDateString('en-US', { month: 'short' });
      if (months.hasOwnProperty(monthKey)) {
        months[monthKey] += parseFloat(r.parking_cost);
      }
    }
  });
  
  return Object.entries(months).map(([month, amount]) => ({
    month,
    amount: amount.toFixed(2)
  }));
});

const maxAmount = computed(() => {
  return Math.max(...monthlyData.value.map(m => parseFloat(m.amount)), 1);
});

const filterHistory = () => {
  // Trigger reactivity
};

const formatDate = (isoString) => {
  if (!isoString) return 'N/A';
  return new Date(isoString).toLocaleDateString();
};

const formatDateTime = (isoString) => {
  if (!isoString) return 'N/A';
  return new Date(isoString).toLocaleString();
};

const calculateSessionDuration = (reservation) => {
  if (!reservation.parking_timestamp || !reservation.leaving_timestamp) return 'N/A';
  
  const start = new Date(reservation.parking_timestamp);
  const end = new Date(reservation.leaving_timestamp);
  const diffHours = (end - start) / (1000 * 60 * 60);
  
  return `${diffHours.toFixed(1)}h`;
};

const getStatusClass = (status) => {
  switch (status) {
    case 'completed': return 'completed';
    case 'expired': return 'expired';
    case 'active': return 'active';
    default: return 'default';
  }
};

onMounted(() => {
  loadHistory();
});
</script>

<style scoped>
.parking-history h2 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.history-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: linear-gradient(135deg, #42b883 0%, #38a169 100%);
  color: white;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-card h3 {
  margin: 0;
  font-size: 2rem;
}

.stat-card p {
  margin: 0.5rem 0 0 0;
  opacity: 0.9;
}

.filter-section {
  margin-bottom: 2rem;
}

.filter-section select {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.no-history {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
}

.history-list {
  display: grid;
  gap: 1.5rem;
}

.history-card {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.history-header h3 {
  margin: 0;
  color: #2c3e50;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: bold;
}

.status-badge.completed {
  background-color: #d4edda;
  color: #155724;
}

.status-badge.expired {
  background-color: #f8d7da;
  color: #721c24;
}

.status-badge.active {
  background-color: #fff3cd;
  color: #856404;
}

.history-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-weight: bold;
  color: #6c757d;
  font-size: 0.875rem;
}

.detail-value {
  color: #2c3e50;
}

.history-timeline {
  display: flex;
  gap: 2rem;
  margin-top: 1rem;
}

.timeline-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #42b883;
  flex-shrink: 0;
}

.timeline-content {
  flex: 1;
}

.timeline-content strong {
  display: block;
  color: #2c3e50;
  font-size: 0.875rem;
}

.timeline-content p {
  margin: 0;
  color: #6c757d;
  font-size: 0.75rem;
}

.chart-section {
  margin-top: 3rem;
}

.chart-section h3 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

.chart-container {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
}

.chart-bars {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  height: 200px;
}

.chart-bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.bar-fill {
  background: linear-gradient(to top, #42b883, #38a169);
  width: 100%;
  min-height: 4px;
  border-radius: 4px 4px 0 0;
  transition: height 0.3s ease;
}

.bar-label {
  font-size: 0.875rem;
  color: #6c757d;
}

.bar-amount {
  font-size: 0.75rem;
  font-weight: bold;
  color: #2c3e50;
}

@media (max-width: 768px) {
  .history-stats {
    grid-template-columns: 1fr;
  }
  
  .history-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .history-details {
    grid-template-columns: 1fr;
  }
  
  .history-timeline {
    flex-direction: column;
    gap: 1rem;
  }
  
  .chart-bars {
    height: 150px;
  }
}
</style>
