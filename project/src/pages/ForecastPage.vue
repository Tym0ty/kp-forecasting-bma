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