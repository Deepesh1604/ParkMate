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
            @click="showReleasePayment(reservation)"
            class="action-btn release-btn"
          >
            Complete & Pay
          </button>
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
                <span>{{ calculateDuration(selectedReservation.parking_timestamp) }}</span>
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
import { ref, onMounted } from 'vue';
import axios from 'axios';

const emit = defineEmits(['change-tab', 'refresh']);
const reservations = ref([]);

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

const calculateDuration = (parkingTimestamp) => {
  if (!parkingTimestamp) return 'N/A';
  const start = new Date(parkingTimestamp);
  const now = new Date();
  const diffInHours = Math.max(1, (now - start) / (1000 * 60 * 60));
  return `${diffInHours.toFixed(1)} hours`;
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
    loadReservations();
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
  color: white;
  font-weight: 600;
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
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.reservation-card:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(100, 181, 246, 0.15);
}

.reservation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.reservation-header h3 {
  margin: 0;
  color: white;
  font-weight: 600;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: bold;
}

.status-badge.active {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.2) 0%, rgba(102, 187, 106, 0.15) 100%);
  color: #4CAF50;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.status-badge.completed {
  background: linear-gradient(135deg, rgba(100, 181, 246, 0.2) 0%, rgba(25, 118, 210, 0.15) 100%);
  color: #64B5F6;
  border: 1px solid rgba(100, 181, 246, 0.3);
}

.status-badge.expired {
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.2) 0%, rgba(239, 83, 80, 0.15) 100%);
  color: #F44336;
  border: 1px solid rgba(244, 67, 54, 0.3);
}

.reservation-details p {
  margin: 0.5rem 0;
  color: rgba(255, 255, 255, 0.8);
}

.parking-details {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
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

.form-group input {
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

.form-group input:focus {
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

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
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

@media (max-width: 768px) {
  .reservation-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .reservation-actions {
    flex-direction: column;
  }

  .payment-modal-content {
    margin: 1rem;
    width: calc(100% - 2rem);
    padding: 1.5rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .modal-actions {
    flex-direction: column;
  }

  .cancel-btn, .pay-btn {
    width: 100%;
  }
}
</style>
