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
  color: white;
}

.parking-lots-management h2 {
  color: white;
  background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1.5rem;
  font-weight: 600;
}

.create-lot-btn {
  background: linear-gradient(135deg, #6f80cfff 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  cursor: pointer;
  margin-bottom: 1rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
  font-weight: 500;
}

.create-lot-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

form {
  margin-bottom: 1.5rem;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.1);
}

form div {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

input {
  width: 100%;
  padding: 0.75rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  color: white;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

input:focus {
  outline: none;
  border-color: rgba(102, 126, 234, 0.6);
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

button[type="submit"] {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 1rem;
  margin-right: 0.5rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
  font-weight: 500;
}

button[type="submit"]:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

button[type="button"] {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 1rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
}

button[type="button"]:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

form h3 {
  color: white;
  margin-bottom: 1rem;
  margin-top: 0;
  font-weight: 600;
}

.lots-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.lot-card {
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.lot-card:hover {
  transform: translateY(-5px);
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 15px 40px rgba(102, 126, 234, 0.2);
}

.lot-card h3 {
  margin-top: 0;
  color: white;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.lot-card p {
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.lot-card button {
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-top: 0.5rem;
  margin-right: 0.5rem;
  color: white;
  font-weight: 500;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.lot-card button:first-of-type {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.lot-card button:first-of-type:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.lot-card button:last-of-type {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.lot-card button:last-of-type:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(240, 147, 251, 0.3);
}

.lot-card button:disabled {
  background: rgba(255, 255, 255, 0.2);
  cursor: not-allowed;
  opacity: 0.6;
  transform: none;
}

@media (max-width: 768px) {
  .lots-list {
    grid-template-columns: 1fr;
  }
  
  form {
    padding: 1rem;
  }
}
</style>

