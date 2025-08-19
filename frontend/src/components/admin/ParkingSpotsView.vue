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
  color: white;
  background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 600;
}

.lot-section {
  margin-bottom: 3rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.lot-section:hover {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 15px 40px rgba(102, 126, 234, 0.2);
}

.lot-section h3 {
  color: white;
  margin-bottom: 1rem;
  margin-top: 0;
  font-size: 1.3rem;
  font-weight: 600;
}

.lot-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.lot-stats .stat {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  backdrop-filter: blur(10px);
}

.lot-stats .stat.available {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.3) 0%, rgba(102, 187, 106, 0.2) 100%);
  color: #ffffff;
  border: 1px solid rgba(76, 175, 80, 0.5);
}

.lot-stats .stat.occupied {
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.3) 0%, rgba(197, 37, 34, 0.2) 100%);
  color: #ffffff;
  border: 1px solid rgba(244, 67, 54, 0.5);
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
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.filter-section select {
  padding: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  min-width: 200px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  color: white;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.filter-section select:focus {
  outline: none;
  border-color: rgba(102, 126, 234, 0.6);
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.filter-section select option {
  background: #667eea;
  color: white;
}

.spots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.spot-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(15px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 1rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.08);
}

.spot-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(102, 126, 234, 0.2);
}

.spot-card.available {
  border-color: rgba(76, 175, 80, 0.5);
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.2) 0%, rgba(102, 187, 106, 0.15) 100%);
  box-shadow: 0 4px 20px rgba(76, 175, 80, 0.12);
}

.spot-card.available:hover {
  border-color: rgba(76, 175, 80, 0.7);
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.3) 0%, rgba(102, 187, 106, 0.25) 100%);
  box-shadow: 0 15px 35px rgba(76, 175, 80, 0.25);
}

.spot-card.occupied {
  border-color: rgba(244, 67, 54, 0.5);
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.2) 0%, rgba(239, 83, 80, 0.15) 100%);
  box-shadow: 0 4px 20px rgba(244, 67, 54, 0.12);
}

.spot-card.occupied:hover {
  border-color: rgba(244, 67, 54, 0.7);
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.3) 0%, rgba(239, 83, 80, 0.25) 100%);
  box-shadow: 0 15px 35px rgba(244, 67, 54, 0.25);
}

.spot-number {
  font-size: 1.3rem;
  font-weight: bold;
  color: white;
  margin-bottom: 0.25rem;
  text-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
}

.spot-status {
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255, 255, 255, 0.9);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  padding: 2rem;
  border-radius: 16px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(102, 126, 234, 0.2);
}

.modal-content h3 {
  margin-top: 0;
  color: white;
  font-weight: 600;
}

.modal-content h4 {
  margin-top: 1.5rem;
  color: white;
  font-weight: 600;
}

.modal-content p {
  color: rgba(255, 255, 255, 0.9);
  margin: 0.5rem 0;
  font-weight: 500;
}

.modal-content button {
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  margin: 0.25rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1.5rem;
  justify-content: flex-end;
}

.btn-close {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.btn-close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.btn-free {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-free:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
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
  
  .modal-content {
    padding: 1.5rem;
  }
}
</style>
