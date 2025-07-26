<template>
  <div class="reports-view">
    <h1>🔬 Overall Insights</h1>
    
    <div class="button-group">
      <button @click="loadAllGraphs" :disabled="loading">Load All Graphs</button>
      <button @click="clearGraphs" :disabled="loading">Clear Graphs</button>
    </div>
    
    <div id="status" v-html="generalStatus"></div>
    
    <div class="graphs-wrapper">
      <div class="graph-container">
        <h3>📊 Occupancy Analysis</h3>
        <div class="status-section" v-html="graphs.occupancy.status"></div>
        <div class="graph-content-section" v-html="graphs.occupancy.content"></div>
      </div>
      
      <div class="graph-container">
        <h3>💰 Revenue Analysis</h3>
        <div class="status-section" v-html="graphs.revenue.status"></div>
        <div class="graph-content-section" v-html="graphs.revenue.content"></div>
      </div>
      
      <div class="graph-container">
        <h3>📈 Usage Patterns</h3>
        <div class="status-section" v-html="graphs.usage.status"></div>
        <div class="graph-content-section" v-html="graphs.usage.content"></div>
      </div>
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
          
          // Display the graph with better structure and fixed sizing
          this.graphs[type].content = `
            <div class="graph-image-wrapper">
              <div class="graph-title-overlay">${type.charAt(0).toUpperCase() + type.slice(1)} Analytics Dashboard</div>
              <img src="data:image/png;base64,${data.graph}" class="graph-img" alt="${type} graph" loading="lazy">
            </div>
            <div class="graph-summary">
              <h4>📋 Summary Details:</h4>
              <div class="summary-content">
                <pre class="summary-text">${JSON.stringify(data.summary, null, 2)}</pre>
              </div>
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
  max-width: 1400px;
  margin: 0 auto;
  padding: 30px;
  background-color: #f8f9fa;
  min-height: 100vh;
}

.reports-view h1 {
  text-align: center;
  margin-bottom: 40px;
  font-size: 2.5em;
  color: #2c3e50;
}

.button-group {
  text-align: center;
  margin-bottom: 40px;
}

.graphs-wrapper {
  display: flex;
  flex-direction: column;
  gap: 50px; /* Increased spacing between graph containers */
}

.graph-container {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  border: 2px solid #e1e8ed;
  border-radius: 16px;
  padding: 50px;
  background: #ffffff;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  overflow: visible;
  position: relative;
}

.graph-container::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, #3498db, #2ecc71, #9b59b6, #e74c3c);
  border-radius: 18px;
  z-index: -1;
  opacity: 0.1;
}

.graph-container h3 {
  margin-top: 0;
  margin-bottom: 30px;
  color: #2c3e50;
  font-size: 1.5em;
  text-align: center;
  padding-bottom: 15px;
  border-bottom: 3px solid #3498db;
}

.status-section {
  margin-bottom: 25px;
  min-height: 20px; /* Prevents layout shift */
}

.graph-content-section {
  margin-top: 30px;
}

/* Graph image wrapper with fixed dimensions */
:deep(.graph-image-wrapper) {
  position: relative;
  text-align: center;
  margin: 30px 0;
  padding: 25px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  border: 2px solid #dee2e6;
  overflow: hidden;
  min-height: 650px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

:deep(.graph-title-overlay) {
  position: absolute;
  top: 15px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(52, 152, 219, 0.9);
  color: white;
  padding: 8px 20px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
  z-index: 10;
  backdrop-filter: blur(10px);
}

:deep(.graph-img) {
  width: 100%;
  min-width: 900px;
  height: auto;
  min-height: 600px;
  max-height: 800px;
  object-fit: contain;
  border: 3px solid #ffffff;
  border-radius: 12px;
  display: block;
  margin: 20px auto 0;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  background-color: white;
  transition: transform 0.3s ease;
}

:deep(.graph-img:hover) {
  transform: scale(1.02);
}

/* Summary section with better organization */
:deep(.graph-summary) {
  margin-top: 40px;
  padding: 30px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-radius: 12px;
  border: 2px solid #e3f2fd;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
}

:deep(.graph-summary h4) {
  margin-top: 0;
  margin-bottom: 20px;
  color: #2c3e50;
  font-size: 1.3em;
  text-align: center;
  padding-bottom: 15px;
  border-bottom: 2px solid #3498db;
}

:deep(.summary-content) {
  background-color: #ffffff;
  border-radius: 8px;
  border: 1px solid #e1e8ed;
  overflow: hidden;
}

:deep(.summary-text) {
  background-color: transparent;
  padding: 25px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.8;
  color: #2c3e50;
  overflow-x: auto;
  white-space: pre-wrap;
  margin: 0;
  border: none;
  max-height: 300px;
  overflow-y: auto;
}

/* Status message styles with better spacing */
:deep(.error) {
  color: #e74c3c;
  padding: 15px 20px;
  background: #ffeaea;
  border-radius: 8px;
  border-left: 4px solid #e74c3c;
  margin: 10px 0;
}

:deep(.loading) {
  color: #3498db;
  padding: 15px 20px;
  background: #e3f2fd;
  border-radius: 8px;
  border-left: 4px solid #3498db;
  margin: 10px 0;
}

:deep(.success) {
  color: #27ae60;
  padding: 15px 20px;
  background: #eafaf1;
  border-radius: 8px;
  border-left: 4px solid #27ae60;
  margin: 10px 0;
}

button {
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: white;
  border: none;
  padding: 12px 25px;
  border-radius: 8px;
  cursor: pointer;
  margin: 0 10px;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.3s ease;
}

button:hover:not(:disabled) {
  background: linear-gradient(135deg, #2980b9, #21618c);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
}

button:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* Responsive design improvements */
@media (max-width: 1024px) {
  .graph-container {
    max-width: 95%;
    padding: 30px;
  }
  
  :deep(.graph-img) {
    max-height: 400px;
  }
}

@media (max-width: 768px) {
  .reports-view {
    padding: 15px;
  }
  
  .graph-container {
    padding: 20px;
    margin: 0 10px;
  }
  
  :deep(.graph-image-wrapper) {
    min-height: 300px;
    padding: 15px;
  }
  
  :deep(.graph-img) {
    max-height: 300px;
  }
  
  :deep(.summary-text) {
    font-size: 11px;
    padding: 15px;
    max-height: 200px;
  }
  
  :deep(.graph-title-overlay) {
    font-size: 12px;
    padding: 6px 15px;
  }
}

@media (max-width: 480px) {
  .graphs-wrapper {
    gap: 30px;
  }
  
  .graph-container {
    padding: 15px;
  }
  
  :deep(.graph-summary) {
    padding: 20px;
  }
}
</style>