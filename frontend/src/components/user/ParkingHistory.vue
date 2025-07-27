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
      
      <div class="export-dropdown">
        <button @click="showExportMenu = !showExportMenu" class="export-btn">
          <span class="export-icon">📥</span>
          Export Data
          <span class="dropdown-arrow">▼</span>
        </button>
        <div v-if="showExportMenu" class="dropdown-menu" @click.stop>
          <button @click="exportData('overall')" class="dropdown-item">
            <span class="item-icon">📋</span>
            Overall Data Export
          </button>
          <button @click="exportData('last-month')" class="dropdown-item">
            <span class="item-icon">📅</span>
            Last Month Export
          </button>
          <button @click="exportData('last-6-months')" class="dropdown-item">
            <span class="item-icon">📊</span>
            Last 6 Months Export
          </button>
          <button @click="previewCSV()" class="dropdown-item">
            <span class="item-icon">👁️</span>
            Preview CSV Format
          </button>
        </div>
      </div>
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
      <h3>Monthly Spending (Last 6 Months)</h3>
      <div class="chart-container">
        <div class="chart-bars">
          <div v-for="month in monthlyData" :key="month.month" class="chart-bar">
            <div 
              class="bar-fill" 
              :style="{ 
                height: parseFloat(month.amount) > 0 ? (parseFloat(month.amount) / maxAmount * 100) + '%' : '2px'
              }"
              :title="`${month.month}: $${month.amount}`"
            ></div>
            <span class="bar-label">{{ month.month }}</span>
            <span class="bar-amount">${{ month.amount }}</span>
          </div>
        </div>
        <div class="chart-debug" v-if="monthlyData.length === 0">
          <p>No monthly data available</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import axios from 'axios';

const reservations = ref([]);
const selectedFilter = ref('all');
const showExportMenu = ref(false);

const loadHistory = async () => {
  try {
    const response = await axios.get('/api/user/my-reservations');
    reservations.value = response.data.reservations;
    console.log('Loaded reservations:', reservations.value.length);
    console.log('Sample reservation:', reservations.value[0]);
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
    case 'last-month': {
      const lastMonth = new Date();
      lastMonth.setMonth(lastMonth.getMonth() - 1);
      filtered = filtered.filter(r => new Date(r.created_at) >= lastMonth);
      break;
    }
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
  const now = new Date();
  const monthsData = [];
  
  // Initialize last 6 months with proper date tracking
  for (let i = 5; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const monthKey = date.toLocaleDateString('en-US', { month: 'short' });
    const year = date.getFullYear();
    const month = date.getMonth();
    
    monthsData.push({
      monthKey,
      year,
      month,
      amount: 0
    });
  }
  
  // Calculate spending per month
  reservations.value.forEach(r => {
    if (r.parking_cost && r.created_at) {
      const reservationDate = new Date(r.created_at);
      const reservationYear = reservationDate.getFullYear();
      const reservationMonth = reservationDate.getMonth();
      
      // Find matching month in our 6-month window
      const monthIndex = monthsData.findIndex(m => 
        m.year === reservationYear && m.month === reservationMonth
      );
      
      if (monthIndex !== -1) {
        monthsData[monthIndex].amount += parseFloat(r.parking_cost);
      }
    }
  });
  
  // Return formatted data
  return monthsData.map(m => ({
    month: m.monthKey,
    amount: m.amount.toFixed(2)
  }));
});

const maxAmount = computed(() => {
  const amounts = monthlyData.value.map(m => parseFloat(m.amount));
  const max = Math.max(...amounts);
  return max > 0 ? max : 100; // Use 100 as default if no data
});

const filterHistory = () => {
  // Trigger reactivity
};

const formatDate = (isoString) => {
  if (!isoString) return 'N/A';
  return new Date(isoString).toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit' 
  });
};

const formatDateTime = (isoString) => {
  if (!isoString) return 'N/A';
  return new Date(isoString).toLocaleString('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
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

const exportData = async (type) => {
  showExportMenu.value = false;
  
  try {
    let dataToExport = [];
    const now = new Date();
    
    switch (type) {
      case 'overall':
        dataToExport = reservations.value;
        break;
      case 'last-month': {
        const lastMonth = new Date();
        lastMonth.setMonth(lastMonth.getMonth() - 1);
        dataToExport = reservations.value.filter(r => new Date(r.created_at) >= lastMonth);
        break;
      }
      case 'last-6-months': {
        const sixMonthsAgo = new Date();
        sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
        dataToExport = reservations.value.filter(r => new Date(r.created_at) >= sixMonthsAgo);
        break;
      }
    }
    
    if (dataToExport.length === 0) {
      alert('No data available for the selected period.');
      return;
    }
    
    // Create CSV content with proper escaping
    const headers = [
      'Location',
      'Spot Number',
      'Reservation Date',
      'Parking Start',
      'Parking End',
      'Duration (hours)',
      'Cost ($)',
      'Status'
    ];
    
    // Create CSV rows with consistent formatting
    const csvRows = dataToExport.map(reservation => {
      const location = reservation.prime_location_name || 'N/A';
      const spotNumber = reservation.spot_number ? reservation.spot_number.toString() : 'N/A';
      const reservationDate = formatDate(reservation.created_at);
      const parkingStart = reservation.parking_timestamp ? formatDateTime(reservation.parking_timestamp) : 'N/A';
      const parkingEnd = reservation.leaving_timestamp ? formatDateTime(reservation.leaving_timestamp) : 'N/A';
      const duration = calculateDurationForExport(reservation);
      const cost = reservation.parking_cost ? parseFloat(reservation.parking_cost).toFixed(2) : '0.00';
      const status = reservation.status || 'N/A';
      
      // Escape quotes in data and wrap each field in quotes
      const row = [
        `"${location.replace(/"/g, '""')}"`,
        `"${spotNumber}"`,
        `"${reservationDate}"`,
        `"${parkingStart}"`,
        `"${parkingEnd}"`,
        `"${duration}"`,
        `"${cost}"`,
        `"${status}"`
      ];
      
      return row.join(',');
    });
    
    const csvContent = [headers.join(','), ...csvRows].join('\n');
    
    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `parking_history_${type}_${now.toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    // Show success message
    alert(`Successfully exported ${dataToExport.length} records!`);
    
  } catch (error) {
    console.error('Export error:', error);
    alert('Failed to export data. Please try again.');
  }
};

const calculateDurationForExport = (reservation) => {
  if (!reservation.parking_timestamp || !reservation.leaving_timestamp) return 'N/A';
  
  const start = new Date(reservation.parking_timestamp);
  const end = new Date(reservation.leaving_timestamp);
  const diffHours = (end - start) / (1000 * 60 * 60);
  
  return diffHours.toFixed(1);
};

const previewCSV = () => {
  showExportMenu.value = false;
  
  if (reservations.value.length === 0) {
    alert('No data available to preview.');
    return;
  }
  
  // Get first record for preview
  const sampleReservation = reservations.value[0];
  
  const headers = [
    'Location',
    'Spot Number', 
    'Reservation Date',
    'Parking Start',
    'Parking End',
    'Duration (hours)',
    'Cost ($)',
    'Status'
  ];
  
  const sampleData = [
    sampleReservation.prime_location_name || 'N/A',
    sampleReservation.spot_number ? sampleReservation.spot_number.toString() : 'N/A',
    formatDate(sampleReservation.created_at),
    sampleReservation.parking_timestamp ? formatDateTime(sampleReservation.parking_timestamp) : 'N/A',
    sampleReservation.leaving_timestamp ? formatDateTime(sampleReservation.leaving_timestamp) : 'N/A',
    calculateDurationForExport(sampleReservation),
    sampleReservation.parking_cost ? parseFloat(sampleReservation.parking_cost).toFixed(2) : '0.00',
    sampleReservation.status || 'N/A'
  ];
  
  let previewText = 'CSV Preview (First Record):\n\n';
  previewText += 'Headers:\n';
  headers.forEach((header, index) => {
    previewText += `${index + 1}. ${header}\n`;
  });
  
  previewText += '\nSample Data:\n';
  sampleData.forEach((data, index) => {
    previewText += `${index + 1}. ${data}\n`;
  });
  
  previewText += `\nTotal records available: ${reservations.value.length}`;
  
  alert(previewText);
};

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest('.export-dropdown')) {
    showExportMenu.value = false;
  }
};

onMounted(() => {
  loadHistory();
  document.addEventListener('click', handleClickOutside);
});

// Debug watcher for monthly data
watch(monthlyData, (newData) => {
  console.log('Monthly data updated:', newData);
  console.log('Max amount:', maxAmount.value);
}, { immediate: true });

// Clean up event listener
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
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
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.filter-section select {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.export-dropdown {
  position: relative;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #42b883 0%, #38a169 100%);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(66, 184, 131, 0.2);
}

.export-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(66, 184, 131, 0.3);
}

.export-icon {
  font-size: 1rem;
}

.dropdown-arrow {
  font-size: 0.8rem;
  transition: transform 0.2s ease;
}

.export-btn:hover .dropdown-arrow {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 200px;
  overflow: hidden;
  margin-top: 0.25rem;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s ease;
  font-size: 0.9rem;
  color: #2c3e50;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

.item-icon {
  font-size: 1rem;
  width: 16px;
  text-align: center;
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

.chart-debug {
  text-align: center;
  color: #6c757d;
  font-style: italic;
  padding: 2rem;
}

.bar-fill:hover {
  opacity: 0.8;
  cursor: pointer;
}

@media (max-width: 768px) {
  .history-stats {
    grid-template-columns: 1fr;
  }
  
  .filter-section {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }
  
  .filter-section select,
  .export-btn {
    width: 100%;
    justify-content: center;
  }
  
  .dropdown-menu {
    left: 0;
    right: 0;
    width: 100%;
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
