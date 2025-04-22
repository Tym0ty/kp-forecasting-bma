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
        <select v-model="forecastPeriod" class="forecast-period-select">
          <option value="week">1 Week Ahead</option>
          <option value="month">1 Month Ahead</option>
          <option value="year">1 Year Ahead</option>
        </select>
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

// Register necessary components with Chart.js
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
      forecastPeriod: 'month' // Default to 1 month
    };
  },
  mounted() {
    // Load cached data when component mounts
    this.loadCachedData();
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
      // Reprocess data with new period if we have data
      if (this.forecastData.length > 0) {
        this.processForecastData(this.forecastData);
        // Update cache with new period
        this.saveCacheData(this.forecastData);
      }
    }
  },
  methods: {
    loadCachedData() {
      try {
        const cachedData = localStorage.getItem('forecastCache');
        if (cachedData) {
          const { forecastData, targetProductId, forecastPeriod } = JSON.parse(cachedData);
          this.targetProductId = targetProductId;
          this.forecastPeriod = forecastPeriod;
          this.parseTargetProductId(targetProductId);
          
          // Process the cached data
          this.processForecastData(forecastData);
        }
      } catch (error) {
        console.error('Error loading cached data:', error);
      }
    },

    saveCacheData(data) {
      try {
        const cacheData = {
          forecastData: data,
          targetProductId: this.targetProductId,
          forecastPeriod: this.forecastPeriod
        };
        localStorage.setItem('forecastCache', JSON.stringify(cacheData));
      } catch (error) {
        console.error('Error saving cache:', error);
      }
    },

    processForecastData(data) {
      // Filter data based on forecast period
      let filteredData = data;
      if (this.forecastPeriod === 'week') {
        filteredData = data.slice(0, 7); // First 7 days
      } else if (this.forecastPeriod === 'month') {
        filteredData = data.slice(0, 30); // First 30 days
      }

      // Keep daily data for the table
      this.forecastData = filteredData;

      // Process data for the graph based on forecast period
      if (this.forecastPeriod === 'year') {
        // Aggregate data by month for yearly view
        const monthlyData = {};
        data.forEach(item => {
          const date = new Date(item.TANGGAL);
          const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          
          if (!monthlyData[monthKey]) {
            monthlyData[monthKey] = {
              total: 0,
              count: 0
            };
          }
          
          monthlyData[monthKey].total += parseFloat(item.TOTAL_JUMLAH);
          monthlyData[monthKey].count += 1;
        });

        const monthlyArray = Object.entries(monthlyData).map(([date, data]) => ({
          TANGGAL: date,
          TOTAL_JUMLAH: (data.total / data.count).toFixed(2)
        })).sort((a, b) => a.TANGGAL.localeCompare(b.TANGGAL));

        this.chartData = monthlyArray.map(item => parseFloat(item.TOTAL_JUMLAH));
        this.chartLabels = monthlyArray.map(item => {
          const [year, month] = item.TANGGAL.split('-');
          return new Date(year, month - 1).toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
        });
      } else {
        // Use daily data for weekly and monthly views
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
        console.log('Upload response:', response); // Debug log
        
        if (response && response.task_id) {
          this.taskId = response.task_id;
          this.startStatusCheck();
        } else {
          console.error('Invalid response format:', response);
          throw new Error('Server response missing task ID');
        }
      } catch (error) {
        console.error('Upload error details:', error);
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
        // Continue polling if no filename or error is received
      } catch (error) {
        // Don't clear interval on network errors, keep trying
        this.error = 'Error checking status. Retrying...';
        console.error('Status check error:', error);
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

          // Save to cache before processing
          this.saveCacheData(data);
          
          // Process the data
          this.processForecastData(data);
          this.isProcessing = false;
        };

        reader.readAsText(blob);
      } catch (error) {
        this.error = 'Error processing downloaded file. Please try again.';
        this.isProcessing = false;
      }
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
                text: this.forecastPeriod === 'year' ? 'Average Total Weight' : 'Total Weight'
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

<style scoped>
.container {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.header {
  text-align: center;
  margin-bottom: 2rem;
}

.header h1 {
  font-size: 2.5rem;
  color: #333;
  margin-bottom: 0.5rem;
}

.header p {
  color: #666;
  font-size: 1.1rem;
  margin: 0;
}

.file-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.file-input {
  width: 0.1px;
  height: 0.1px;
  opacity: 0;
  overflow: hidden;
  position: absolute;
  z-index: -1;
}

.file-input-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  width: 100%;
  max-width: 400px;
  font-size: 1rem;
  font-weight: 500;
  color: #fff;
  background-color: #4CAF50;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.file-input-label:hover {
  background-color: #45a049;
}

.file-name {
  font-size: 0.9rem;
  opacity: 0.9;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.target-inputs {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.product-input,
.forecast-period-select {
  width: 100%;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
  transition: border-color 0.2s;
}

.product-input:focus,
.forecast-period-select:focus {
  outline: none;
  border-color: #4CAF50;
}

.target-details {
  padding: 1rem;
  background-color: #f5f5f5;
  border-radius: 6px;
  text-align: left;
}

.target-details p {
  margin: 0.5rem 0;
  color: #333;
}

.upload-button {
  display: inline-block;
  width: 100%;
  max-width: 400px;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  color: #fff;
  background-color: #4CAF50;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.upload-button:hover:not(:disabled) {
  background-color: #45a049;
}

.upload-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.result {
  margin-top: 40px;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.data-table {
  width: 100%;
  margin: 20px auto;
  border-collapse: collapse;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.data-table th, .data-table td {
  padding: 15px;
  text-align: center;
  border-bottom: 1px solid #ddd;
  color: #333;
}

.data-table th {
  background-color: #4CAF50;
  color: white;
  font-size: 1.1rem;
}

.data-table tr:nth-child(even) {
  background-color: #f9f9f9;
}

.data-table tr:hover {
  background-color: #f1f1f1;
}

.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 20px 0;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 8px;
}

.page-size-select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
}

.pagination-buttons {
  display: flex;
  align-items: center;
  gap: 15px;
}

.pagination-button {
  padding: 10px 20px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.pagination-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.pagination-button:hover:not(:disabled) {
  background-color: #45a049;
}

.page-info {
  color: #333;
  font-size: 1rem;
}

.loading {
  margin: 30px 0;
  text-align: center;
}

.spinner {
  width: 50px;
  height: 50px;
  margin: 20px auto;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.error {
  color: #ff0000;
  margin: 20px 0;
  padding: 15px;
  background-color: #ffebee;
  border-radius: 8px;
  text-align: center;
}

canvas {
  width: 100% !important;
  max-width: 1000px;
  margin: 30px auto;
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
