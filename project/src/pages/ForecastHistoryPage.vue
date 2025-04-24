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
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in history" :key="idx">
            <td>{{ row[0] }}</td>
            <td>{{ row[1] }}</td>
            <td>{{ row[2] }}</td>
            <td>{{ row[3] }}</td>
            <td>{{ row[4] }}</td>
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
    this.loading = true
    this.error = null
    try {
      const res = await axios.get('http://localhost:8000/forecast-history/')
      this.history = res.data || []
    } catch (err) {
      this.error = 'Failed to load forecast history. Please try again.'
      console.error(err)
    } finally {
      this.loading = false
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

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>