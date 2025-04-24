<template>
  <div class="forecast-page">
    <h1>Start Forecast</h1>

    <!-- Input Section -->
    <div class="input-section">
      <label for="target">Target Product ID</label>
      <input
        id="target"
        v-model="targetProduct"
        class="product-input"
        placeholder="MP000294_KD000016_PL000037_SZ000012"
      />
      <button
        class="fetch-button"
        :disabled="!targetProduct || loading"
        @click="startForecast"
      >
        {{ loading ? 'Starting...' : 'Start Forecast' }}
      </button>
    </div>

    <!-- Status / Loading -->
    <div v-if="loadingStatus" class="status">
      <p>{{ statusMessage }}</p>
      <div class="spinner"></div>
    </div>

    <!-- Error -->
    <div v-if="error" class="error">{{ error }}</div>

    <!-- Success / Download -->
    <div v-if="finished && result?.output_file" class="result">
      <p>Forecast completed!</p>
      <a
        :href="downloadUrl"
        class="download-button"
        target="_blank"
      >
        Download Forecast CSV
      </a>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ForecastPage',
  data() {
    return {
      targetProduct: '',
      loading: false,         // for initial POST
      loadingStatus: false,   // for polling spinner
      statusMessage: '',
      taskId: null,
      error: null,
      result: null,
      finished: false,
      pollInterval: null
    }
  },
  computed: {
    downloadUrl() {
      // Extract filename and build download link
      const path = this.result.output_file || ''
      const filename = path.split('/').pop()
      return `http://localhost:8000/download/${filename}`
    }
  },
  methods: {
    async startForecast() {
      this.error = null
      this.result = null
      this.finished = false
      this.loading = true
      try {
        const res = await axios.post(
          `http://localhost:8000/process-csv/`,
          null,
          { params: { target_product_id: this.targetProduct } }
        )
        this.taskId = res.data.task_id
        this.loading = false
        this.loadingStatus = true
        this.statusMessage = 'Forecast queued...'
        this.pollInterval = setInterval(this.checkStatus, 2000)
      } catch (err) {
        this.error = 'Failed to start forecast. Please try again.'
        console.error(err)
        this.loading = false
      }
    },
    async checkStatus() {
      if (!this.taskId) return
      try {
        const res = await axios.get(
          `http://localhost:8000/task-status/${this.taskId}`
        )
        const { state, status, result } = res.data
        if (state === 'PENDING' || state === 'PROGRESS') {
          this.statusMessage = status || 'Processing...'
        } else if (state === 'SUCCESS') {
          clearInterval(this.pollInterval)
          this.result = result || {}
          this.statusMessage = 'Done'
          this.loadingStatus = false
          this.finished = true
          // show a success popup
          window.alert('Forecast completed successfully!')
          // redirect to history page
          this.$router.push('/forecast-history')
        } else {
          // FAILURE or other
          clearInterval(this.pollInterval)
          this.statusMessage = status || 'Error during processing.'
          this.loadingStatus = false
          this.error = this.statusMessage
        }
      } catch (err) {
        clearInterval(this.pollInterval)
        this.loadingStatus = false
        this.error = 'Error fetching status.'
        console.error(err)
      }
    }
  },
  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval)
    }
  }
}
</script>

<style scoped>
.forecast-page {
  padding: 2rem;
  background-color: #f9f9f9;
  min-height: 100vh;
}

.forecast-page h1 {
  margin-bottom: 1.5rem;
  color: #333;
}

.input-section {
  margin-bottom: 2rem;
  background-color: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  gap: 1rem;
  align-items: center;
}

.product-input {
  flex: 1;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
}

.fetch-button {
  padding: 0.75rem 1.5rem;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.fetch-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.fetch-button:hover:not(:disabled) {
  background-color: #45a049;
}

.status {
  text-align: center;
  margin: 2rem 0;
  font-size: 1.1rem;
}

.error {
  color: #e74c3c;
  text-align: center;
  margin: 1.5rem 0;
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
  text-align: center;
  margin-top: 2rem;
}

.download-button {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background-color: #4CAF50;
  color: white;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 500;
  transition: background-color 0.2s;
}

.download-button:hover {
  background-color: #45a049;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>