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
            @click="showReleasePayment(reservation)"
            class="action-btn release-btn"
          >
            🚪 Complete & Pay
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

    <!-- Payment Modal for Release -->
    <div v-if="showPaymentModal" class="modal-overlay" @click="closePaymentModal">
      <div class="payment-modal-content" @click.stop>
        <div class="modal-header">
          <h3>💳 Complete Payment & Release Spot</h3>
          <button @click="closePaymentModal" class="close-btn">×</button>
        </div>
        
        <div class="payment-modal-body">
          <div class="session-summary" v-if="selectedReservation">
            <h4>🅿️ Parking Session Summary</h4>
            <div class="summary-details">
              <div class="summary-item">
                <span>Location:</span>
                <span>{{ selectedReservation.prime_location_name }}</span>
              </div>
              <div class="summary-item">
                <span>Spot:</span>
                <span>#{{ selectedReservation.spot_number }}</span>
              </div>
              <div class="summary-item">
                <span>Parked At:</span>
                <span>{{ formatDateTime(selectedReservation.parking_timestamp) }}</span>
              </div>
              <div class="summary-item">
                <span>Duration:</span>
                <span>{{ calculateDurationForPayment(selectedReservation.parking_timestamp) }}</span>
              </div>
              <div class="summary-item">
                <span>Rate:</span>
                <span>${{ selectedReservation.price }}/hour</span>
              </div>
              <div class="summary-item total">
                <span>Total Amount:</span>
                <span>${{ calculateAmount(selectedReservation.parking_timestamp, selectedReservation.price) }}</span>
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
            @click="processPaymentAndRelease" 
            :disabled="isProcessingPayment"
            class="pay-btn"
          >
            <span v-if="isProcessingPayment" class="btn-content">
              <div class="spinner-small"></div>
              Processing...
            </span>
            <span v-else class="btn-content">
              <span class="btn-icon">💳</span>
              Pay ${{ selectedReservation ? calculateAmount(selectedReservation.parking_timestamp, selectedReservation.price) : '0.00' }}
            </span>
          </button>
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

// Payment Modal State
const showPaymentModal = ref(false);
const selectedReservation = ref(null);
const paymentMethod = ref('upi');
const paymentDetails = ref({
  upi: { upi_id: '' },
  card: {
    card_number: '',
    expiry_month: '',
    expiry_year: '',
    cvv: '',
    cardholder_name: ''
  }
});
const isProcessingPayment = ref(false);

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

const showReleasePayment = (reservation) => {
  selectedReservation.value = reservation;
  showPaymentModal.value = true;
};

const closePaymentModal = () => {
  showPaymentModal.value = false;
  selectedReservation.value = null;
  paymentMethod.value = 'upi';
  paymentDetails.value = {
    upi: { upi_id: '' },
    card: {
      card_number: '',
      expiry_month: '',
      expiry_year: '',
      cvv: '',
      cardholder_name: ''
    }
  };
};

const formatCardNumber = (value) => {
  const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
  const matches = v.match(/\d{4,16}/g);
  const match = matches && matches[0] || '';
  const parts = [];
  for (let i = 0, len = match.length; i < len; i += 4) {
    parts.push(match.substring(i, i + 4));
  }
  if (parts.length) {
    return parts.join(' ');
  } else {
    return v;
  }
};

const calculateAmount = (parkingTimestamp, pricePerHour) => {
  if (!parkingTimestamp) return '0.00';
  const start = new Date(parkingTimestamp);
  const now = new Date();
  const diffInHours = Math.max(1, (now - start) / (1000 * 60 * 60));
  return (diffInHours * pricePerHour).toFixed(2);
};

const processPaymentAndRelease = async () => {
  if (!selectedReservation.value) return;
  
  try {
    isProcessingPayment.value = true;
    
    const paymentData = {
      reservation_id: selectedReservation.value.id,
      payment_method: paymentMethod.value,
      payment_details: paymentMethod.value === 'upi' 
        ? paymentDetails.value.upi 
        : paymentDetails.value.card
    };
    
    const response = await axios.post('/api/user/release-spot', paymentData);
    
    alert(`Payment successful! Total cost: $${response.data.parking_cost}. Spot released successfully!`);
    closePaymentModal();
    loadActiveReservations();
    emit('refresh');
  } catch (error) {
    console.error('Error processing payment and releasing spot:', error);
    const errorMessage = error.response?.data?.error || 'Payment failed. Please try again.';
    alert(errorMessage);
  } finally {
    isProcessingPayment.value = false;
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

const calculateDurationForPayment = (parkingTimestamp) => {
  if (!parkingTimestamp) return 'N/A';
  const start = new Date(parkingTimestamp);
  const now = new Date();
  const diffInHours = Math.max(1, (now - start) / (1000 * 60 * 60));
  return `${diffInHours.toFixed(1)} hours`;
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
  color: white;
  font-weight: 600;
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
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.parking-session:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(100, 181, 246, 0.15);
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
  font-weight: 600;
  color: white;
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
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.75rem;
  border-radius: 8px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.detail-item:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
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
  background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.park-btn:hover {
  background: linear-gradient(135deg, #45a049 0%, #4CAF50 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
}

.release-btn {
  background: linear-gradient(135deg, #F44336 0%, #d32f2f 100%);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.release-btn:hover {
  background: linear-gradient(135deg, #d32f2f 0%, #F44336 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(244, 67, 54, 0.3);
}

.session-progress {
  margin-top: 1.5rem;
}

.progress-bar {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.05);
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
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

/* Payment Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(10px);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 2rem;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
  overflow-y: auto;
}

.payment-modal-content {
  background: rgba(26, 32, 44, 0.95);
  backdrop-filter: blur(30px);
  border-radius: 24px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  padding: 2rem;
  width: 90%;
  max-width: 500px;
  max-height: calc(100vh - 4rem);
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  animation: slideDown 0.3s ease;
  position: relative;
  margin-bottom: 2rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.modal-header h3 {
  margin: 0;
  color: #ffffff;
  font-size: 1.5rem;
  font-weight: 700;
}

.close-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  font-size: 1.5rem;
  width: 35px;
  height: 35px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: rotate(90deg);
}

.session-summary {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.session-summary h4 {
  margin: 0 0 1rem 0;
  color: #ffffff;
  font-size: 1.1rem;
  font-weight: 600;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  color: rgba(255, 255, 255, 0.9);
}

.summary-item.total {
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding-top: 0.75rem;
  margin-top: 0.75rem;
  font-weight: 600;
  color: #ffffff;
  font-size: 1.1rem;
}

.payment-methods {
  margin-bottom: 1.5rem;
}

.payment-methods h4 {
  margin: 0 0 1rem 0;
  color: #ffffff;
  font-size: 1.1rem;
  font-weight: 600;
}

.payment-tabs {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.payment-tab {
  flex: 1;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
  font-weight: 600;
}

.payment-tab.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.payment-form {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.payment-form h5 {
  margin: 0 0 1rem 0;
  color: #ffffff;
  font-size: 1rem;
  font-weight: 600;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.form-group input, .form-group select {
  width: 100%;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  color: white;
  font-size: 1rem;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.form-group input:focus, .form-group select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
  background: rgba(255, 255, 255, 0.15);
}

.form-group input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.75rem;
}

.input-help {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 0.25rem;
}

.payment-modal-footer {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.cancel-btn, .pay-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 100px;
}

.cancel-btn {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.cancel-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.pay-btn {
  background: linear-gradient(135deg, #4CAF50, #45a049);
  color: white;
  box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
}

.pay-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
}

.pay-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
