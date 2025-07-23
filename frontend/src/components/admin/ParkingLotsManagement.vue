<template>
  <div class="parking-lots-management">
    <h2>Manage Parking Lots</h2>
    <button @click="toggleCreateLotForm" class="create-lot-btn">Create New Lot</button>

    <form v-if="showCreateLotForm" @submit.prevent="createParkingLot">
      <h3>Create New Parking Lot</h3>
      <div>
        <label for="lotName">Lot Name:</label>
        <input type="text" id="lotName" v-model="newLot.name" required />
      </div>
      <div>
        <label for="lotPrice">Price:</label>
        <input type="number" id="lotPrice" v-model="newLot.price" required />
      </div>
      <div>
        <label for="lotAddress">Address:</label>
        <input type="text" id="lotAddress" v-model="newLot.address" required />
      </div>
      <div>
        <label for="lotSpots">Number of Spots:</label>
        <input type="number" id="lotSpots" v-model="newLot.spots" required />
      </div>
      <div>
        <label for="lotPin">Pin Code:</label>
        <input type="text" id="lotPin" v-model="newLot.pin" required />
      </div>
      <button type="submit">Create Lot</button>
      <button type="button" @click="cancelCreate">Cancel</button>
    </form>

    <form v-if="showEditLotForm" @submit.prevent="updateParkingLot">
      <h3>Edit Parking Lot</h3>
      <div>
        <label for="editLotName">Lot Name:</label>
        <input type="text" id="editLotName" v-model="editLotData.name" required />
      </div>
      <div>
        <label for="editLotPrice">Price:</label>
        <input type="number" id="editLotPrice" v-model="editLotData.price" required />
      </div>
      <div>
        <label for="editLotAddress">Address:</label>
        <input type="text" id="editLotAddress" v-model="editLotData.address" required />
      </div>
      <div>
        <label for="editLotSpots">Number of Spots:</label>
        <input type="number" id="editLotSpots" v-model="editLotData.spots" required />
      </div>
      <div>
        <label for="editLotPin">Pin Code:</label>
        <input type="text" id="editLotPin" v-model="editLotData.pin" required />
      </div>
      <button type="submit">Update Lot</button>
      <button type="button" @click="cancelEdit">Cancel</button>
    </form>

    <div class="lots-list">
      <div v-for="lot in parkingLots" :key="lot.id" class="lot-card">
        <h3>{{ lot.prime_location_name }}</h3>
        <p>Price: ${{ lot.price }}</p>
        <p>Address: {{ lot.address }}</p>
        <p>Spots: {{ lot.maximum_number_of_spots }}</p>
        <button @click="editLot(lot)">Edit</button>
        <button @click="deleteLot(lot.id)" :disabled="lot.occupied_spots > 0">Delete</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const emit = defineEmits(['refresh']);

const parkingLots = ref([]);
const showCreateLotForm = ref(false);
const showEditLotForm = ref(false);
const newLot = ref({
  name: '',
  price: 0,
  address: '',
  spots: 0,
  pin: ''
});
const editLotData = ref({
  id: null,
  name: '',
  price: 0,
  address: '',
  spots: 0,
  pin: ''
});

const loadParkingLots = async () => {
  try {
    const response = await axios.get('/api/admin/parking-lots');
    parkingLots.value = response.data.parking_lots;
  } catch (error) {
    console.error('Error loading parking lots:', error);
  }
};

const toggleCreateLotForm = () => {
  showCreateLotForm.value = !showCreateLotForm.value;
};

const createParkingLot = async () => {
  try {
    await axios.post('/api/admin/parking-lots', {
      prime_location_name: newLot.value.name,
      price: newLot.value.price,
      address: newLot.value.address,
      pin_code: newLot.value.pin,
      maximum_number_of_spots: newLot.value.spots
    });
    await loadParkingLots();
    showCreateLotForm.value = false;
    emit('refresh');
    // Reset form
    newLot.value = {
      name: '',
      price: 0,
      address: '',
      spots: 0,
      pin: ''
    };
  } catch (error) {
    console.error('Error creating parking lot:', error);
  }
};

const cancelCreate = () => {
  showCreateLotForm.value = false;
  newLot.value = {
    name: '',
    price: 0,
    address: '',
    spots: 0,
    pin: ''
  };
};

const editLot = (lot) => {
  editLotData.value = {
    id: lot.id,
    name: lot.prime_location_name,
    price: lot.price,
    address: lot.address,
    spots: lot.maximum_number_of_spots,
    pin: lot.pin_code
  };
  showEditLotForm.value = true;
  showCreateLotForm.value = false;
};

const updateParkingLot = async () => {
  try {
    await axios.put(`/api/admin/parking-lots/${editLotData.value.id}`, {
      prime_location_name: editLotData.value.name,
      price: editLotData.value.price,
      address: editLotData.value.address,
      pin_code: editLotData.value.pin,
      maximum_number_of_spots: editLotData.value.spots
    });
    await loadParkingLots();
    showEditLotForm.value = false;
    emit('refresh');
  } catch (error) {
    console.error('Error updating parking lot:', error);
  }
};

const cancelEdit = () => {
  showEditLotForm.value = false;
  editLotData.value = {
    id: null,
    name: '',
    price: 0,
    address: '',
    spots: 0,
    pin: ''
  };
};

const deleteLot = async (id) => {
  if (confirm('Are you sure you want to delete this parking lot?')) {
    try {
      await axios.delete(`/api/admin/parking-lots/${id}`);
      await loadParkingLots();
      emit('refresh');
    } catch (error) {
      console.error('Error deleting parking lot:', error);
      alert('Error deleting parking lot. It may have active reservations.');
    }
  }
};

onMounted(() => {
  loadParkingLots();
});
</script>

<style scoped>
.parking-lots-management {
  margin: 2rem 0;
  color: #2c3e50;
}

.parking-lots-management h2 {
  color: #2c3e50;
  margin-bottom: 1.5rem;
}

.create-lot-btn {
  background-color: #42b883;
  color: white;
  border: none;
  padding: 0.7rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 1rem;
}

.create-lot-btn:hover {
  background-color: #38a169;
}

form {
  margin-bottom: 1.5rem;
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

form div {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #495057;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #ced4da;
  color: #495057;
}

button[type="submit"] {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.7rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 1rem;
  margin-right: 0.5rem;
}

button[type="submit"]:hover {
  background-color: #2980b9;
}

button[type="button"] {
  background-color: #6c757d;
  color: white;
  border: none;
  padding: 0.7rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 1rem;
}

button[type="button"]:hover {
  background-color: #5a6268;
}

form h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
  margin-top: 0;
}

.lots-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.lot-card {
  background-color: white;
  padding: 1rem;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
}

.lot-card h3 {
  margin-top: 0;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.lot-card p {
  color: #6c757d;
  margin-bottom: 0.5rem;
}

.lot-card button {
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-top: 0.5rem;
  margin-right: 0.5rem;
  color: white;
}

.lot-card button:first-of-type {
  background-color: #28a745;
}

.lot-card button:first-of-type:hover {
  background-color: #218838;
}

.lot-card button:last-of-type {
  background-color: #dc3545;
}

.lot-card button:last-of-type:hover:not(:disabled) {
  background-color: #c82333;
}

.lot-card button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
  opacity: 0.6;
}
</style>

