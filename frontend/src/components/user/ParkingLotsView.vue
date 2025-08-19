<template>
  <div class="parking-lots-view">
    <div class="header-section">
      <h2>Find Parking</h2>
      <div class="search-container">
        <div class="search-input-wrapper">
          <span class="search-icon">🔍</span>
          <input 
            v-model="searchQuery"
            type="text"
            placeholder="Search parking lots by name..."
            class="search-input"
            @input="handleSearch"
          />
          <button 
            v-if="searchQuery"
            @click="clearSearch"
            class="clear-search-btn"
          >
            ×
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="filteredParkingLots.length === 0 && searchQuery" class="no-results">
      <p>No parking lots found matching "{{ searchQuery }}"</p>
      <button @click="clearSearch" class="clear-search-btn-large">
        Clear Search
      </button>
    </div>
    
    <div v-else-if="filteredParkingLots.length === 0" class="no-lots">
      <p>No parking lots available at the moment.</p>
    </div>
    
    <div v-else class="lots-list">
      <div v-for="lot in filteredParkingLots" :key="lot.id" class="lot-card">
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
            @click="openSlotSelection(lot)" 
            :disabled="lot.available_spots === 0" 
            class="reserve-btn"
          >
            {{ lot.available_spots === 0 ? 'No Spots Available' : 'Choose Your Spot' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Slot Selection Modal -->
    <div v-if="showSlotModal" class="modal-overlay" @click="closeSlotModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Choose Your Parking Spot</h3>
          <button @click="closeSlotModal" class="close-btn">×</button>
        </div>
        
        <div class="modal-body">
          <div class="lot-info">
            <h4>{{ selectedLot?.prime_location_name }}</h4>
            <p><strong>Address:</strong> {{ selectedLot?.address }}</p>
            <p><strong>Price:</strong> ${{ selectedLot?.price }}/hour</p>
            
            <div v-if="selectedSlot" class="selection-summary">
              <div class="selected-spot-info">
                <h4>Selected Spot</h4>
                <div class="spot-details">
                  <div class="spot-number-large">#{{ selectedSlot.spot_number }}</div>
                  <div class="spot-location">{{ selectedLot?.prime_location_name }}</div>
                </div>
                <div class="pricing-info">
                  <span class="price">${{ selectedLot?.price }}/hour</span>
                </div>
              </div>
            </div>
          </div>

          <div class="slots-section">
            <div v-if="loadingSlots" class="loading-slots">
              <div class="spinner"></div>
              <p>Loading available spots...</p>
            </div>

            <div v-else-if="availableSlots.length === 0" class="no-slots">
              <p>No available spots found for this location.</p>
            </div>

            <div v-else class="slots-container">
              <h5>Available Spots ({{ availableSlots.length }} available)</h5>
              <div class="slots-grid">
                <div 
                  v-for="slot in availableSlots" 
                  :key="slot.id" 
                  :class="['slot-card', { 'selected': selectedSlot?.id === slot.id }]"
                  @click="selectSlot(slot)"
                >
                  <div class="slot-number">{{ slot.spot_number }}</div>
                  <div class="slot-status">Available</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeSlotModal" class="cancel-btn">
            <span>Cancel</span>
          </button>
          <button 
            @click="confirmReservation" 
            :disabled="!selectedSlot || isReserving"
            class="confirm-btn"
          >
            <span v-if="isReserving" class="btn-content">
              <div class="spinner-small"></div>
              Reserving...
            </span>
            <span v-else class="btn-content">
              <span class="btn-icon">🎯</span>
              Reserve Spot #{{ selectedSlot?.spot_number || '' }}
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- Payment Modal -->
    <div v-if="showPaymentModal" class="modal-overlay" @click="closePaymentModal">
      <div class="payment-modal-content" @click.stop>
        <div class="modal-header">
          <h3>💳 Complete Your Payment</h3>
          <button @click="closePaymentModal" class="close-btn">×</button>
        </div>
        
        <div class="payment-modal-body">
          <div class="booking-summary">
            <h4>🅿️ Booking Summary</h4>
            <div class="summary-details">
              <div class="summary-item">
                <span>Location:</span>
                <span>{{ selectedLot?.prime_location_name }}</span>
              </div>
              <div class="summary-item">
                <span>Spot:</span>
                <span>#{{ selectedSlot?.spot_number }}</span>
              </div>
              <div class="summary-item">
                <span>Rate:</span>
                <span>${{ selectedLot?.price }}/hour</span>
              </div>
              <div class="summary-item total">
                <span>Amount to Pay:</span>
                <span>${{ selectedLot?.price }}</span>
              </div>
            </div>
          </div>

          <div class="payment-methods">
            <h4>💳 Choose Payment Method</h4>
            
            <div class="payment-tabs">
              <button 
                :class="['payment-tab', { 'active': paymentMethod === 'upi' }]" 
                @click="paymentMethod = 'upi'"
              >
                <span class="tab-icon">📱</span>
                UPI Payment
              </button>
              <button 
                :class="['payment-tab', { 'active': paymentMethod === 'card' }]" 
                @click="paymentMethod = 'card'"
              >
                <span class="tab-icon">💳</span>
                Card Payment
              </button>
            </div>

            <!-- UPI Payment Form -->
            <div v-if="paymentMethod === 'upi'" class="payment-form">
              <h5>📱 UPI Payment</h5>
              <div class="form-group">
                <label for="upi-id">UPI ID</label>
                <input 
                  id="upi-id"
                  v-model="paymentDetails.upi.upi_id" 
                  type="text" 
                  placeholder="yourname@paytm" 
                  class="form-input"
                />
                <div class="input-help">Enter your UPI ID (e.g., yourname@paytm, yourname@gpay)</div>
              </div>
            </div>

            <!-- Card Payment Form -->
            <div v-if="paymentMethod === 'card'" class="payment-form">
              <h5>💳 Card Payment</h5>
              
              <div class="form-group">
                <label for="card-number">Card Number</label>
                <input 
                  id="card-number"
                  v-model="paymentDetails.card.card_number" 
                  type="text" 
                  placeholder="1234 5678 9012 3456" 
                  maxlength="19"
                  class="form-input"
                  @input="paymentDetails.card.card_number = formatCardNumber($event.target.value)"
                />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="expiry-month">Expiry Month</label>
                  <select id="expiry-month" v-model="paymentDetails.card.expiry_month" class="form-input">
                    <option value="">MM</option>
                    <option v-for="month in 12" :key="month" :value="month.toString().padStart(2, '0')">
                      {{ month.toString().padStart(2, '0') }}
                    </option>
                  </select>
                </div>
                <div class="form-group">
                  <label for="expiry-year">Expiry Year</label>
                  <select id="expiry-year" v-model="paymentDetails.card.expiry_year" class="form-input">
                    <option value="">YYYY</option>
                    <option v-for="year in 10" :key="year" :value="(new Date().getFullYear() + year - 1).toString()">
                      {{ new Date().getFullYear() + year - 1 }}
                    </option>
                  </select>
                </div>
                <div class="form-group">
                  <label for="cvv">CVV</label>
                  <input 
                    id="cvv"
                    v-model="paymentDetails.card.cvv" 
                    type="text" 
                    placeholder="123" 
                    maxlength="3"
                    class="form-input"
                  />
                </div>
              </div>

              <div class="form-group">
                <label for="cardholder-name">Cardholder Name</label>
                <input 
                  id="cardholder-name"
                  v-model="paymentDetails.card.cardholder_name" 
                  type="text" 
                  placeholder="Name as on card" 
                  class="form-input"
                />
              </div>
            </div>
          </div>
        </div>

        <div class="payment-modal-footer">
          <button @click="closePaymentModal" class="cancel-btn">
            <span>Cancel</span>
          </button>
          <button 
            @click="processPayment" 
            :disabled="isProcessingPayment"
            class="pay-btn"
          >
            <span v-if="isProcessingPayment" class="btn-content">
              <div class="spinner-small"></div>
              Processing...
            </span>
            <span v-else class="btn-content">
              <span class="btn-icon">💳</span>
              Pay ${{ selectedLot?.price }}
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

const emit = defineEmits(['refresh']);
const parkingLots = ref([]);
const searchQuery = ref('');
const isReserving = ref(false);

// Modal state
const showSlotModal = ref(false);
const selectedLot = ref(null);
const availableSlots = ref([]);
const selectedSlot = ref(null);
const loadingSlots = ref(false);

// Computed property for filtered parking lots
const filteredParkingLots = computed(() => {
  if (!searchQuery.value.trim()) {
    return parkingLots.value;
  }
  
  const query = searchQuery.value.toLowerCase().trim();
  return parkingLots.value.filter(lot => 
    lot.prime_location_name.toLowerCase().includes(query) ||
    lot.address.toLowerCase().includes(query)
  );
});

// Search functions
const handleSearch = () => {
  // Search is reactive through computed property
};

const clearSearch = () => {
  searchQuery.value = '';
};

const loadParkingLots = async () => {
  try {
    const response = await axios.get('/api/user/parking-lots');
    parkingLots.value = response.data.parking_lots;
  } catch (error) {
    console.error('Error loading parking lots:', error);
  }
};

const openSlotSelection = async (lot) => {
  selectedLot.value = lot;
  selectedSlot.value = null;
  showSlotModal.value = true;
  await loadAvailableSlots(lot.id);
};

const loadAvailableSlots = async (lotId) => {
  try {
    loadingSlots.value = true;
    const response = await axios.get(`/api/user/parking-lots/${lotId}/slots`);
    availableSlots.value = response.data.available_slots || [];
  } catch (error) {
    console.error('Error loading available slots:', error);
    availableSlots.value = [];
  } finally {
    loadingSlots.value = false;
  }
};

const selectSlot = (slot) => {
  selectedSlot.value = slot;
};

const confirmReservation = async () => {
  if (!selectedSlot.value) return;
  
  try {
    isReserving.value = true;
    await axios.post('/api/user/reserve-specific-spot', { 
      spot_id: selectedSlot.value.id 
    });
    
    alert(`Spot ${selectedSlot.value.spot_number} reserved successfully! You'll pay when you leave.`);
    closeSlotModal();
    await loadParkingLots();
    emit('refresh');
  } catch (error) {
    console.error('Error reserving spot:', error);
    alert('Failed to reserve spot. Please try again.');
  } finally {
    isReserving.value = false;
  }
};

const closeSlotModal = () => {
  showSlotModal.value = false;
  selectedLot.value = null;
  selectedSlot.value = null;
  availableSlots.value = [];
};

onMounted(() => {
  loadParkingLots();
});
</script>

<style scoped>
.parking-lots-view h2 {
  margin-bottom: 2rem;
  color: white;
  font-weight: 600;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  gap: 2rem;
}

.header-section h2 {
  margin: 0;
  color: white;
  font-weight: 600;
  font-size: 2rem;
}

.search-container {
  flex: 0 0 auto;
  min-width: 300px;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  transition: all 0.3s ease;
}

.search-input-wrapper:focus-within {
  border-color: #64b5f6;
  box-shadow: 0 0 0 3px rgba(100, 181, 246, 0.2);
  background: rgba(255, 255, 255, 0.15);
}

.search-icon {
  color: rgba(255, 255, 255, 0.6);
  margin-right: 0.75rem;
  font-size: 1.1rem;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: white;
  font-size: 1rem;
  placeholder-color: rgba(255, 255, 255, 0.5);
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.clear-search-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  transition: all 0.3s ease;
  margin-left: 0.5rem;
}

.clear-search-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: rotate(90deg);
}

.no-results {
  text-align: center;
  padding: 3rem;
  color: rgba(255, 255, 255, 0.8);
}

.no-results p {
  margin-bottom: 1.5rem;
  font-size: 1.1rem;
}

.clear-search-btn-large {
  background: linear-gradient(135deg, #64b5f6 0%, #1976d2 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(100, 181, 246, 0.3);
}

.clear-search-btn-large:hover {
  background: linear-gradient(135deg, #1976d2 0%, #64b5f6 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(100, 181, 246, 0.4);
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
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: white;
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.lot-card:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(100, 181, 246, 0.15);
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
  font-weight: 600;
}

.availability-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: bold;
}

.availability-badge.available {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.2) 0%, rgba(102, 187, 106, 0.15) 100%);
  color: #4CAF50;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.availability-badge.full {
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.2) 0%, rgba(239, 83, 80, 0.15) 100%);
  color: #F44336;
  border: 1px solid rgba(244, 67, 54, 0.3);
}

.lot-details {
  text-align: left;
  margin-bottom: 1.5rem;
}

.lot-details p {
  margin: 0.5rem 0;
  color: rgba(255, 255, 255, 0.8);
}

.lot-actions {
  text-align: center;
}

.reserve-btn {
  background: linear-gradient(135deg, #64b5f6 0%, #1976d2 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 1rem;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 15px rgba(100, 181, 246, 0.2);
}

.reserve-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #1976d2 0%, #64b5f6 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(100, 181, 246, 0.4);
}

.reserve-btn:disabled {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* Modal Styling */
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
  z-index: 9999;
  padding: 6rem 2rem 2rem 2rem;
}

.modal-content {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  width: 95vw;
  max-width: 1200px;
  height: 80vh;
  max-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(100, 181, 246, 0.2);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.modal-header h3 {
  margin: 0;
  color: white;
  font-size: 1.5rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 2rem;
  cursor: pointer;
  transition: color 0.3s ease;
  line-height: 1;
}

.close-btn:hover {
  color: white;
}

.modal-body {
  flex: 1;
  padding: 1.5rem;
  display: flex;
  gap: 2rem;
  overflow: hidden;
}

.lot-info {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  border-radius: 12px;
  flex: 0 0 300px;
  height: fit-content;
}

.slots-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.lot-info h4 {
  margin: 0 0 0.5rem 0;
  color: white;
  font-size: 1.2rem;
  font-weight: 600;
}

.lot-info p {
  margin: 0.25rem 0;
  color: rgba(255, 255, 255, 0.8);
}

.loading-slots {
  text-align: center;
  padding: 2rem;
  color: rgba(255, 255, 255, 0.8);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-top: 4px solid #64b5f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.no-slots {
  text-align: center;
  padding: 2rem;
  color: rgba(255, 255, 255, 0.7);
}

.slots-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.slots-container h5 {
  margin: 0 0 1rem 0;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
  flex-shrink: 0;
}

.slots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  flex: 1;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.slots-grid::-webkit-scrollbar {
  width: 6px;
}

.slots-grid::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.slots-grid::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.slots-grid::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

.slot-card {
  background: rgba(255, 255, 255, 0.08);
  border: 2px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 1rem 1.5rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.slot-card:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(100, 181, 246, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(100, 181, 246, 0.25);
}

.slot-card.selected {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.3) 0%, rgba(102, 187, 106, 0.2) 100%);
  border-color: #4CAF50;
  box-shadow: 0 8px 25px rgba(76, 175, 80, 0.4);
  transform: translateY(-3px);
}

.slot-number {
  font-size: 1.4rem;
  font-weight: bold;
  color: white;
  transition: all 0.3s ease;
}

.slot-card.selected .slot-number {
  color: #4CAF50;
  font-size: 1.5rem;
}

.slot-status {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
}

.slot-card.selected .slot-status {
  color: rgba(76, 175, 80, 0.9);
  font-weight: bold;
}

/* Selection Summary Styles */
.selection-summary {
  margin-top: 1.5rem;
  padding: 1rem;
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(102, 187, 106, 0.05) 100%);
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.selected-spot-info h4 {
  margin: 0 0 1rem 0;
  color: #4CAF50;
  font-size: 1.1rem;
  font-weight: 600;
  text-align: center;
}

.spot-details {
  text-align: center;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.spot-number-large {
  display: block;
  font-size: 1.8rem;
  font-weight: bold;
  color: #4CAF50;
  text-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
  margin-bottom: 0.5rem;
}

.spot-location {
  display: block;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.pricing-info {
  text-align: center;
  padding: 0.5rem;
  background: rgba(76, 175, 80, 0.1);
  border-radius: 6px;
  border: 1px solid rgba(76, 175, 80, 0.2);
}

.price {
  font-size: 1.1rem;
  font-weight: bold;
  color: #4CAF50;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
}

.cancel-btn, .confirm-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
  position: relative;
  overflow: hidden;
}

.cancel-btn {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.cancel-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  transform: translateY(-2px);
}

.confirm-btn {
  background: linear-gradient(135deg, #64b5f6 0%, #1976d2 100%);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 15px rgba(100, 181, 246, 0.2);
  min-width: 200px;
}

.confirm-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #1976d2 0%, #64b5f6 100%);
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(100, 181, 246, 0.4);
}

.confirm-btn:disabled {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-icon {
  font-size: 1.1rem;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
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

  .header-section {
    flex-direction: column;
    gap: 1.5rem;
    align-items: stretch;
  }

  .header-section h2 {
    text-align: center;
    font-size: 1.5rem;
  }

  .search-container {
    min-width: auto;
    width: 100%;
  }

  .search-input-wrapper {
    padding: 0.875rem 1rem;
  }

  .modal-overlay {
    padding: 5rem 1rem 1rem 1rem;
  }

  .modal-content {
    width: 95vw;
    height: 85vh;
    max-height: calc(100vh - 100px);
  }

  .modal-body {
    flex-direction: column;
    gap: 1rem;
  }

  .lot-info {
    flex: none;
    order: 2;
  }

  .slots-section {
    order: 1;
    flex: 1;
  }

  .slots-grid {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  .slot-card {
    min-height: 50px;
    padding: 0.75rem 1rem;
  }

  .modal-footer {
    flex-direction: column;
  }

  .cancel-btn, .confirm-btn {
    width: 100%;
  }

  .selection-summary {
    margin-top: 1rem;
  }
}

/* Payment Modal Styles */
.payment-modal-content {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  width: 90vw;
  max-width: 600px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(100, 181, 246, 0.2);
  overflow: hidden;
}

.payment-modal-body {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}

.booking-summary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 2rem;
}

.booking-summary h4 {
  margin: 0 0 1rem 0;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
}

.summary-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.summary-item:last-child {
  border-bottom: none;
}

.summary-item.total {
  font-weight: bold;
  font-size: 1.1rem;
  color: #4CAF50;
  border-top: 2px solid rgba(76, 175, 80, 0.3);
  padding-top: 1rem;
  margin-top: 0.5rem;
}

.summary-item span:first-child {
  color: rgba(255, 255, 255, 0.8);
}

.summary-item span:last-child {
  color: white;
  font-weight: 500;
}

.payment-methods h4 {
  margin: 0 0 1.5rem 0;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
}

.payment-tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.payment-tab {
  flex: 1;
  background: rgba(255, 255, 255, 0.08);
  border: 2px solid rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.8);
  padding: 1rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.payment-tab:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(100, 181, 246, 0.5);
  transform: translateY(-2px);
}

.payment-tab.active {
  background: linear-gradient(135deg, rgba(100, 181, 246, 0.3) 0%, rgba(25, 118, 210, 0.2) 100%);
  border-color: #64b5f6;
  color: white;
  box-shadow: 0 8px 20px rgba(100, 181, 246, 0.25);
}

.tab-icon {
  font-size: 1.5rem;
}

.payment-form {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  border-radius: 12px;
}

.payment-form h5 {
  margin: 0 0 1.5rem 0;
  color: white;
  font-size: 1rem;
  font-weight: 600;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.form-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.15);
  color: white;
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #64b5f6;
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 0 0 3px rgba(100, 181, 246, 0.2);
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1rem;
}

.input-help {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 0.5rem;
}

.payment-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
}

.pay-btn {
  background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 15px rgba(76, 175, 80, 0.2);
  min-width: 150px;
}

.pay-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #45a049 0%, #4CAF50 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(76, 175, 80, 0.4);
}

.pay-btn:disabled {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

@media (max-width: 768px) {
  .payment-modal-content {
    width: 95vw;
    height: 90vh;
  }

  .payment-tabs {
    flex-direction: column;
  }

  .form-row {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .payment-modal-footer {
    flex-direction: column;
  }

  .cancel-btn, .pay-btn {
    width: 100%;
  }
}
</style>

