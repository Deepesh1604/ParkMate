<template>
  <div class="parking-lots-management">
    <h2>Manage Parking Lots</h2>
    <button @click="toggleCreateLotForm" class="create-lot-btn">Create New Lot</button>

    <form v-if="showCreateLotForm" @submit.prevent="createParkingLot">
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
const newLot = ref({
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
    const response = await axios.post('/api/admin/parking-lots', {
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

const editLot = (lot) => {
  // Implement edit functionality (e.g., opening a form with the lot data)
  console.log('Edit lot:', lot);
};

const deleteLot = async (id) => {
  try {
    await axios.delete(`/api/admin/parking-lots/${id}`);
    parkingLots.value = parkingLots.value.filter(lot => lot.id !== id);
  } catch (error) {
    console.error('Error deleting parking lot:', error);
  }
};

onMounted(() => {
  loadParkingLots();
});
</script>

<style scoped>
.parking-lots-management {
  margin: 2rem 0;
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
}

form div {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
}

input {
  width: 100%;
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #ccc;
}

button[type="submit"] {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.7rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 1rem;
}

button[type="submit"]:hover {
  background-color: #2980b9;
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
}

.lot-card h3 {
  margin-top: 0;
}

.lot-card button {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-top: 0.5rem;
}

.lot-card button:hover {
  background-color: #c0392b;
}
</style>

