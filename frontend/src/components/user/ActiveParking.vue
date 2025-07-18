<template>
  <div class="active-parking">
    <h2>Active Parking</h2>
    
    <div v-if="activeReservations.length === 0" class="no-active-parking">
      <p>You don't have any active parking sessions.</p>
      <button @click="$emit('change-tab', 'parking-lots')" class="find-parking-btn">
        Find Parking
      </button>
    </div>

    <div v-else class="active-sessions">
      <div v-for="reservation in activeReservations" :key="reservation.id" class="parking-session">
        <div class="session-header">
          <h3>{{ reservation.prime_location_name }}</h3>
          <div class="timer-display">
            <span class="timer">{{ calculateDuration(reservation.parking_timestamp) }}</span>
            <span class="timer-label">Parking Time</span>
          </div>
        </div>
        
        <div class="session-details">
          <div class="detail-item">
            <strong>Spot Number:</strong> {{ reservation.spot_number }}
          </div>
          <div class="detail-item">
            <strong>Address:</strong> {{ reservation.address }}
          </div>
          <div class="detail-item">
            <strong>Price:</strong> ${{ reservation.price }}/hour
          </div>
          <div class="detail-item">
            <strong>Parked At:</strong> {{ formatDateTime(reservation.parking_timestamp) }}
          </div>
          <div class="detail-item">
            <strong>Estimated Cost:</strong> ${{ calculateEstimatedCost(reservation) }}
          </div>
        </div>

        <div class="session-actions">
          <button 
            v-if="!reservation.parking_timestamp"
            @click="parkVehicle(reservation.id)"
            class="action-btn park-btn"
          >
            🚗 Park Vehicle
          </button>
          
          <button 
            v-if="reservation.parking_timestamp && !reservation.leaving_timestamp"
            @click="releaseSpot(reservation.id)"
            class="action-btn release-btn"
          >
            🚪 Release Spot
          </button>
        </div>
        
        <div class="session-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getProgressWidth(reservation) + '%' }"></div>
          </div>
          <p class="progress-text">{{ getProgressText(reservation) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';

const emit = defineEmits(['change-tab', 'refresh']);
const activeReservations = ref([]);
let intervalId = null;

const loadActiveReservations = async () => {
  try {
    const response = await axios.get('/api/user/my-reservations');
    activeReservations.value = response.data.reservations.filter(r => r.status === 'active');
  } catch (error) {
    console.error('Error loading active reservations:', error);
  }
};

const parkVehicle = async (reservationId) => {
  try {
    await axios.post('/api/user/park-vehicle', { reservation_id: reservationId });
    alert('Vehicle parked successfully!');
    loadActiveReservations();
    emit('refresh');
  } catch (error) {
    console.error('Error parking vehicle:', error);
    alert('Failed to park vehicle.');
  }
};

const releaseSpot = async (reservationId) => {
  try {
    const response = await axios.post('/api/user/release-spot', { reservation_id: reservationId });
    alert(`Spot released successfully! Total cost: $${response.data.parking_cost}`);
    loadActiveReservations();
    emit('refresh');
  } catch (error) {
    console.error('Error releasing spot:', error);
    alert('Failed to release spot.');
  }
};

const formatDateTime = (isoString) => {
  if (!isoString) return 'N/A';
  return new Date(isoString).toLocaleString();
};

const calculateDuration = (startTime) => {
  if (!startTime) return '0:00:00';
  const start = new Date(startTime);
  const now = new Date();
  const diffMs = now - start;
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((diffMs % (1000 * 60)) / 1000);
  return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
};

const calculateEstimatedCost = (reservation) => {
  if (!reservation.parking_timestamp) return '0.00';
  const start = new Date(reservation.parking_timestamp);
  const now = new Date();
  const diffHours = Math.max(1, (now - start) / (1000 * 60 * 60));
  return (diffHours * reservation.price).toFixed(2);
};

const getProgressWidth = (reservation) => {
  if (!reservation.parking_timestamp) return 0;
  const start = new Date(reservation.parking_timestamp);
  const now = new Date();
  const diffHours = (now - start) / (1000 * 60 * 60);
  // Assume 24 hours as max for progress bar
  return Math.min(100, (diffHours / 24) * 100);
};

const getProgressText = (reservation) => {
  if (!reservation.parking_timestamp) return 'Reserved - Click "Park Vehicle" to start';
  return 'Parking in progress...';
};

onMounted(() => {
  loadActiveReservations();
  // Update timer every second
  intervalId = setInterval(() => {
    // Force reactivity update
    activeReservations.value = [...activeReservations.value];
  }, 1000);
});

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId);
  }
});
</script>

<style scoped>
.active-parking h2 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.no-active-parking {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
}

.find-parking-btn {
  background-color: #42b883;
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  margin-top: 1rem;
}

.find-parking-btn:hover {
  background-color: #38a169;
}

.active-sessions {
  display: grid;
  gap: 2rem;
}

.parking-session {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.session-header h3 {
  margin: 0;
  font-size: 1.5rem;
}

.timer-display {
  text-align: right;
}

.timer {
  display: block;
  font-size: 2rem;
  font-weight: bold;
  font-family: 'Courier New', monospace;
}

.timer-label {
  font-size: 0.875rem;
  opacity: 0.8;
}

.session-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.detail-item {
  background-color: rgba(255, 255, 255, 0.1);
  padding: 0.75rem;
  border-radius: 6px;
  backdrop-filter: blur(10px);
}

.session-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.action-btn {
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: bold;
  transition: all 0.3s;
}

.park-btn {
  background-color: #28a745;
  color: white;
}

.park-btn:hover {
  background-color: #218838;
  transform: translateY(-2px);
}

.release-btn {
  background-color: #dc3545;
  color: white;
}

.release-btn:hover {
  background-color: #c82333;
  transform: translateY(-2px);
}

.session-progress {
  margin-top: 1.5rem;
}

.progress-bar {
  background-color: rgba(255, 255, 255, 0.2);
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background-color: #28a745;
  transition: width 0.3s ease;
}

.progress-text {
  margin: 0;
  font-size: 0.875rem;
  opacity: 0.8;
  text-align: center;
}

@media (max-width: 768px) {
  .session-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .timer-display {
    text-align: left;
  }
  
  .session-details {
    grid-template-columns: 1fr;
  }
  
  .session-actions {
    flex-direction: column;
  }
}
</style>
