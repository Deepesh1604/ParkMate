<template>
  <div class="reports-view">
    <h1>🔬 Overall Insights</h1>
    
    
    <div class="button-group">
     
      <button @click="loadAllGraphs" :disabled="loading">Load All Graphs</button>
      <button @click="clearGraphs" :disabled="loading">Clear Graphs</button>
    </div>
    
    <div id="status" v-html="generalStatus"></div>
    
    <div class="graph-container">
      <h3>📊 Occupancy Analysis</h3>
      <div class="status" v-html="graphs.occupancy.status"></div>
      <div class="graph-content" v-html="graphs.occupancy.content"></div>
    </div>
    
    <div class="graph-container">
      <h3>💰 Revenue Analysis</h3>
      <div class="status" v-html="graphs.revenue.status"></div>
      <div class="graph-content" v-html="graphs.revenue.content"></div>
    </div>
    
    <div class="graph-container">
      <h3>📈 Usage Patterns</h3>
      <div class="status" v-html="graphs.usage.status"></div>
      <div class="graph-content" v-html="graphs.usage.content"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ReportsView',
  data() {
    return {
      loading: false,
      generalStatus: '',
      API_BASE: 'http://localhost:5001',
      graphs: {
        occupancy: {
          status: '',
          content: ''
        },
        revenue: {
          status: '',
          content: ''
        },
        usage: {
          status: '',
          content: ''
        }
      }
    }
  },
  methods: {
    async loginAsAdmin() {
      this.loading = true;
      this.generalStatus = '<div class="loading">Logging in as admin...</div>';
      
      try {
        const response = await fetch(`${this.API_BASE}/api/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            username: 'admin',
            password: 'admin123'
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          this.generalStatus = '<div class="success">✅ Logged in successfully as admin!</div>';
          console.log('Login successful:', data);
        } else {
          throw new Error(`Login failed: ${response.status}`);
        }
      } catch (error) {
        this.generalStatus = `<div class="error">❌ Login failed: ${error.message}</div>`;
        console.error('Login error:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async loadGraph(type) {
      this.graphs[type].status = '<div class="loading">Loading graph...</div>';
      this.graphs[type].content = '';
      
      try {
        const response = await fetch(`${this.API_BASE}/api/admin/graphs/${type}`, {
          credentials: 'include'
        });
        
        if (response.ok) {
          const data = await response.json();
          this.graphs[type].status = '<div class="success">✅ Graph loaded successfully!</div>';
          
          // Display the graph
          this.graphs[type].content = `
            <img src="data:image/png;base64,${data.graph}" class="graph-img" alt="${type} graph">
            <div style="margin-top: 10px;">
              <strong>Summary:</strong> ${JSON.stringify(data.summary, null, 2)}
            </div>
          `;
        } else if (response.status === 403) {
          this.graphs[type].status = '<div class="error">❌ Access denied. Please login as admin first.</div>';
        } else {
          throw new Error(`Failed to load graph: ${response.status}`);
        }
      } catch (error) {
        this.graphs[type].status = `<div class="error">❌ Error loading graph: ${error.message}</div>`;
        console.error(`Error loading ${type} graph:`, error);
      }
    },
    
    async loadAllGraphs() {
      this.loading = true;
      try {
        await Promise.all([
          this.loadGraph('occupancy'),
          this.loadGraph('revenue'),
          this.loadGraph('usage')
        ]);
      } finally {
        this.loading = false;
      }
    },
    
    clearGraphs() {
      Object.keys(this.graphs).forEach(type => {
        this.graphs[type].status = '';
        this.graphs[type].content = '';
      });
      this.generalStatus = '';
    }
  }
}
</script>

<style scoped>
.reports-view {
  font-family: Arial, sans-serif;
  color: #333;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.button-group {
  margin-bottom: 20px;
}

.graph-container {
  margin-bottom: 30px;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
}

.graph-container h3 {
  margin-top: 0;
  color: #333;
}

.graph-img {
  width: 10%;
  max-width: auto;
  height: auto;
  border: 1px solid #ccc;
  border-radius: 4px;
}

/* Status message styles */
:deep(.error) {
  color: #e74c3c;
  padding: 10px;
  background: #ffe6e6;
  border-radius: 4px;
}

:deep(.loading) {
  color: #3498db;
  padding: 10px;
  background: #e6f3ff;
  border-radius: 4px;
}

:deep(.success) {
  color: #27ae60;
  padding: 10px;
  background: #e6ffe6;
  border-radius: 4px;
}

button {
  background: #3498db;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 10px;
}

button:hover:not(:disabled) {
  background: #2980b9;
}

button:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}
</style>