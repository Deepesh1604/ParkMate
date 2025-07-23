<template>
  <div class="parking-lots-view">
    <h2>Find Parking</h2>
    
    <div v-if="parkingLots.length === 0" class="no-lots">
      <p>No parking lots available at the moment.</p>
    </div>
    
    <div v-else class="lots-list">
      <div v-for="lot in parkingLots" :key="lot.id" class="lot-card">
        <div class="lot-header">
          <h3>{{ lot.prime_location_name }}</h3>
          <span class="availability-badge" :class="{ 'available': lot.available_spots > 0, 'full': lot.available_spots === 0 }">
            {{ lot.available_spots > 0 ? 'Available' : 'Full' }}
          </span>
        </div>
        
        <div class="lot-details">
          <p><strong>📍 Address:</strong> {{ lot.address }}</p>
          <p><strong>💰 Price:</strong> ${{ lot.price }}/hour</p>
          <p><strong>🅿️ Available Spots:</strong> {{ lot.available_spots }} / {{ lot.total_spots }}</p>
        </div>
        
        <div class="lot-actions">
          <button 
            @click="reserveSpot(lot.id)" 
            :disabled="lot.available_spots === 0 || isReserving" 
            class="reserve-btn"
          >
            {{ isReserving ? 'Reserving...' : 'Reserve Spot' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const emit = defineEmits(['refresh']);
const parkingLots = ref([]);
const isReserving = ref(false);

const loadParkingLots = async () => {
  try {
    const response = await axios.get('/api/user/parking-lots');
    parkingLots.value = response.data.parking_lots;
  } catch (error) {
    console.error('Error loading parking lots:', error);
  }
};

const reserveSpot = async (lotId) => {
  try {
    isReserving.value = true;
    const response = await axios.post('/api/user/reserve-spot', { lot_id: lotId });
    alert('Spot reserved successfully!');
    await loadParkingLots();
    emit('refresh');
  } catch (error) {
    console.error('Error reserving spot:', error);
    alert('Failed to reserve spot.');
  } finally {
    isReserving.value = false;
  }
};

onMounted(() => {
  loadParkingLots();
});
</script>

<style scoped>
.parking-lots-view h2 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.no-lots {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
}

.lots-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
}

.lot-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
}

.lot-card:hover {
  transform: translateY(-2px);
}

.lot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.lot-header h3 {
  color: white;
  margin: 0;
  font-size: 1.2rem;
}

.availability-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: bold;
}

.availability-badge.available {
  background-color: #28a745;
  color: white;
}

.availability-badge.full {
  background-color: #dc3545;
  color: white;
}

.lot-details {
  text-align: left;
  margin-bottom: 1.5rem;
}

.lot-details p {
  margin: 0.5rem 0;
  color: rgba(255, 255, 255, 0.9);
}

.lot-actions {
  text-align: center;
}

.reserve-btn {
  background-color: #28a745;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 1rem;
  font-weight: bold;
}

.reserve-btn:hover:not(:disabled) {
  background-color: #218838;
  transform: translateY(-1px);
}

.reserve-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 768px) {
  .lots-list {
    grid-template-columns: 1fr;
  }
  
  .lot-header {
    flex-direction: column;
    gap: 0.5rem;
    text-align: center;
  }
}
</style>

