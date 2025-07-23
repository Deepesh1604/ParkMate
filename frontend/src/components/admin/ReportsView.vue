<template>
  <div class="reports-view">
    <div class="reports-header">
      <h2>📊 Analytics & Reports</h2>
      <div class="refresh-section">
        <button @click="refreshAllData" class="refresh-btn" :disabled="loading">
          <span v-if="loading">🔄 Refreshing...</span>
          <span v-else>🔄 Refresh Data</span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading analytics data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
      <button @click="refreshAllData" class="retry-btn">Try Again</button>
    </div>

    <!-- Main Content -->
    <div v-else class="reports-content">
      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="card">
          <div class="card-icon">🚗</div>
          <div class="card-content">
            <h3>{{ analytics.summary?.total_spots || 0 }}</h3>
            <p>Total Parking Spots</p>
            <small>{{ analytics.summary?.occupancy_rate || 0 }}% Occupied</small>
          </div>
        </div>
        <div class="card">
          <div class="card-icon">👥</div>
          <div class="card-content">
            <h3>{{ analytics.summary?.total_users || 0 }}</h3>
            <p>Registered Users</p>
            <small>{{ analytics.summary?.active_reservations || 0 }} Active</small>
          </div>
        </div>
        <div class="card">
          <div class="card-icon">💰</div>
          <div class="card-content">
            <h3>${{ analytics.summary?.total_revenue || 0 }}</h3>
            <p>Total Revenue</p>
            <small>All time earnings</small>
          </div>
        </div>
        <div class="card">
          <div class="card-icon">📍</div>
          <div class="card-content">
            <h3>{{ analytics.summary?.total_lots || 0 }}</h3>
            <p>Parking Lots</p>
            <small>{{ analytics.summary?.available_spots || 0 }} Available</small>
          </div>
        </div>
      </div>

      <!-- Charts Grid -->
      <div class="charts-grid">
        <!-- Occupancy Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <h3>🎯 Lot Occupancy Rates</h3>
            <p>Real-time occupancy across all parking lots</p>
          </div>
          <canvas ref="occupancyChart" class="chart"></canvas>
        </div>

        <!-- Weekly Trends -->
        <div class="chart-container">
          <div class="chart-header">
            <h3>📈 Available Day Trends</h3>
            <p v-if="weeklyData.daily_data?.length">Daily reservations and revenue for the past week</p>
            <p v-else-if="dailySimple.available_days?.length" class="fallback-message">
              Showing {{ dailySimple.available_days.length }} days of available data
            </p>
            <p v-else class="no-data-message">No reservation data available yet</p>
          </div>
          <canvas ref="weeklyChart" class="chart"></canvas>
        </div>

        <!-- Hourly Distribution -->
        <div class="chart-container">
          <div class="chart-header">
            <h3>⏰ Today's Hourly Activity</h3>
            <p v-if="weeklyData.hourly_data?.length">Reservation patterns throughout the day</p>
            <p v-else class="no-data-message">No hourly data available - no reservations made today</p>
          </div>
          <canvas ref="hourlyChart" class="chart"></canvas>
        </div>

        <!-- Top Users -->
        <div class="chart-container">
          <div class="chart-header">
            <h3>👑 Top Users (This Week)</h3>
            <p v-if="weeklyData.top_users?.length">Most active users by reservations</p>
            <p v-else class="no-data-message">No user activity data available for this week</p>
          </div>
          <canvas ref="topUsersChart" class="chart"></canvas>
        </div>

        <!-- Monthly Trends -->
        <div class="chart-container full-width">
          <div class="chart-header">
            <h3>📊 6-Month Revenue & Usage Trends</h3>
            <p v-if="monthlyData.monthly_trends?.length">Long-term performance analysis</p>
            <p v-else class="no-data-message">No monthly trend data available - need historical reservations</p>
          </div>
          <canvas ref="monthlyChart" class="chart"></canvas>
        </div>

        <!-- Lot Performance -->
        <div class="chart-container full-width">
          <div class="chart-header">
            <h3>🏆 Parking Lot Performance (Last Month)</h3>
            <p v-if="monthlyData.lot_performance?.length">Revenue and reservation comparison by location</p>
            <p v-else class="no-data-message">No lot performance data available for the last month</p>
          </div>
          <canvas ref="lotPerformanceChart" class="chart"></canvas>
        </div>
      </div>

      <!-- Export Section -->
      <div class="export-section">
        <h3>📄 Export Reports</h3>
        <div class="export-buttons">
          <button @click="exportDailyReport" class="export-btn">
            📋 Daily Report
          </button>
          <button @click="exportWeeklyReport" class="export-btn">
            📊 Weekly Report
          </button>
          <button @click="exportMonthlyReport" class="export-btn">
            📈 Monthly Report
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import axios from 'axios';
import {
  Chart,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

// Register Chart.js components
Chart.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

// Reactive data
const loading = ref(false);
const error = ref(null);
const analytics = ref({});
const weeklyData = ref({});
const monthlyData = ref({});
const dailySimple = ref({});

// Chart refs
const occupancyChart = ref(null);
const weeklyChart = ref(null);
const hourlyChart = ref(null);
const topUsersChart = ref(null);
const monthlyChart = ref(null);
const lotPerformanceChart = ref(null);

// Chart instances
let occupancyChartInstance = null;
let weeklyChartInstance = null;
let hourlyChartInstance = null;
let topUsersChartInstance = null;
let monthlyChartInstance = null;
let lotPerformanceChartInstance = null;

// Color palette
const colors = {
  primary: '#42b883',
  secondary: '#2c3e50',
  danger: '#e74c3c',
  warning: '#f39c12',
  info: '#3498db',
  success: '#27ae60',
  purple: '#9b59b6',
  orange: '#e67e22'
};

// Load all data
const loadAnalytics = async () => {
  try {
    const response = await axios.get('/api/admin/analytics');
    analytics.value = response.data;
  } catch (err) {
    console.error('Error loading analytics:', err);
    throw err;
  }
};

const loadWeeklyData = async () => {
  try {
    const response = await axios.get('/api/admin/reports/weekly');
    weeklyData.value = response.data;
  } catch (err) {
    console.error('Error loading weekly data:', err);
    // Set default empty data structure instead of throwing
    weeklyData.value = {
      daily_data: [],
      hourly_data: [],
      top_users: []
    };
  }
};

const loadMonthlyData = async () => {
  try {
    const response = await axios.get('/api/admin/reports/monthly');
    monthlyData.value = response.data;
  } catch (err) {
    console.error('Error loading monthly data:', err);
    // Set default empty data structure instead of throwing
    monthlyData.value = {
      monthly_trends: [],
      lot_performance: []
    };
  }
};

const loadDailySimple = async () => {
  try {
    const response = await axios.get('/api/admin/reports/daily-simple');
    dailySimple.value = response.data;
  } catch (err) {
    console.error('Error loading daily simple data:', err);
    // Set default empty data structure
    dailySimple.value = {
      today: { total_reservations_today: 0, revenue_today: 0 },
      available_days: [],
      has_data: false
    };
  }
};

// Chart creation functions
const createOccupancyChart = () => {
  if (!analytics.value.lot_occupancy?.length) return;
  
  const ctx = occupancyChart.value.getContext('2d');
  const lots = analytics.value.lot_occupancy;
  
  occupancyChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: lots.map(lot => lot.prime_location_name),
      datasets: [{
        data: lots.map(lot => lot.occupancy_rate || 0),
        backgroundColor: [
          colors.primary,
          colors.info,
          colors.warning,
          colors.danger,
          colors.success,
          colors.purple
        ],
        borderWidth: 2,
        borderColor: '#fff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.label}: ${context.parsed}%`;
            }
          }
        }
      }
    }
  });
};

const createWeeklyChart = () => {
  const ctx = weeklyChart.value.getContext('2d');
  
  // Try to use weekly data first, then fall back to daily simple data
  if (weeklyData.value.daily_data?.length) {
    const data = weeklyData.value.daily_data;
    
    weeklyChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.map(d => new Date(d.date).toLocaleDateString()),
        datasets: [
          {
            label: 'Reservations',
            data: data.map(d => d.reservations),
            borderColor: colors.primary,
            backgroundColor: colors.primary + '20',
            tension: 0.4,
            yAxisID: 'y'
          },
          {
            label: 'Revenue ($)',
            data: data.map(d => d.revenue),
            borderColor: colors.warning,
            backgroundColor: colors.warning + '20',
            tension: 0.4,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top'
          }
        },
        scales: {
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: {
              display: true,
              text: 'Reservations'
            }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            title: {
              display: true,
              text: 'Revenue ($)'
            },
            grid: {
              drawOnChartArea: false,
            },
          }
        }
      }
    });
  } else if (dailySimple.value.available_days?.length) {
    // Use available days data as fallback
    const data = dailySimple.value.available_days;
    
    weeklyChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.map(d => new Date(d.date).toLocaleDateString()),
        datasets: [{
          label: 'Reservations (Available Days)',
          data: data.map(d => d.reservations),
          backgroundColor: colors.primary,
          borderColor: colors.primary,
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Reservations'
            }
          }
        }
      }
    });
  } else {
    // Create a message chart for no data
    weeklyChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['No Data'],
        datasets: [{
          label: 'No weekly data available',
          data: [0],
          borderColor: colors.secondary,
          backgroundColor: colors.secondary + '20',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: () => 'No weekly data available for the last 7 days'
            }
          }
        },
        scales: {
          y: {
            display: false
          },
          x: {
            display: false
          }
        }
      }
    });
  }
};

const createHourlyChart = () => {
  if (!weeklyData.value.hourly_data?.length) {
    // Create a message chart for no data
    const ctx = hourlyChart.value.getContext('2d');
    hourlyChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['No Data'],
        datasets: [{
          label: 'No hourly data available',
          data: [0],
          backgroundColor: colors.secondary,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: () => 'No hourly data available for today'
            }
          }
        },
        scales: {
          y: {
            display: false
          },
          x: {
            display: false
          }
        }
      }
    });
    return;
  }
  
  const ctx = hourlyChart.value.getContext('2d');
  const data = weeklyData.value.hourly_data;
  
  // Fill missing hours with 0
  const hourlyReservations = new Array(24).fill(0);
  data.forEach(d => {
    hourlyReservations[parseInt(d.hour)] = d.reservations;
  });
  
  hourlyChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: Array.from({length: 24}, (_, i) => `${i}:00`),
      datasets: [{
        label: 'Reservations',
        data: hourlyReservations,
        backgroundColor: colors.info,
        borderColor: colors.info,
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Number of Reservations'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Hour of Day'
          }
        }
      }
    }
  });
};

const createTopUsersChart = () => {
  if (!weeklyData.value.top_users?.length) {
    // Create a message chart for no data
    const ctx = topUsersChart.value.getContext('2d');
    topUsersChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['No Users'],
        datasets: [{
          label: 'No user data available',
          data: [0],
          backgroundColor: colors.secondary,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: () => 'No user activity data available for this week'
            }
          }
        },
        scales: {
          x: {
            display: false
          },
          y: {
            display: false
          }
        }
      }
    });
    return;
  }
  
  const ctx = topUsersChart.value.getContext('2d');
  const users = weeklyData.value.top_users.slice(0, 5); // Top 5 users
  
  topUsersChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: users.map(user => user.username),
      datasets: [{
        label: 'Reservations',
        data: users.map(user => user.total_reservations),
        backgroundColor: colors.success,
        borderColor: colors.success,
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Number of Reservations'
          }
        }
      }
    }
  });
};

const createMonthlyChart = () => {
  if (!monthlyData.value.monthly_trends?.length) {
    // Create a message chart for no data
    const ctx = monthlyChart.value.getContext('2d');
    monthlyChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['No Data'],
        datasets: [{
          label: 'No monthly data available',
          data: [0],
          borderColor: colors.secondary,
          backgroundColor: colors.secondary + '20',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: () => 'No monthly trend data available for the last 6 months'
            }
          }
        },
        scales: {
          y: {
            display: false
          },
          x: {
            display: false
          }
        }
      }
    });
    return;
  }
  
  const ctx = monthlyChart.value.getContext('2d');
  const trends = monthlyData.value.monthly_trends;
  
  monthlyChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: trends.map(t => t.month),
      datasets: [
        {
          label: 'Reservations',
          data: trends.map(t => t.reservations),
          borderColor: colors.primary,
          backgroundColor: colors.primary + '20',
          tension: 0.4,
          yAxisID: 'y'
        },
        {
          label: 'Revenue ($)',
          data: trends.map(t => t.revenue),
          borderColor: colors.warning,
          backgroundColor: colors.warning + '20',
          tension: 0.4,
          yAxisID: 'y1'
        },
        {
          label: 'Unique Users',
          data: trends.map(t => t.unique_users),
          borderColor: colors.info,
          backgroundColor: colors.info + '20',
          tension: 0.4,
          yAxisID: 'y'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top'
        }
      },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: {
            display: true,
            text: 'Count'
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: {
            display: true,
            text: 'Revenue ($)'
          },
          grid: {
            drawOnChartArea: false,
          },
        }
      }
    }
  });
};

const createLotPerformanceChart = () => {
  if (!monthlyData.value.lot_performance?.length) {
    // Create a message chart for no data
    const ctx = lotPerformanceChart.value.getContext('2d');
    lotPerformanceChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['No Data'],
        datasets: [{
          label: 'No lot performance data available',
          data: [0],
          backgroundColor: colors.secondary,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: () => 'No lot performance data available for the last month'
            }
          }
        },
        scales: {
          y: {
            display: false
          },
          x: {
            display: false
          }
        }
      }
    });
    return;
  }
  
  const ctx = lotPerformanceChart.value.getContext('2d');
  const performance = monthlyData.value.lot_performance;
  
  lotPerformanceChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: performance.map(lot => lot.prime_location_name),
      datasets: [
        {
          label: 'Total Reservations',
          data: performance.map(lot => lot.total_reservations || 0),
          backgroundColor: colors.primary,
          yAxisID: 'y'
        },
        {
          label: 'Total Revenue ($)',
          data: performance.map(lot => lot.total_revenue || 0),
          backgroundColor: colors.warning,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top'
        }
      },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: {
            display: true,
            text: 'Reservations'
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: {
            display: true,
            text: 'Revenue ($)'
          },
          grid: {
            drawOnChartArea: false,
          },
        }
      }
    }
  });
};

// Destroy all charts
const destroyCharts = () => {
  [
    occupancyChartInstance,
    weeklyChartInstance,
    hourlyChartInstance,
    topUsersChartInstance,
    monthlyChartInstance,
    lotPerformanceChartInstance
  ].forEach(chart => {
    if (chart) {
      chart.destroy();
    }
  });
};

// Create all charts
const createAllCharts = async () => {
  await nextTick();
  destroyCharts();
  
  createOccupancyChart();
  createWeeklyChart();
  createHourlyChart();
  createTopUsersChart();
  createMonthlyChart();
  createLotPerformanceChart();
};

// Refresh all data
const refreshAllData = async () => {
  try {
    loading.value = true;
    error.value = null;
    
    // Load analytics first (most important)
    await loadAnalytics();
    
    // Load daily simple data (fallback for when no complex data exists)
    await loadDailySimple();
    
    // Load weekly and monthly data (these can fail gracefully)
    await Promise.all([
      loadWeeklyData(),
      loadMonthlyData()
    ]);
    
    await createAllCharts();
  } catch (err) {
    // Only show error if analytics failed
    if (err.message && err.message.includes('analytics')) {
      error.value = 'Failed to load analytics data. Please try again.';
    } else {
      error.value = 'Some reports data could not be loaded, but basic analytics are available.';
    }
    console.error('Error refreshing data:', err);
  } finally {
    loading.value = false;
  }
};

// Export functions
const exportDailyReport = () => {
  const today = new Date().toISOString().split('T')[0];
  window.open(`/api/admin/reports/daily/${today}`, '_blank');
};

const exportWeeklyReport = () => {
  // Create CSV from weekly data or available data
  let csvContent = '';
  
  if (weeklyData.value.daily_data?.length) {
    csvContent = generateWeeklyCsv();
  } else if (dailySimple.value.available_days?.length) {
    csvContent = generateSimpleCsv();
  } else {
    alert('No data available to export');
    return;
  }
  
  downloadCsv(csvContent, `weekly-report-${new Date().toISOString().split('T')[0]}.csv`);
};

const generateSimpleCsv = () => {
  if (!dailySimple.value.available_days) return '';
  
  const headers = ['Date', 'Reservations'];
  const rows = dailySimple.value.available_days.map(d => [
    d.date,
    d.reservations
  ]);
  
  return [headers, ...rows].map(row => row.join(',')).join('\n');
};

const exportMonthlyReport = () => {
  // Create CSV from monthly data
  const csvContent = generateMonthlyCsv();
  downloadCsv(csvContent, `monthly-report-${new Date().toISOString().split('T')[0]}.csv`);
};

const generateWeeklyCsv = () => {
  if (!weeklyData.value.daily_data) return '';
  
  const headers = ['Date', 'Reservations', 'Completed', 'Active', 'Revenue'];
  const rows = weeklyData.value.daily_data.map(d => [
    d.date,
    d.reservations,
    d.completed,
    d.active,
    d.revenue
  ]);
  
  return [headers, ...rows].map(row => row.join(',')).join('\n');
};

const generateMonthlyCsv = () => {
  if (!monthlyData.value.monthly_trends) return '';
  
  const headers = ['Month', 'Reservations', 'Revenue', 'Unique Users'];
  const rows = monthlyData.value.monthly_trends.map(t => [
    t.month,
    t.reservations,
    t.revenue,
    t.unique_users
  ]);
  
  return [headers, ...rows].map(row => row.join(',')).join('\n');
};

const downloadCsv = (content, filename) => {
  const blob = new Blob([content], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
};

// Initialize on mount
onMounted(() => {
  refreshAllData();
});
</script>

<style scoped>
.reports-view {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.reports-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e9ecef;
}

.reports-header h2 {
  color: #2c3e50;
  margin: 0;
  font-size: 2rem;
  font-weight: bold;
}

.refresh-btn {
  background: linear-gradient(135deg, #42b883, #369870);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(66, 184, 131, 0.3);
}

.refresh-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #369870, #2d7a5f);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(66, 184, 131, 0.4);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Loading and Error States */
.loading-container, .error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
  color: #6c757d;
}

.spinner {
  width: 50px;
  height: 50px;
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

/* Summary Cards */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.card {
  background: linear-gradient(135deg, #fff, #f8f9fa);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.card-icon {
  font-size: 2.5rem;
  opacity: 0.8;
}

.card-content h3 {
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
  margin: 0;
}

.card-content p {
  color: #6c757d;
  margin: 0.25rem 0;
  font-weight: 500;
}

.card-content small {
  color: #42b883;
  font-size: 0.85rem;
  font-weight: bold;
}

/* Charts Grid */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.chart-container {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.chart-container:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.chart-container.full-width {
  grid-column: 1 / -1;
}

.chart-header {
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e9ecef;
}

.chart-header h3 {
  color: #2c3e50;
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  font-weight: bold;
}

.chart-header p {
  color: #6c757d;
  margin: 0;
  font-size: 0.9rem;
}

.no-data-message {
  color: #e74c3c !important;
  font-style: italic;
  font-weight: 500;
}

.fallback-message {
  color: #f39c12 !important;
  font-style: italic;
  font-weight: 500;
}

.chart {
  height: 300px !important;
  width: 100% !important;
}

/* Export Section */
.export-section {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  border: 1px solid #dee2e6;
}

.export-section h3 {
  color: #2c3e50;
  margin: 0 0 1.5rem 0;
  font-size: 1.5rem;
}

.export-buttons {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.export-btn {
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);
}

.export-btn:hover {
  background: linear-gradient(135deg, #2980b9, #21618c);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.4);
}

/* Responsive Design */
@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-container.full-width {
    grid-column: 1;
  }
}

@media (max-width: 768px) {
  .reports-view {
    padding: 1rem;
  }
  
  .reports-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .reports-header h2 {
    font-size: 1.5rem;
  }
  
  .summary-cards {
    grid-template-columns: 1fr;
  }
  
  .card {
    flex-direction: column;
    text-align: center;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .chart-container {
    padding: 1rem;
  }
  
  .chart {
    height: 250px !important;
  }
  
  .export-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .export-btn {
    width: 100%;
    max-width: 200px;
  }
}

/* Animation for smooth transitions */
.reports-content {
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

/* Custom scrollbar */
.reports-view::-webkit-scrollbar {
  width: 8px;
}

.reports-view::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.reports-view::-webkit-scrollbar-thumb {
  background: #42b883;
  border-radius: 4px;
}

.reports-view::-webkit-scrollbar-thumb:hover {
  background: #369870;
}
</style>

