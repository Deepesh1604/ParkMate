<template>
  <div class="reports-view">
    <div class="header-section">
      <h1>📊 Analytics Dashboard</h1>
      <div class="action-buttons">
        <button @click="refreshData" :disabled="loading" class="refresh-btn">
          <span class="btn-icon">🔄</span>
          {{ loading ? 'Loading...' : 'Refresh Data' }}
        </button>
        <div class="dropdown-container">
          <button @click="showExportMenu = !showExportMenu" class="export-btn">
            <span class="btn-icon">📥</span>
            Export Data
            <span class="arrow">▼</span>
          </button>
          <div v-if="showExportMenu" class="dropdown-menu">
            <button @click="exportData('all')" class="dropdown-item">
              <span class="item-icon">📋</span>
              All Data
            </button>
            <button @click="exportData('reservations')" class="dropdown-item">
              <span class="item-icon">🎫</span>
              Reservations
            </button>
            <button @click="exportData('occupancy')" class="dropdown-item">
              <span class="item-icon">🏢</span>
              Occupancy
            </button>
            <button @click="exportData('revenue')" class="dropdown-item">
              <span class="item-icon">💰</span>
              Revenue
            </button>
            <button @click="exportData('users')" class="dropdown-item">
              <span class="item-icon">👥</span>
              Users
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Status Messages -->
    <div v-if="statusMessage" class="status-message" :class="statusType">
      {{ statusMessage }}
    </div>

    <!-- Loading Spinner -->
    <div v-if="loading" class="loading-spinner">
      <div class="spinner"></div>
      <p>Loading analytics data...</p>
    </div>

    <!-- Dashboard Content -->
    <div v-if="!loading && dashboardData" class="dashboard-grid">
      
      <!-- Key Metrics Cards -->
     <!-- <div class="metrics-section">
        <h2>📈 Key Metrics</h2>
        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-icon">🚗</div>
            <div class="metric-content">
              <h3>{{ totalOccupiedSpots }}</h3>
              <p>Occupied Spots</p>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">💰</div>
            <div class="metric-content">
              <h3>${{ totalRevenue.toFixed(2) }}</h3>
              <p>Total Revenue (30d)</p>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">📅</div>
            <div class="metric-content">
              <h3>{{ totalReservations }}</h3>
              <p>Total Reservations</p>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-content">
              <h3>{{ occupancyRate }}%</h3>
              <p>Occupancy Rate</p>
            </div>
          </div>
        </div>
      </div> -->

      <!-- Occupancy Analysis -->
      <div class="chart-section">
        <h2>🏢 Occupancy Analysis</h2>
        <div class="chart-grid">
          <div class="chart-container">
            <h3>Current Occupancy by Location</h3>
            <div class="chart-wrapper">
              <Doughnut 
                :data="occupancyChartData" 
                :options="occupancyChartOptions"
                :key="'occupancy-' + chartKey"
              />
            </div>
          </div>
          <div class="chart-container">
            <h3>Occupancy Rate Comparison</h3>
            <div class="chart-wrapper">
              <BarChart 
                :data="occupancyBarData" 
                :options="occupancyBarOptions"
                :key="'occupancy-bar-' + chartKey"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Revenue Analysis -->
      <div class="chart-section">
        <h2>💰 Revenue Analysis</h2>
        <div class="chart-grid">
          <div class="chart-container">
            <h3>Daily Revenue Trend (Last 30 Days)</h3>
            <div class="chart-wrapper">
              <LineChart 
                :data="revenueChartData" 
                :options="revenueChartOptions"
                :key="'revenue-' + chartKey"
              />
            </div>
          </div>
          <div class="chart-container">
            <h3>Monthly Revenue Trends</h3>
            <div class="chart-wrapper">
              <BarChart 
                :data="monthlyRevenueData" 
                :options="monthlyRevenueOptions"
                :key="'monthly-' + chartKey"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Usage Patterns -->
      <div class="chart-section">
        <h2>📈 Usage Patterns</h2>
        <div class="chart-grid">
          <div class="chart-container">
            <h3>Hourly Usage Pattern</h3>
            <div class="chart-wrapper">
              <LineChart 
                :data="hourlyUsageData" 
                :options="hourlyUsageOptions"
                :key="'hourly-' + chartKey"
              />
            </div>
          </div>
          <div class="chart-container">
            <h3>Parking Duration Distribution</h3>
            <div class="chart-wrapper">
              <Pie 
                :data="durationChartData" 
                :options="durationChartOptions"
                :key="'duration-' + chartKey"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Top Users -->
      <div class="chart-section">
        <h2>👥 Top Active Users</h2>
        <div class="chart-container full-width">
          <h3>Most Active Users (Last 30 Days)</h3>
          <div class="chart-wrapper">
            <BarChart 
              :data="topUsersData" 
              :options="topUsersOptions"
              :key="'users-' + chartKey"
            />
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import axios from 'axios'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js'

import { Line as LineChart, Bar as BarChart, Doughnut, Pie } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
)

export default {
  name: 'ReportsView',
  components: {
    LineChart,
    BarChart,
    Doughnut,
    Pie
  },
  data() {
    return {
      loading: false,
      dashboardData: null,
      statusMessage: '',
      statusType: '',
      showExportMenu: false,
      chartKey: 0,
      API_BASE: 'http://localhost:5000',
      
      // Chart colors
      colors: {
        primary: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#A8E6CF', '#FFD93D'],
        secondary: ['rgba(255, 107, 107, 0.6)', 'rgba(78, 205, 196, 0.6)', 'rgba(69, 183, 209, 0.6)', 'rgba(150, 206, 180, 0.6)'],
        gradient: {
          revenue: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          occupancy: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
          usage: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
        }
      }
    }
  },
  
  computed: {
    totalOccupiedSpots() {
      if (!this.dashboardData?.occupancy) return 0
      return this.dashboardData.occupancy.reduce((sum, item) => sum + (item.occupied_spots || 0), 0)
    },
    totalRevenue() {
      if (!this.dashboardData?.revenue) return 0
      return this.dashboardData.revenue.reduce((sum, item) => sum + (item.revenue || 0), 0)
    },
    totalReservations() {
      if (!this.dashboardData?.revenue) return 0
      return this.dashboardData.revenue.reduce((sum, item) => sum + (item.reservations || 0), 0)
    },
    occupancyRate() {
      if (!this.dashboardData?.occupancy) return 0
      const totalSpots = this.dashboardData.occupancy.reduce((sum, item) => sum + (item.total_spots || 0), 0)
      const occupiedSpots = this.totalOccupiedSpots
      return totalSpots > 0 ? Math.round((occupiedSpots / totalSpots) * 100) : 0
    },
    
    // Chart Data
    occupancyChartData() {
      if (!this.dashboardData?.occupancy) return { labels: [], datasets: [] }
      
      return {
        labels: this.dashboardData.occupancy.map(item => item.prime_location_name),
        datasets: [{
          data: this.dashboardData.occupancy.map(item => item.occupied_spots),
          backgroundColor: this.colors.primary,
          borderWidth: 2,
          borderColor: '#fff'
        }]
      }
    },
    
    occupancyBarData() {
      if (!this.dashboardData?.occupancy) return { labels: [], datasets: [] }
      
      return {
        labels: this.dashboardData.occupancy.map(item => item.prime_location_name),
        datasets: [
          {
            label: 'Occupied',
            data: this.dashboardData.occupancy.map(item => item.occupied_spots),
            backgroundColor: '#FF6B6B',
            borderColor: '#FF6B6B',
            borderWidth: 1
          },
          {
            label: 'Available',
            data: this.dashboardData.occupancy.map(item => item.available_spots),
            backgroundColor: '#4ECDC4',
            borderColor: '#4ECDC4',
            borderWidth: 1
          }
        ]
      }
    },
    
    revenueChartData() {
      if (!this.dashboardData?.revenue) return { labels: [], datasets: [] }
      
      const sortedData = [...this.dashboardData.revenue].sort((a, b) => new Date(a.date) - new Date(b.date))
      
      return {
        labels: sortedData.map(item => new Date(item.date).toLocaleDateString()),
        datasets: [{
          label: 'Daily Revenue ($)',
          data: sortedData.map(item => item.revenue),
          borderColor: '#667eea',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#667eea',
          pointBorderColor: '#fff',
          pointBorderWidth: 2
        }]
      }
    },
    
    monthlyRevenueData() {
      if (!this.dashboardData?.monthly_trends) return { labels: [], datasets: [] }
      
      return {
        labels: this.dashboardData.monthly_trends.map(item => item.month),
        datasets: [{
          label: 'Monthly Revenue ($)',
          data: this.dashboardData.monthly_trends.map(item => item.revenue),
          backgroundColor: '#45B7D1',
          borderColor: '#45B7D1',
          borderWidth: 1
        }]
      }
    },
    
    hourlyUsageData() {
      if (!this.dashboardData?.hourly_usage) return { labels: [], datasets: [] }
      
      // Create 24-hour array
      const hourlyData = new Array(24).fill(0)
      this.dashboardData.hourly_usage.forEach(item => {
        const hour = parseInt(item.hour)
        hourlyData[hour] = item.reservations
      })
      
      return {
        labels: Array.from({length: 24}, (_, i) => `${i.toString().padStart(2, '0')}:00`),
        datasets: [{
          label: 'Reservations',
          data: hourlyData,
          borderColor: '#FF6B6B',
          backgroundColor: 'rgba(255, 107, 107, 0.1)',
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#FF6B6B',
          pointBorderColor: '#fff',
          pointBorderWidth: 2
        }]
      }
    },
    
    durationChartData() {
      if (!this.dashboardData?.duration_analysis) return { labels: [], datasets: [] }
      
      return {
        labels: this.dashboardData.duration_analysis.map(item => item.duration_category),
        datasets: [{
          data: this.dashboardData.duration_analysis.map(item => item.count),
          backgroundColor: this.colors.primary.slice(0, this.dashboardData.duration_analysis.length),
          borderWidth: 2,
          borderColor: '#fff'
        }]
      }
    },
    
    topUsersData() {
      if (!this.dashboardData?.top_users) return { labels: [], datasets: [] }
      
      return {
        labels: this.dashboardData.top_users.map(item => item.username),
        datasets: [
          {
            label: 'Reservations',
            data: this.dashboardData.top_users.map(item => item.total_reservations),
            backgroundColor: '#4ECDC4',
            borderColor: '#4ECDC4',
            borderWidth: 1,
            yAxisID: 'y'
          },
          {
            label: 'Total Spent ($)',
            data: this.dashboardData.top_users.map(item => item.total_spent),
            backgroundColor: '#FECA57',
            borderColor: '#FECA57',
            borderWidth: 1,
            yAxisID: 'y1'
          }
        ]
      }
    },

    // Chart Options
    occupancyChartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 20,
              usePointStyle: true,
              color: 'white'
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const total = context.dataset.data.reduce((a, b) => a + b, 0)
                const percentage = ((context.parsed * 100) / total).toFixed(1)
                return `${context.label}: ${context.parsed} spots (${percentage}%)`
              }
            }
          }
        }
      }
    },
    
    occupancyBarOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#ffffff'
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(255, 255, 255, 0.2)'
            },
            ticks: {
              color: '#ffffff'
            }
          },
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: '#ffffff'
            }
          }
        }
      }
    },
    
    revenueChartOptions() {
      return {
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
            grid: {
              color: 'rgba(255, 255, 255, 0.2)'
            },
            ticks: {
              callback: (value) => `$${value}`,
              color: '#ffffff'
            }
          },
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: '#ffffff'
            }
          }
        }
      }
    },
    
    monthlyRevenueOptions() {
      return {
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
            grid: {
              color: 'rgba(255, 255, 255, 0.2)'
            },
            ticks: {
              callback: (value) => `$${value}`,
              color: '#ffffff'
            }
          },
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: '#ffffff'
            }
          }
        }
      }
    },
    
    hourlyUsageOptions() {
      return {
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
            grid: {
              color: 'rgba(255, 255, 255, 0.2)'
            },
            ticks: {
              color: '#ffffff'
            }
          },
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: '#ffffff'
            }
          }
        }
      }
    },
    
    durationChartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 20,
              usePointStyle: true,
              color: '#ffffff'
            }
          }
        }
      }
    },
    
    topUsersOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: 'white'
            }
          }
        },
        scales: {
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            beginAtZero: true,
            grid: {
              color: 'rgba(255, 255, 255, 0.2)'
            },
            title: {
              display: true,
              text: 'Reservations',
              color: 'white'
            },
            ticks: {
              color: 'white'
            }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            beginAtZero: true,
            grid: {
              drawOnChartArea: false,
              color: 'rgba(255, 255, 255, 0.2)'
            },
            title: {
              display: true,
              text: 'Amount Spent ($)',
              color: 'white'
            },
            ticks: {
              callback: (value) => `$${value}`,
              color: 'white'
            }
          },
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: 'white'
            }
          }
        }
      }
    }
  },
  
  mounted() {
    this.refreshData()
    // Click outside to close dropdown
    document.addEventListener('click', this.closeDropdown)
  },
  
  beforeUnmount() {
    document.removeEventListener('click', this.closeDropdown)
  },
  
  methods: {
    async refreshData() {
      this.loading = true
      this.statusMessage = ''
      
      console.log('🔍 Fetching dashboard data from:', `${this.API_BASE}/api/admin/analytics/dashboard-data`)
      
      try {
        const response = await fetch(`${this.API_BASE}/api/admin/analytics/dashboard-data`, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        })
        
        console.log('📡 Response status:', response.status)
        console.log('📡 Response headers:', response.headers)
        
        if (response.ok) {
          this.dashboardData = await response.json()
          console.log('✅ Dashboard data received:', this.dashboardData)
          this.chartKey++ // Force chart re-render
          this.showStatus('Data refreshed successfully!', 'success')
        } else if (response.status === 401) {
          this.showStatus('Session expired. Please login again as admin.', 'error')
        } else if (response.status === 403) {
          this.showStatus('Access denied. Please login as admin.', 'error')
        } else {
          const errorText = await response.text()
          console.error('❌ API Error:', errorText)
          this.showStatus(`Failed to load dashboard data: HTTP ${response.status}`, 'error')
        }
      } catch (error) {
        console.error('❌ Network error:', error)
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
          this.showStatus('Cannot connect to server. Please ensure the backend is running on port 5000.', 'error')
        } else {
          this.showStatus('Failed to load dashboard data. Please try again.', 'error')
        }
      } finally {
        this.loading = false
      }
    },
    
    async exportData(type) {
      this.showExportMenu = false
      this.showStatus('Preparing export...', 'info')
      
      try {
        const response = await fetch(`${this.API_BASE}/api/admin/analytics/export-csv`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({ type })
        })
        
        if (response.ok) {
          const data = await response.json()
          
          // Create and download file
          const blob = new Blob([data.csv_data], { type: 'text/csv' })
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = data.filename
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
          window.URL.revokeObjectURL(url)
          
          this.showStatus(`${type} data exported successfully!`, 'success')
        } else {
          throw new Error(`HTTP ${response.status}`)
        }
      } catch (error) {
        console.error('Export error:', error)
        this.showStatus('Export failed. Please try again.', 'error')
      }
    },
    
    showStatus(message, type) {
      this.statusMessage = message
      this.statusType = type
      setTimeout(() => {
        this.statusMessage = ''
      }, 5000)
    },
    
    closeDropdown(event) {
      if (!this.$el.contains(event.target)) {
        this.showExportMenu = false
      }
    }
  }
}
</script>

<style scoped>
.reports-view {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: white;
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
}

.header-section h1 {
  margin: 0;
  font-size: 2.5em;
  background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.action-buttons {
  display: flex;
  gap: 15px;
  align-items: center;
}

.refresh-btn, .export-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.refresh-btn:hover, .export-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

.refresh-btn:disabled {
  background: rgba(255, 255, 255, 0.2);
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  opacity: 0.6;
}

.dropdown-container {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 12px;
  box-shadow: 0 15px 35px rgba(102, 126, 234, 0.2);
  z-index: 1000;
  min-width: 180px;
  overflow: hidden;
  margin-top: 5px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 12px 16px;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.dropdown-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.btn-icon, .item-icon {
  font-size: 16px;
}

.arrow {
  font-size: 12px;
  transition: transform 0.2s ease;
}

.status-message {
  padding: 15px 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  font-weight: 500;
  backdrop-filter: blur(10px);
}

.status-message.success {
  background: rgba(102, 126, 234, 0.2);
  color: #ffffff;
  border: 1px solid rgba(102, 126, 234, 0.4);
}

.status-message.error {
  background: rgba(240, 147, 251, 0.2);
  color: #ffffff;
  border: 1px solid rgba(240, 147, 251, 0.4);
}

.status-message.info {
  background: rgba(79, 172, 254, 0.2);
  color: #ffffff;
  border: 1px solid rgba(79, 172, 254, 0.4);
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.dashboard-grid {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.metrics-section {
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 25px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
}

.metrics-section h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.5em;
  color: white;
  font-weight: 600;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.metric-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 16px;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.metric-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
}

.metric-icon {
  font-size: 2.5em;
  margin-right: 15px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.metric-content h3 {
  margin: 0;
  font-size: 2em;
  font-weight: bold;
}

.metric-content p {
  margin: 5px 0 0 0;
  opacity: 0.9;
  font-size: 0.9em;
}

.chart-section {
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 25px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
}

.chart-section h2 {
  margin-top: 0;
  margin-bottom: 25px;
  font-size: 1.5em;
  color: white;
  font-weight: 600;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 30px;
}

.chart-container {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  padding: 20px;
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chart-container:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
}

.chart-container.full-width {
  grid-column: 1 / -1;
}

.chart-container h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.1em;
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
  font-weight: 600;
}

.chart-wrapper {
  position: relative;
  height: 300px;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-container {
    min-width: unset;
  }
}

@media (max-width: 768px) {
  .reports-view {
    padding: 15px;
  }
  
  .header-section {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .header-section h1 {
    font-size: 2em;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
  
  .metric-card {
    flex-direction: column;
    text-align: center;
  }
  
  .metric-icon {
    margin-right: 0;
    margin-bottom: 10px;
  }
  
  .chart-wrapper {
    height: 250px;
  }
}

@media (max-width: 480px) {
  .action-buttons {
    flex-direction: column;
    width: 100%;
  }
  
  .refresh-btn, .export-btn {
    width: 100%;
    justify-content: center;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-wrapper {
    height: 200px;
  }
}
</style>
