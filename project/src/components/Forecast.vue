<template>
  <div class="container">
    <div class="header">
      <h1>Time Series Forecasting</h1>
      <p>Upload your CSV data to get forecasts and visualizations.</p>
    </div>

    <!-- File input for CSV upload -->
    <div class="file-upload">
      <input type="file" id="csv-upload" class="file-input" @change="handleFileUpload" accept=".csv" />
      <label for="csv-upload" class="file-input-label">
        <span>Choose CSV File</span>
        <span v-if="selectedFile" class="file-name">{{ selectedFile.name }}</span>
        <span v-else class="file-name">No file chosen</span>
      </label>
      <div class="target-inputs">
        <input type="text" v-model="targetProductId" placeholder="Enter Target Product ID" class="product-input" />
        <div class="target-details" v-if="parsedTarget">
          <p>KODE_BARANG: {{ parsedTarget.kodeBarang }}</p>
          <p>KLASIFIKASI_BARANG: {{ parsedTarget.klasifikasiBarang }}</p>
          <p>WARNA_BARANG: {{ parsedTarget.warnaBarang }}</p>
          <p>UKURAN_BARANG: {{ parsedTarget.ukuranBarang }}</p>
        </div>
      </div>
      <button @click="uploadCSV" :disabled="!selectedFile || !isValidTarget" class="upload-button">
        Upload and Process
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isProcessing" class="loading">
      <p>Processing your file... Please wait.</p>
      <div class="spinner"></div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="error">
      {{ error }}
    </div>

    <!-- Forecast Graph -->
    <div v-if="chartData.length" class="result">
      <h3>Forecast Graph</h3>
      <select v-model="forecastPeriod" class="forecast-period-select">
        <option value="week">1 Week View</option>
        <option value="month">1 Month View</option>
        <option value="year">1 Year View</option>
      </select>
      <canvas id="forecastChart" width="400" height="200"></canvas>
    </div>

    <!-- Forecast Data Table -->
    <div v-if="forecastData.length" class="result">
      <h3>Forecast Data</h3>
      <div class="pagination-controls">
        <select v-model="itemsPerPage" class="page-size-select">
          <option value="5">5 per page</option>
          <option value="10">10 per page</option>
          <option value="20">20 per page</option>
          <option value="50">50 per page</option>
        </select>
        <div class="pagination-buttons">
          <button @click="currentPage--" :disabled="currentPage === 1" class="pagination-button">Previous</button>
          <span class="page-info">Page {{ currentPage }} of {{ totalPages }}</span>
          <button @click="currentPage++" :disabled="currentPage === totalPages" class="pagination-button">Next</button>
        </div>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Forecasted Value</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(data, index) in paginatedData" :key="index">
            <td>{{ data.TANGGAL }}</td>
            <td>{{ data.TOTAL_JUMLAH }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { nextTick } from 'vue';
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { uploadCSV, checkTaskStatus, downloadFile } from '../services/api';

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend
);

export default {
  name: 'TimeSeriesForecast',
  data() {
    return {
      selectedFile: null,
      targetProductId: '',
      originalData: [],
      forecastData: [],
      chartData: [],
      chartLabels: [],
      chartInstance: null,
      isProcessing: false,
      error: null,
      taskId: null,
      statusCheckInterval: null,
      parsedTarget: null,
      currentPage: 1,
      itemsPerPage: 10,
      forecastPeriod: localStorage.getItem('lastForecastPeriod') || 'month'
    };
  },
  computed: {
    isValidTarget() {
      return this.parsedTarget !== null;
    },
    totalPages() {
      return Math.ceil(this.forecastData.length / this.itemsPerPage);
    },
    paginatedData() {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      const end = start + this.itemsPerPage;
      return this.forecastData.slice(start, end);
    }
  },
  watch: {
    targetProductId(newValue) {
      this.parseTargetProductId(newValue);
    },
    forecastPeriod() {
      this.updateForecastView();
    }
  },
  async mounted() {
    // Try to load data in this order: localStorage -> server -> empty state
    await this.loadSavedData();
  },
  methods: {
    parseTargetProductId(id) {
      if (!id) {
        this.parsedTarget = null;
        return;
      }
      const parts = id.split('_');
      if (parts.length !== 4) {
        this.parsedTarget = null;
        return;
      }
      this.parsedTarget = {
        kodeBarang: parts[0],
        klasifikasiBarang: parts[1],
        warnaBarang: parts[2],
        ukuranBarang: parts[3]
      };
    },

    handleFileUpload(event) {
      this.selectedFile = event.target.files[0];
      this.error = null;
    },

    async uploadCSV() {
      if (!this.selectedFile || !this.isValidTarget) {
        this.error = 'Please select a file and enter a valid target product ID';
        return;
      }
      this.isProcessing = true;
      this.error = null;

      try {
        const response = await uploadCSV(this.selectedFile, this.targetProductId);
        if (response && response.task_id) {
          this.taskId = response.task_id;
          this.startStatusCheck();
        } else {
          throw new Error('Server response missing task ID');
        }
      } catch (error) {
        this.error = error.response?.data?.message || error.message || 'Error uploading file. Please try again.';
        this.isProcessing = false;
      }
    },

    startStatusCheck() {
      if (this.statusCheckInterval) {
        clearInterval(this.statusCheckInterval);
      }
      this.statusCheckInterval = setInterval(this.checkStatus, 2000);
    },

    async checkStatus() {
      if (!this.taskId) return;
      try {
        const status = await checkTaskStatus(this.taskId);
        if (status.output_file) {
          clearInterval(this.statusCheckInterval);
          await this.downloadAndProcessFile(status.output_file);
          this.isProcessing = false;
        } else if (status.error) {
          clearInterval(this.statusCheckInterval);
          this.error = 'Processing failed: ' + status.error;
          this.isProcessing = false;
        }
      } catch (error) {
        this.error = 'Error checking status. Retrying...';
      }
    },

    async loadSavedData() {
      // Try to load from localStorage
      const cachedData = localStorage.getItem('forecastData');
      const cachedTimestamp = localStorage.getItem('forecastDataTimestamp');
      const cacheExpiry = 24 * 60 * 60 * 1000; // 24 hours

      if (cachedData && cachedTimestamp) {
        const timestamp = parseInt(cachedTimestamp);
        if (Date.now() - timestamp < cacheExpiry) {
          try {
            this.originalData = JSON.parse(cachedData);
            this.updateForecastView();
            return;
          } catch (e) {
            // Ignore parse error, fallback to server
          }
        }
      }

      // If cache is missing or expired, try to load from server
      try {
        const response = await fetch('http://localhost:8000/latest-output/');
        if (response.ok) {
          const data = await response.json();
          if (data && data.length > 0) {
            this.originalData = data;
            this.updateForecastView();
            this.updateCache(data);
          }
        }
      } catch (error) {
        // Ignore error, just don't load data
      }
    },

    updateCache(data) {
      try {
        localStorage.setItem('forecastData', JSON.stringify(data));
        localStorage.setItem('forecastDataTimestamp', Date.now().toString());
      } catch (e) {
        // Ignore cache error
      }
    },

    async downloadAndProcessFile(filename) {
      try {
        const blob = await downloadFile(filename);
        const reader = new FileReader();
        reader.onload = (e) => {
          const text = e.target.result;
          const rows = text.split('\n').map(row => row.split(','));
          const headers = rows[0];
          const data = rows.slice(1).map(row => {
            const obj = {};
            headers.forEach((header, index) => {
              obj[header] = row[index];
            });
            return obj;
          });
          this.originalData = data;
          this.updateCache(data);
          this.updateForecastView();
          this.isProcessing = false;
        };
        reader.readAsText(blob);
      } catch (error) {
        this.error = 'Error processing downloaded file. Please try again.';
        this.isProcessing = false;
      }
    },

    updateForecastView() {
      if (!this.originalData.length) return;

      // Save last used period
      localStorage.setItem('lastForecastPeriod', this.forecastPeriod);

      // Update table data based on period
      if (this.forecastPeriod === 'week') {
        this.forecastData = this.originalData.slice(0, 7);
      } else if (this.forecastPeriod === 'month') {
        this.forecastData = this.originalData.slice(0, 30);
      } else {
        this.forecastData = this.originalData;
      }

      // Update chart data based on period
      if (this.forecastPeriod === 'year') {
        // Process monthly data for the chart
        const monthlyData = {};
        this.originalData.forEach(item => {
          const date = new Date(item.TANGGAL);
          const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          if (!monthlyData[monthKey]) {
            monthlyData[monthKey] = { total: 0, count: 0 };
          }
          monthlyData[monthKey].total += parseFloat(item.TOTAL_JUMLAH);
          monthlyData[monthKey].count += 1;
        });

        const monthlyArray = Object.entries(monthlyData)
          .map(([date, data]) => ({
            TANGGAL: date,
            TOTAL_JUMLAH: (data.total / data.count).toFixed(2)
          }))
          .sort((a, b) => a.TANGGAL.localeCompare(b.TANGGAL));

        this.chartData = monthlyArray.map(item => parseFloat(item.TOTAL_JUMLAH));
        this.chartLabels = monthlyArray.map(item => {
          const [year, month] = item.TANGGAL.split('-');
          return new Date(year, month - 1).toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
        });
      } else {
        // For week and month views, show daily data in the chart
        const filteredData = this.forecastPeriod === 'week'
          ? this.originalData.slice(0, 7)
          : this.originalData.slice(0, 30);

        this.chartData = filteredData.map(item => parseFloat(item.TOTAL_JUMLAH));
        this.chartLabels = filteredData.map(item => {
          const date = new Date(item.TANGGAL);
          return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
      }

      nextTick(() => {
        this.renderChart();
      });
    },

    renderChart() {
      const ctx = document.getElementById('forecastChart').getContext('2d');
      if (this.chartInstance) {
        this.chartInstance.destroy();
      }
      this.chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: this.chartLabels,
          datasets: [{
            label: this.forecastPeriod === 'year' ? 'Monthly Average' : 'Daily Value',
            data: this.chartData,
            borderColor: '#4CAF50',
            backgroundColor: 'rgba(76, 175, 80, 0.2)',
            fill: true,
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          scales: {
            x: {
              type: 'category',
              title: {
                display: true,
                text: this.forecastPeriod === 'year' ? 'Month' : 'Date'
              }
            },
            y: {
              title: {
                display: true,
                text: this.forecastPeriod === 'year' ? 'Monthly Average' : 'Daily Value'
              }
            }
          }
        }
      });
    }
  },
  beforeUnmount() {
    if (this.statusCheckInterval) {
      clearInterval(this.statusCheckInterval);
    }
  }
};
</script>
