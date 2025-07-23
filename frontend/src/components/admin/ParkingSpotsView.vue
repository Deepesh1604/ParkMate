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

    <!-- Spots organized by lots -->
    <div v-if="selectedLot" class="lot-section">
      <h3>{{ getLotName(selectedLot) }}</h3>
      <div class="spots-grid">
        <div 
          v-for="spot in parkingSpots" 
          :key="spot.id" 
          :class="['spot-card', getSpotStatusClass(spot)]"
          @click="viewSpotDetails(spot)"
        >
          <div class="spot-number">{{ spot.spot_number }}</div>
          <div class="spot-status">
            {{ getSpotStatusText(spot.status) }}
          </div>
        </div>
      </div>
    </div>

    <!-- All lots with their spots -->
    <div v-else class="all-lots-view">
      <div v-for="lot in spotsGroupedByLot" :key="lot.id" class="lot-section">
        <h3>{{ lot.name }} ({{ lot.spots.length }} spots)</h3>
        <div class="lot-stats">
          <span class="stat available">Available: {{ lot.availableCount }}</span>
          <span class="stat occupied">Occupied: {{ lot.occupiedCount }}</span>
        </div>
        <div class="spots-grid">
          <div 
            v-for="spot in lot.spots" 
            :key="spot.id" 
            :class="['spot-card', getSpotStatusClass(spot)]"
            @click="viewSpotDetails(spot)"
          >
            <div class="spot-number">{{ spot.spot_number }}</div>
            <div class="spot-status">
              {{ getSpotStatusText(spot.status) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Spot Details Modal -->
    <div v-if="selectedSpot" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h3>Spot Details</h3>
        <p><strong>Spot Number:</strong> {{ selectedSpot.spot_number }}</p>
        <p><strong>Lot:</strong> {{ selectedSpot.lot_name }}</p>
        <p><strong>Status:</strong> {{ getSpotStatusText(selectedSpot.status) }}</p>
        
        <div v-if="selectedSpot.status === 'O' && selectedSpot.reservation">
          <h4>Current Reservation</h4>
          <p><strong>User:</strong> {{ selectedSpot.reservation.username }}</p>
          <p><strong>Email:</strong> {{ selectedSpot.reservation.email }}</p>
          <p><strong>Phone:</strong> {{ selectedSpot.reservation.phone }}</p>
          <p><strong>Parked At:</strong> {{ formatDateTime(selectedSpot.reservation.parking_timestamp) }}</p>
          <p><strong>Duration:</strong> {{ calculateDuration(selectedSpot.reservation.parking_timestamp) }}</p>
          <p v-if="selectedSpot.reservation.parking_cost"><strong>Cost:</strong> ${{ selectedSpot.reservation.parking_cost }}</p>
        </div>

        <div class="modal-actions">
          <button @click="closeModal" class="btn-close">Close</button>
          <button v-if="selectedSpot.status === 'O'" @click="freeSpot" class="btn-free">Mark as Free</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

const parkingLots = ref([]);
const parkingSpots = ref([]);
const selectedLot = ref('');
const selectedSpot = ref(null);

const spotsGroupedByLot = computed(() => {
  if (!parkingSpots.value.length) return [];
  
  const grouped = {};
  parkingSpots.value.forEach(spot => {
    if (!grouped[spot.lot_id]) {
      grouped[spot.lot_id] = {
        id: spot.lot_id,
        name: spot.lot_name,
        spots: [],
        availableCount: 0,
        occupiedCount: 0
      };
    }
    grouped[spot.lot_id].spots.push(spot);
    
    if (spot.status === 'O') {
      grouped[spot.lot_id].occupiedCount++;
    } else {
      grouped[spot.lot_id].availableCount++;
    }
  });
  
  return Object.values(grouped);
});

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
    const params = selectedLot.value ? { lot_id: selectedLot.value } : {};
    const response = await axios.get('/api/admin/parking-spots', { params });
    parkingSpots.value = response.data.parking_spots;
  } catch (error) {
    console.error('Error loading parking spots:', error);
  }
};

const getLotName = (lotId) => {
  const lot = parkingLots.value.find(l => l.id == lotId);
  return lot ? lot.prime_location_name : 'Unknown Lot';
};

const getSpotStatusClass = (spot) => {
  return spot.status === 'O' ? 'occupied' : 'available';
};

const getSpotStatusText = (status) => {
  return status === 'O' ? 'Occupied' : 'Available';
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

const freeSpot = async () => {
  if (!selectedSpot.value) return;
  
  if (confirm('Are you sure you want to mark this spot as free?')) {
    try {
      await axios.patch(`/api/admin/parking-spots/${selectedSpot.value.id}/free`);
      await loadParkingSpots();
      selectedSpot.value = null;
    } catch (error) {
      console.error('Error freeing spot:', error);
      alert('Error freeing the spot. Please try again.');
    }
  }
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

.lot-section {
  margin-bottom: 3rem;
  padding: 1.5rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.lot-section h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
  margin-top: 0;
  font-size: 1.3rem;
}

.lot-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 0.5rem;
  background-color: white;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.lot-stats .stat {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
}

.lot-stats .stat.available {
  background-color: #d4edda;
  color: #155724;
}

.lot-stats .stat.occupied {
  background-color: #f8d7da;
  color: #721c24;
}

.all-lots-view {
  margin-top: 1rem;
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
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.spot-card {
  background-color: white;
  border: 2px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.spot-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.spot-card.available {
  border-color: #28a745;
  background-color: #d4edda;
}

.spot-card.occupied {
  border-color: #dc3545;
  background-color: #f8d7da;
}

.spot-number {
  font-size: 1.3rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.spot-status {
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.spot-card.available .spot-status {
  color: #155724;
}

.spot-card.occupied .spot-status {
  color: #721c24;
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
color:#080808ff;
  margin: 0.5rem 0;
}

.modal-content button {
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  margin: 0.25rem;
  transition: background-color 0.3s;
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1.5rem;
  justify-content: flex-end;
}

.btn-close {
  background-color: #6c757d;
  color: white;
}

.btn-close:hover {
  background-color: #5a6268;
}

.btn-free {
  background-color: #28a745;
  color: white;
}

.btn-free:hover {
  background-color: #218838;
}

@media (max-width: 768px) {
  .spots-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 0.5rem;
  }
  
  .spot-card {
    padding: 0.75rem;
    min-height: 70px;
  }
  
  .spot-number {
    font-size: 1.1rem;
  }
  
  .lot-section {
    padding: 1rem;
  }
  
  .lot-stats {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>
