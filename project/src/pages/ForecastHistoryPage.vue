<template>
  <div class="history-page">
    <h1>Forecast History</h1>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <p>Loading history... Please wait.</p>
      <div class="spinner"></div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="error">{{ error }}</div>

    <!-- History Table -->
    <div v-if="history.length" class="result">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Product Code</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Timestamp</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in history" :key="row.id">
            <td>{{ row.id }}</td>
            <td>{{ row.product_id }}</td>
            <td>{{ formatDate(row.date_start) }}</td>
            <td>{{ formatDate(row.date_end) }}</td>
            <td>{{ formatDate(row.timestamp) }}</td>
            <td>
              <button 
                class="download-button" 
                @click="downloadForecast(row.csv_path)"
                title="Download forecast data"
              >
                <svg class="download-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                  <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
                </svg>
                Download
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !history.length && !error" class="empty">
      <p>No history records found.</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ForecastHistoryPage',
  data() {
    return {
      loading: false,
      error: null,
      history: []
    }
  },
  async mounted() {
    await this.fetchHistory()
  },
  methods: {
    async fetchHistory() {
      this.loading = true
      this.error = null
      try {
        const res = await axios.get('http://localhost:8000/forecast-history/')
        // Make sure we get an array of objects with consistent properties
        this.history = Array.isArray(res.data) ? 
          res.data.map(item => {
            // Handle both array and object responses
            if (Array.isArray(item)) {
              return {
                id: item[0],
                product_id: item[1],
                date_start: item[2],
                date_end: item[3],
                csv_path: item[4],
                timestamp: item[5] || new Date().toISOString()
              }
            }
            return item
          }) : []
      } catch (err) {
        this.error = 'Failed to load forecast history. Please try again.'
        console.error(err)
      } finally {
        this.loading = false
      }
    },
    
    async downloadForecast(path) {
      try {
        // Extract filename from path
        const filename = path.split('/').pop()
        
        // Call the download API endpoint
        const response = await axios.get(`http://localhost:8000/download/${filename}`, {
          responseType: 'blob'
        })
        
        // Create download link and trigger download
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        
        // Clean up
        window.URL.revokeObjectURL(url)
        document.body.removeChild(link)
      } catch (err) {
        this.error = `Failed to download forecast: ${err.message}`
        console.error('Download error:', err)
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      try {
        const date = new Date(dateString)
        return date.toLocaleString()
      } catch (e) {
        return dateString
      }
    }
  }
}
</script>

<style scoped>
.history-page {
  padding: 2rem;
  background-color: #f9f9f9;
  min-height: 100vh;
}

.history-page h1 {
  margin-bottom: 1.5rem;
  color: #333;
}

.loading,
.error,
.empty {
  text-align: center;
  margin: 2rem 0;
  font-size: 1.1rem;
}

.error {
  color: #e74c3c;
}

.spinner {
  width: 50px;
  height: 50px;
  margin: 1rem auto;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.result {
  background-color: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.data-table th,
.data-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #ddd;
  text-align: left;
}

.data-table th {
  background-color: #4CAF50;
  color: white;
  font-weight: 500;
}

.data-table tr:nth-child(even) {
  background-color: #f5f5f5;
}

.data-table tr:hover {
  background-color: #eaeaea;
}

.download-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.download-button:hover {
  background-color: #45a049;
}

.download-icon {
  font-size: 16px;
  width: 16px;
  height: 16px;
  margin-right: 4px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>