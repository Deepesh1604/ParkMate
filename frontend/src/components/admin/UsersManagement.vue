<template>
  <div class="users-management">
    <h2>Registered Users</h2>
    
    <div class="users-stats">
      <div class="stat-card">
        <h3>{{ users.length }}</h3>
        <p>Total Users</p>
      </div>
      <div class="stat-card">
        <h3>{{ activeUsers }}</h3>
        <p>Active Users</p>
      </div>
      <div class="stat-card">
        <h3>{{ newUsersThisMonth }}</h3>
        <p>New This Month</p>
      </div>
    </div>

    <div class="search-section">
      <input 
        type="text" 
        v-model="searchQuery" 
        placeholder="Search users by name or email..."
        class="search-input"
      />
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading users from database...</p>
    </div>
    
    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
      <button @click="loadUsers" class="btn-retry">Retry</button>
    </div>
    
    <!-- Empty State -->
    <div v-else-if="users.length === 0" class="empty-state">
      <div class="empty-icon">👥</div>
      <h3>No Registered Users</h3>
      <p>No users have registered yet. When users register, they will appear here.</p>
    </div>
    
    <!-- Users Table -->
    <div v-else class="users-table">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Username</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Registration Date</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.phone || 'N/A' }}</td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>
              <span :class="['status-badge', getStatusClass(user)]">
                {{ getUserStatus(user) }}
              </span>
            </td>
            <td>
              <div class="action-buttons">
                <button @click="viewUserDetails(user)" class="btn-view">View</button>
                <button @click="confirmDeleteUser(user)" class="btn-delete">Delete</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- No search results -->
      <div v-if="filteredUsers.length === 0 && searchQuery" class="no-results">
        <p>No users found matching "{{ searchQuery }}"</p>
      </div>
    </div>

    <!-- User Details Modal -->
    <div v-if="selectedUser" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h3>User Details</h3>
        <div class="user-info">
          <p><strong>ID:</strong> {{ selectedUser.id }}</p>
          <p><strong>Username:</strong> {{ selectedUser.username }}</p>
          <p><strong>Email:</strong> {{ selectedUser.email }}</p>
          <p><strong>Phone:</strong> {{ selectedUser.phone || 'N/A' }}</p>
          <p><strong>Registration Date:</strong> {{ formatDate(selectedUser.created_at) }}</p>
        </div>

        <div class="user-stats">
          <h4>User Activity</h4>
          <div class="activity-stats">
            <div class="activity-item">
              <span class="activity-label">Total Reservations:</span>
              <span class="activity-value">{{ selectedUser.total_reservations || 0 }}</span>
            </div>
            <div class="activity-item">
              <span class="activity-label">Active Reservations:</span>
              <span class="activity-value">{{ selectedUser.active_reservations || 0 }}</span>
            </div>
            <div class="activity-item">
              <span class="activity-label">Total Spent:</span>
              <span class="activity-value">${{ selectedUser.total_spent || 0 }}</span>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button @click="closeModal" class="btn-close">Close</button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="userToDelete" class="modal-overlay" @click="cancelDelete">
      <div class="modal-content" @click.stop>
        <h3>Confirm User Deletion</h3>
        <div class="warning-message">
          <div class="warning-icon">⚠️</div>
          <p>Are you sure you want to delete user <strong>"{{ userToDelete.username }}"</strong>?</p>
          <p class="warning-text">This action will permanently remove:</p>
          <ul class="warning-list">
            <li>The user account</li>
            <li>All reservation history ({{ userToDelete.total_reservations || 0 }} reservations)</li>
            <li>All associated data</li>
          </ul>
          <p class="warning-text"><strong>This action cannot be undone!</strong></p>
        </div>

        <div class="modal-actions">
          <button @click="cancelDelete" class="btn-cancel">Cancel</button>
          <button @click="deleteUser" class="btn-confirm-delete" :disabled="deleteLoading">
            <span v-if="deleteLoading">Deleting...</span>
            <span v-else>Delete User</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const users = ref([]);
const searchQuery = ref('');
const selectedUser = ref(null);
const userToDelete = ref(null);
const loading = ref(false);
const deleteLoading = ref(false);
const error = ref(null);

const loadUsers = async () => {
  try {
    loading.value = true;
    error.value = null;
    
    // Fetch only real users from the database
    const response = await axios.get('/api/admin/users');
    
    // Ensure we only get legitimate registered users (not demo/test users)
    users.value = response.data.users || response.data || [];
    
    // Filter out any potential demo users if they exist
    users.value = users.value.filter(user => 
      user.username && 
      user.email && 
      !user.username.startsWith('demo') && 
      !user.username.startsWith('test') &&
      !user.email.includes('demo') &&
      !user.email.includes('test')
    );
    
  } catch (error) {
    console.error('Error loading users:', error);
    error.value = 'Failed to load users. Please check your connection and try again.';
    users.value = []; // Show empty list instead of mock data
  } finally {
    loading.value = false;
  }
};

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value;
  
  const query = searchQuery.value.toLowerCase();
  return users.value.filter(user => 
    user.username.toLowerCase().includes(query) || 
    user.email.toLowerCase().includes(query)
  );
});

const activeUsers = computed(() => {
  return users.value.filter(user => user.active_reservations > 0).length;
});

const newUsersThisMonth = computed(() => {
  const thisMonth = new Date();
  thisMonth.setDate(1);
  return users.value.filter(user => new Date(user.created_at) >= thisMonth).length;
});

const viewUserDetails = (user) => {
  selectedUser.value = user;
};

const closeModal = () => {
  selectedUser.value = null;
};

const confirmDeleteUser = (user) => {
  userToDelete.value = user;
};

const cancelDelete = () => {
  userToDelete.value = null;
  deleteLoading.value = false;
};

const deleteUser = async () => {
  if (!userToDelete.value) return;
  
  try {
    deleteLoading.value = true;
    
    const response = await axios.delete(`/api/admin/users/${userToDelete.value.id}`);
    
    if (response.status === 200) {
      // Remove user from local list
      users.value = users.value.filter(user => user.id !== userToDelete.value.id);
      
      // Show success message (you could add a toast notification here)
      console.log('User deleted successfully');
      
      // Close modal
      userToDelete.value = null;
      
      // Optionally reload users to ensure data consistency
      await loadUsers();
    }
  } catch (error) {
    console.error('Error deleting user:', error);
    
    // Show error message
    if (error.response?.data?.error) {
      alert(`Error: ${error.response.data.error}`);
    } else {
      alert('Failed to delete user. Please try again.');
    }
  } finally {
    deleteLoading.value = false;
  }
};

const formatDate = (isoString) => {
  if (!isoString) return 'N/A';
  return new Date(isoString).toLocaleDateString();
};

const getUserStatus = (user) => {
  if (user.active_reservations > 0) return 'Active';
  if (user.total_reservations > 0) return 'Inactive';
  return 'New';
};

const getStatusClass = (user) => {
  if (user.active_reservations > 0) return 'active';
  if (user.total_reservations > 0) return 'inactive';
  return 'new';
};

onMounted(() => {
  loadUsers();
});
</script>

<style scoped>
.users-management h2 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.users-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-card h3 {
  margin: 0;
  font-size: 2rem;
  color: #2c3e50;
}

.stat-card p {
  margin: 0.5rem 0 0 0;
  color: #7f8c8d;
}

.search-section {
  margin-bottom: 2rem;
}

.search-input {
  width: 100%;
  max-width: 400px;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.users-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

th, td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #e9ecef;
  color: #000;
}

th {
  background-color: #f8f9fa;
  font-weight: bold;
  color: #2c3e50;
}

tr:hover {
  background-color: #f8f9fa;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: bold;
}

.status-badge.active {
  background-color: #d4edda;
  color: #155724;
}

.status-badge.inactive {
  background-color: #fff3cd;
  color: #856404;
}

.status-badge.new {
  background-color: #d1ecf1;
  color: #0c5460;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.btn-view {
  background-color: #42b883;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-view:hover {
  background-color: #38a169;
}

.btn-delete {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-delete:hover {
  background-color: #c0392b;
}

.warning-message {
  margin: 1rem 0;
  padding: 1rem;
  background-color: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 4px;
}

.warning-icon {
  font-size: 2rem;
  text-align: center;
  margin-bottom: 1rem;
}

.warning-text {
  color: #856404;
  font-weight: bold;
  margin: 0.5rem 0;
}

.warning-list {
  margin: 0.5rem 0 1rem 1rem;
  color: #856404;
}

.warning-list li {
  margin: 0.25rem 0;
}

.btn-cancel {
  background-color: #6c757d;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 0.5rem;
}

.btn-cancel:hover {
  background-color: #5a6268;
}

.btn-confirm-delete {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.btn-confirm-delete:hover:not(:disabled) {
  background-color: #c0392b;
}

.btn-confirm-delete:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
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
  max-width: 600px;
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

.user-info p {
  margin: 0.5rem 0;
  color: #000;
}

.activity-stats {
  display: grid;
  gap: 0.5rem;
}

.activity-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.activity-label {
  font-weight: bold;
  color: #2c3e50;
}

.activity-value {
  color: #42b883;
  font-weight: bold;
}

.modal-actions {
  margin-top: 2rem;
  text-align: right;
}

.btn-close {
  background-color: #6c757d;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.btn-close:hover {
  background-color: #5a6268;
}

@media (max-width: 768px) {
  .users-stats {
    grid-template-columns: 1fr;
  }
  
  .users-table {
    font-size: 0.875rem;
  }
  
  th, td {
    padding: 0.5rem;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .btn-view, .btn-delete {
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
  }
  
  .modal-content {
    padding: 1rem;
    margin: 1rem;
  }
}

.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #6c757d;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #42b883;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon, .empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.btn-retry {
  background-color: #42b883;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 1rem;
}

.btn-retry:hover {
  background-color: #38a169;
}

.no-results {
  text-align: center;
  padding: 2rem;
  color: #6c757d;
  font-style: italic;
}
</style>
