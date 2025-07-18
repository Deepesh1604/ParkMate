<template>
  <div class="reports-view">
    <h2>Reports</h2>
    
    <div class="buttons-section">
      <button @click="generateDailyReport" class="report-btn">Generate Daily Report</button>
      <button @click="generateWeeklyReport" class="report-btn">Generate Weekly Report</button>
    </div>
    
    <div v-if="report" class="report-content">
      <h3>Report for {{ report.date }}</h3>
      <p><strong>Total Reservations:</strong> {{ report.daily_summary?.total_reservations || 0 }}</p>
      <p><strong>Completed Reservations:</strong> {{ report.daily_summary?.completed_reservations || 0 }}</p>
      <p><strong>Active Reservations:</strong> {{ report.daily_summary?.active_reservations || 0 }}</p>
      <p><strong>Expired Reservations:</strong> {{ report.daily_summary?.expired_reservations || 0 }}</p>
      <p><strong>Total Revenue:</strong> ${{ report.daily_summary?.total_revenue || 0 }}</p>
    </div>

    <div class="lot-report-section">
      <h3>Lot-wise Statistics</h3>
      <div class="lot-report" v-for="lot in report.lot_statistics || []" :key="lot.prime_location_name">
        <h4>{{ lot.prime_location_name }}</h4>
        <p>Reservations: {{ lot.reservations_count }}</p>
        <p>Revenue: ${{ lot.revenue }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <p>Loading report...</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const report = ref(null);
const loading = ref(false);

const generateDailyReport = async () => {
  try {
    loading.value = true;
    const response = await axios.get('/api/admin/reports/daily/' + getTodayDate());
    report.value = response.data;
  } catch (error) {
    console.error('Error generating daily report:', error);
  } finally {
    loading.value = false;
  }
};

const generateWeeklyReport = () => {
  // Implement the logic for weekly report
  console.log('Generating weekly report...');
};

const getTodayDate = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};
</script>

<style scoped>
.reports-view {
  margin: 2rem 0;
}

.buttons-section {
  margin-bottom: 1.5rem;
}

.report-btn {
  background-color: #42b883;
  color: white;
  border: none;
  padding: 0.7rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-right: 1rem;
}

.report-btn:hover {
  background-color: #38a169;
}

.report-content {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.report-content h3 {
  margin: 0 0 1rem;
}

.lot-report-section {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.lot-report {
  padding: 1rem 0;
  border-bottom: 1px solid #ddd;
}

.lot-report:last-child {
  border-bottom: none;
}

.loading {
  color: #7f8c8d;
  font-style: italic;
}
</style>

