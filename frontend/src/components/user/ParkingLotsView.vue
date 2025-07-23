<template>
  <div class="parking-lots-view">
    <h2>Find Parking</h2>
    
    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading parking lots...</p>
    </div>
    
    <!-- Error State -->
    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="loadParkingLots" class="retry-btn">Try Again</button>
    </div>
    
    <!-- No Lots Available -->
    <div v-else-if="parkingLots.length === 0" class="no-lots">
      <div class="no-lots-icon">P</div>
      <h3>No Parking Lots Available</h3>
      <p>No parking lots are currently available. Please check back later.</p>
    </div>
    
    <!-- Parking Lots List -->
    <div v-else class="lots-list">
      <div v-for="lot in parkingLots" :key="lot.id" class="lot-card">
        <div class="lot-header">
          <h3>{{ lot.prime_location_name }}</h3>
          <span class="availability-badge" :class="{ 'available': lot.available_spots > 0, 'full': lot.available_spots === 0 }">
            {{ lot.available_spots > 0 ? 'Available' : 'Full' }}
          </span>
        </div>
        
        <div class="lot-details">
          <p><strong>Address:</strong> {{ lot.address }}</p>
          <p><strong>PIN Code:</strong> {{ lot.pin_code }}</p>
          <p><strong>Price:</strong> ${{ lot.price }}/hour</p>
          <p><strong>Available Spots:</strong> {{ lot.available_spots }} / {{ lot.total_spots }}</p>
        </div>
        
        <div class="lot-actions">
          <button 
            @click="showSpotSelection(lot)" 
            :disabled="lot.available_spots === 0" 
            class="reserve-btn"
          >
            {{ lot.available_spots === 0 ? 'No Spots Available' : 'View & Reserve Spots' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Spot Selection Modal -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Select a Parking Spot</h3>
          <button @click="closeModal" class="close-btn">&times;</button>
        </div>
        
        <div v-if="selectedLot" class="lot-info">
          <h4>{{ selectedLot.prime_location_name }}</h4>
          <p>{{ selectedLot.address }} - ${{ selectedLot.price }}/hour</p>
        </div>
        
        <div v-if="loadingSpots" class="loading-spots">
          <div class="spinner"></div>
          <p>Loading parking spots...</p>
        </div>
        
        <div v-else-if="spotsError" class="error">
          <p>{{ spotsError }}</p>
          <button @click="loadSpots" class="retry-btn">Try Again</button>
        </div>
        
        <div v-else class="spots-grid">
          <div 
            v-for="spot in spots" 
            :key="spot.id"
            :class="[
              'spot-card',
              spot.status === 'A' ? 'available' : 'occupied',
              selectedSpot?.id === spot.id ? 'selected' : ''
            ]"
            @click="selectSpot(spot)"
          >
            <div class="spot-number">{{ spot.spot_number }}</div>
            <div class="spot-status">{{ spot.status_text }}</div>
          </div>
        </div>
        
        <div v-if="selectedSpot" class="selected-spot-info">
          <p><strong>Selected:</strong> Spot #{{ selectedSpot.spot_number }}</p>
        </div>
        
        <div class="modal-actions">
          <button @click="closeModal" class="cancel-btn">Cancel</button>
          <button 
            @click="confirmReservation" 
            :disabled="!selectedSpot || isReserving"
            class="confirm-btn"
          >
            {{ isReserving ? 'Reserving...' : 'Confirm Reservation' }}
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
const loading = ref(false);
const error = ref(null);

// Modal state
const showModal = ref(false);
const selectedLot = ref(null);
const spots = ref([]);
const selectedSpot = ref(null);
const loadingSpots = ref(false);
const spotsError = ref(null);

const loadParkingLots = async () => {
  try {
    loading.value = true;
    error.value = null;
    
    const response = await axios.get('/api/user/parking-lots');
    parkingLots.value = response.data.parking_lots || [];
    
    console.log('Loaded parking lots:', parkingLots.value);
  } catch (err) {
    console.error('Error loading parking lots:', err);
    error.value = 'Failed to load parking lots. Please try again.';
    parkingLots.value = [];
  } finally {
    loading.value = false;
  }
};

const showSpotSelection = async (lot) => {
  selectedLot.value = lot;
  selectedSpot.value = null;
  showModal.value = true;
  await loadSpots();
};

const loadSpots = async () => {
  if (!selectedLot.value) return;
  
  try {
    loadingSpots.value = true;
    spotsError.value = null;
    
    const response = await axios.get(`/api/user/parking-lots/${selectedLot.value.id}/spots`);
    spots.value = response.data.spots || [];
    
    console.log('Loaded spots:', spots.value);
  } catch (err) {
    console.error('Error loading spots:', err);
    spotsError.value = 'Failed to load parking spots. Please try again.';
    spots.value = [];
  } finally {
    loadingSpots.value = false;
  }
};

const selectSpot = (spot) => {
  if (spot.status === 'A') {
    selectedSpot.value = spot;
  }
};

const closeModal = () => {
  showModal.value = false;
  selectedLot.value = null;
  selectedSpot.value = null;
  spots.value = [];
  spotsError.value = null;
};

const confirmReservation = async () => {
  if (!selectedSpot.value) return;
  
  try {
    isReserving.value = true;
    
    const response = await axios.post('/api/user/reserve-spot', { 
      spot_id: selectedSpot.value.id 
    });
    
    if (response.status === 201) {
      alert(`Spot #${selectedSpot.value.spot_number} reserved successfully!`);
      closeModal();
      await loadParkingLots(); // Refresh the lots list
      emit('refresh'); // Notify parent component
    }
  } catch (err) {
    console.error('Error reserving spot:', err);
    
    // Show specific error message if available
    const errorMessage = err.response?.data?.error || 'Failed to reserve spot. Please try again.';
    alert(errorMessage);
  } finally {
    isReserving.value = false;
  }
};

onMounted(() => {
  loadParkingLots();
});
</script>

<style scoped>
.parking-lots-view {
  padding: 1rem;
}

.parking-lots-view h2 {
  margin-bottom: 2rem;
  color: #2c3e50;
  text-align: center;
}

/* Loading State */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
  color: #6c757d;
}

.spinner {
  width: 40px;
  height: 40px;
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

/* Error State */
.error {
  text-align: center;
  padding: 3rem;
  color: #e74c3c;
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

/* No Lots State */
.no-lots {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
}

.no-lots-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  background: #3498db;
  color: white;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  font-weight: bold;
}

.no-lots h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

/* Lots List */
.lots-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.lot-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.lot-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.lot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.lot-header h3 {
  color: white;
  margin: 0;
  font-size: 1.3rem;
  font-weight: bold;
}

.availability-badge {
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.availability-badge.available {
  background-color: #28a745;
  color: white;
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
}

.availability-badge.full {
  background-color: #dc3545;
  color: white;
  box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
}

.lot-details {
  text-align: left;
  margin-bottom: 1.5rem;
}

.lot-details p {
  margin: 0.75rem 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.95rem;
}

.lot-details strong {
  color: white;
  display: inline-block;
  min-width: 120px;
}

.lot-actions {
  text-align: center;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.reserve-btn {
  background: linear-gradient(135deg, #28a745, #20c997);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.reserve-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #218838, #1ba085);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(40, 167, 69, 0.4);
}

.reserve-btn:disabled {
  background: linear-gradient(135deg, #6c757d, #5a6268);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
  opacity: 0.7;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f1f3f4;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.5rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: #7f8c8d;
  cursor: pointer;
  padding: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background-color: #f8f9fa;
  color: #e74c3c;
}

.lot-info {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.lot-info h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
}

.lot-info p {
  margin: 0;
  opacity: 0.9;
}

.loading-spots {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  color: #6c757d;
}

.spots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.spot-card {
  aspect-ratio: 1;
  border: 2px solid transparent;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: bold;
  position: relative;
}

.spot-card.available {
  background: linear-gradient(135deg, #28a745, #20c997);
  color: white;
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.spot-card.available:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(40, 167, 69, 0.4);
  border-color: #155724;
}

.spot-card.occupied {
  background: linear-gradient(135deg, #dc3545, #c82333);
  color: white;
  cursor: not-allowed;
  opacity: 0.7;
}

.spot-card.selected {
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.3);
  transform: scale(1.05);
}

.spot-number {
  font-size: 1.2rem;
  margin-bottom: 0.2rem;
}

.spot-status {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.selected-spot-info {
  background: #e3f2fd;
  border: 1px solid #2196f3;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
  color: #1976d2;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.cancel-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  background: #5a6268;
}

.confirm-btn {
  background: linear-gradient(135deg, #28a745, #20c997);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.confirm-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #218838, #1ba085);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(40, 167, 69, 0.4);
}

.confirm-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
  opacity: 0.7;
}

/* Responsive Design */
@media (max-width: 768px) {
  .parking-lots-view {
    padding: 0.5rem;
  }
  
  .lots-list {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .lot-header {
    flex-direction: column;
    gap: 0.5rem;
    text-align: center;
  }
  
  .lot-card {
    padding: 1rem;
  }
  
  .reserve-btn {
    width: 100%;
    padding: 1rem;
  }
  
  /* Modal responsive */
  .modal-content {
    width: 95%;
    padding: 1.5rem;
    margin: 1rem;
  }
  
  .spots-grid {
    grid-template-columns: repeat(auto-fit, minmax(60px, 1fr));
    gap: 0.5rem;
  }
  
  .spot-card {
    font-size: 0.9rem;
  }
  
  .spot-number {
    font-size: 1rem;
  }
  
  .spot-status {
    font-size: 0.7rem;
  }
  
  .modal-actions {
    flex-direction: column;
  }
  
  .cancel-btn, .confirm-btn {
    width: 100%;
    padding: 1rem;
  }
}

@media (max-width: 480px) {
  .parking-lots-view h2 {
    font-size: 1.5rem;
  }
  
  .lot-header h3 {
    font-size: 1.1rem;
  }
  
  .availability-badge {
    font-size: 0.75rem;
    padding: 0.3rem 0.6rem;
  }
}
</style>

