<template>
  <div class="my-reservations">
    <h2>My Reservations</h2>
    
    <div v-if="reservations.length === 0" class="no-reservations">
      <p>You don't have any reservations yet.</p>
      <button @click="$emit('change-tab', 'parking-lots')" class="find-parking-btn">
        Find Parking
      </button>
    </div>

    <div v-else class="reservations-list">
      <div v-for="reservation in reservations" :key="reservation.id" class="reservation-card">
        <div class="reservation-header">
          <h3>{{ reservation.prime_location_name }}</h3>
          <span :class="['status-badge', getStatusClass(reservation.status)]">
            {{ reservation.status }}
          </span>
        </div>
        
        <div class="reservation-details">
          <p><strong>Spot:</strong> {{ reservation.spot_number }}</p>
          <p><strong>Address:</strong> {{ reservation.address }}</p>
          <p><strong>Price:</strong> ${{ reservation.price }}/hour</p>
          <p><strong>Reserved At:</strong> {{ formatDateTime(reservation.created_at) }}</p>
          
          <div v-if="reservation.parking_timestamp" class="parking-details">
            <p><strong>Parked At:</strong> {{ formatDateTime(reservation.parking_timestamp) }}</p>
            <p v-if="reservation.leaving_timestamp">
              <strong>Left At:</strong> {{ formatDateTime(reservation.leaving_timestamp) }}
            </p>
            <p v-if="reservation.parking_cost">
              <strong>Total Cost:</strong> ${{ reservation.parking_cost }}
            </p>
          </div>
        </div>

        <div class="reservation-actions">
          <button 
            v-if="reservation.status === 'active' && !reservation.parking_timestamp"
            @click="parkVehicle(reservation.id)"
            class="action-btn park-btn"
          >
            Park Vehicle
          </button>
          
          <button 
            v-if="reservation.status === 'active' && reservation.parking_timestamp && !reservation.leaving_timestamp"
            @click="releaseSpot(reservation.id)"
            class="action-btn release-btn"
          >
            Release Spot
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const emit = defineEmits(['change-tab', 'refresh']);
const reservations = ref([]);

const loadReservations = async () => {
  try {
    const response = await axios.get('/api/user/my-reservations');
    reservations.value = response.data.reservations;
  } catch (error) {
    console.error('Error loading reservations:', error);
  }
};

const parkVehicle = async (reservationId) => {
  try {
    await axios.post('/api/user/park-vehicle', { reservation_id: reservationId });
    alert('Vehicle parked successfully!');
    loadReservations();
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
    loadReservations();
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

const getStatusClass = (status) => {
  switch (status) {
    case 'active': return 'active';
    case 'completed': return 'completed';
    case 'expired': return 'expired';
    default: return 'default';
  }
};

onMounted(() => {
  loadReservations();
});
</script>

<style scoped>
.my-reservations h2 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.no-reservations {
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

.reservations-list {
  display: grid;
  gap: 1.5rem;
}

.reservation-card {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
}

.reservation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.reservation-header h3 {
  margin: 0;
  color: #2c3e50;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: bold;
}

.status-badge.active {
  background-color: #d4edda;
  color: #155724;
}

.status-badge.completed {
  background-color: #d1ecf1;
  color: #0c5460;
}

.status-badge.expired {
  background-color: #f8d7da;
  color: #721c24;
}

.reservation-details p {
  margin: 0.5rem 0;
  color: #495057;
}

.parking-details {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e9ecef;
}

.reservation-actions {
  margin-top: 1rem;
  display: flex;
  gap: 1rem;
}

.action-btn {
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: background-color 0.3s;
}

.park-btn {
  background-color: #28a745;
  color: white;
}

.park-btn:hover {
  background-color: #218838;
}

.release-btn {
  background-color: #dc3545;
  color: white;
}

.release-btn:hover {
  background-color: #c82333;
}

@media (max-width: 768px) {
  .reservation-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .reservation-actions {
    flex-direction: column;
  }
}
</style>
