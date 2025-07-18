<template>
  <div class="parking-spots-view">
    <h2>Parking Spots Status</h2>
    
    <!-- Lot Filter -->
    <div class="filter-section">
      <label for="lotFilter">Filter by Parking Lot:</label>
      <select id="lotFilter" v-model="selectedLot" @change="loadParkingSpots">
        <option value="">All Lots</option>
        <option v-for="lot in parkingLots" :key="lot.id" :value="lot.id">
          {{ lot.prime_location_name }}
        </option>
      </select>
    </div>

    <!-- Spots Grid -->
    <div class="spots-grid">
      <div 
        v-for="spot in parkingSpots" 
        :key="spot.id" 
        :class="['spot-card', spot.status === 'O' ? 'occupied' : 'available']"
        @click="viewSpotDetails(spot)"
      >
        <div class="spot-number">{{ spot.spot_number }}</div>
        <div class="spot-status">
          {{ spot.status === 'O' ? 'Occupied' : 'Available' }}
        </div>
        <div class="lot-name">{{ spot.lot_name }}</div>
      </div>
    </div>

    <!-- Spot Details Modal -->
    <div v-if="selectedSpot" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h3>Spot Details</h3>
        <p><strong>Spot Number:</strong> {{ selectedSpot.spot_number }}</p>
        <p><strong>Lot:</strong> {{ selectedSpot.lot_name }}</p>
        <p><strong>Status:</strong> {{ selectedSpot.status === 'O' ? 'Occupied' : 'Available' }}</p>
        
        <div v-if="selectedSpot.status === 'O' && selectedSpot.reservation">
          <h4>Vehicle Details</h4>
          <p><strong>User:</strong> {{ selectedSpot.reservation.username }}</p>
          <p><strong>Email:</strong> {{ selectedSpot.reservation.email }}</p>
          <p><strong>Phone:</strong> {{ selectedSpot.reservation.phone }}</p>
          <p><strong>Parked At:</strong> {{ formatDateTime(selectedSpot.reservation.parking_timestamp) }}</p>
          <p><strong>Duration:</strong> {{ calculateDuration(selectedSpot.reservation.parking_timestamp) }}</p>
        </div>

        <button @click="closeModal">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const parkingLots = ref([]);
const parkingSpots = ref([]);
const selectedLot = ref('');
const selectedSpot = ref(null);

const loadParkingLots = async () => {
  try {
    const response = await axios.get('/api/admin/parking-lots');
    parkingLots.value = response.data.parking_lots;
  } catch (error) {
    console.error('Error loading parking lots:', error);
  }
};

const loadParkingSpots = async () => {
  try {
    // This would need to be implemented in your backend
    // For now, we'll create a mock endpoint or use existing data
    const spotsResponse = await axios.get('/api/admin/parking-spots', {
      params: { lot_id: selectedLot.value }
    });
    parkingSpots.value = spotsResponse.data.parking_spots;
  } catch (error) {
    console.error('Error loading parking spots:', error);
    // Mock data for demonstration
    generateMockSpots();
  }
};

const generateMockSpots = () => {
  const spots = [];
  parkingLots.value.forEach(lot => {
    for (let i = 1; i <= lot.maximum_number_of_spots; i++) {
      spots.push({
        id: `${lot.id}-${i}`,
        spot_number: i,
        lot_name: lot.prime_location_name,
        status: Math.random() > 0.7 ? 'O' : 'A',
        reservation: Math.random() > 0.7 ? {
          username: 'user' + i,
          email: `user${i}@example.com`,
          phone: `+1234567890`,
          parking_timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString()
        } : null
      });
    }
  });
  
  if (selectedLot.value) {
    parkingSpots.value = spots.filter(spot => 
      parkingLots.value.find(lot => lot.id == selectedLot.value)?.prime_location_name === spot.lot_name
    );
  } else {
    parkingSpots.value = spots;
  }
};

const viewSpotDetails = (spot) => {
  selectedSpot.value = spot;
};

const closeModal = () => {
  selectedSpot.value = null;
};

const formatDateTime = (isoString) => {
  if (!isoString) return 'N/A';
  return new Date(isoString).toLocaleString();
};

const calculateDuration = (startTime) => {
  if (!startTime) return 'N/A';
  const start = new Date(startTime);
  const now = new Date();
  const diffMs = now - start;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  return `${diffHours}h ${diffMinutes}m`;
};

onMounted(() => {
  loadParkingLots().then(() => {
    loadParkingSpots();
  });
});
</script>

<style scoped>
.parking-spots-view h2 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.filter-section {
  margin-bottom: 2rem;
}

.filter-section label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
  color: #2c3e50;
}

.filter-section select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  min-width: 200px;
}

.spots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 1rem;
}

.spot-card {
  background-color: white;
  border: 2px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.spot-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.spot-card.available {
  border-color: #42b883;
  background-color: #f0f9ff;
}

.spot-card.occupied {
  border-color: #e74c3c;
  background-color: #fef2f2;
}

.spot-number {
  font-size: 1.5rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.spot-status {
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.spot-card.available .spot-status {
  color: #42b883;
}

.spot-card.occupied .spot-status {
  color: #e74c3c;
}

.lot-name {
  font-size: 0.8rem;
  color: #7f8c8d;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content h3 {
  margin-top: 0;
  color: #2c3e50;
}

.modal-content h4 {
  margin-top: 1.5rem;
  color: #2c3e50;
}

.modal-content p {
  margin: 0.5rem 0;
}

.modal-content button {
  background-color: #42b883;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 1rem;
}

.modal-content button:hover {
  background-color: #38a169;
}

@media (max-width: 768px) {
  .spots-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 0.5rem;
  }
  
  .spot-card {
    padding: 0.75rem;
  }
  
  .spot-number {
    font-size: 1.2rem;
  }
}
</style>
