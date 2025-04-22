<template>
  <div class="container">
    <div class="header">
      <h1>Time Series Forecasting</h1>
      <p>Upload your CSV data to get forecasts and visualizations.</p>
    </div>

    <!-- File input for CSV upload -->
    <div class="file-upload">
      <input type="file" class="file-input" @change="handleFileUpload" accept=".csv" />
      <div class="target-inputs">
        <input type="text" v-model="targetProductId" placeholder="Enter Target Product ID (e.g., MP000294_KD000016_PL000037_SZ000012)" class="product-input" />
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
    }
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
/* Body and general layout */
body {
  font-family: 'Roboto', sans-serif;
  background-color: #f9fafb;
  margin: 0;
  padding: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
}

.container {
  width: 80%;
  max-width: 900px;
  padding: 30px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.header h1 {
  font-size: 2.5rem;
  color: #333;
  margin-bottom: 10px;
}

.header p {
  color: #555;
  font-size: 1.1rem;
  margin-bottom: 30px;
}

.file-upload {
  margin-bottom: 30px;
}

.file-input {
  font-size: 1.1rem;
  padding: 10px;
  color: #fff;
  background-color: #4CAF50;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.file-input:hover {
  background-color: #45a049;
}

/* Result Section */
.result {
  margin-top: 40px;
}

.data-table {
  width: 100%;
  margin-top: 20px;
  border-collapse: collapse;
  border-radius: 8px;
  overflow: hidden;
}

.data-table th, .data-table td {
  padding: 12px;
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

canvas {
  width: 100% !important;
  max-width: 800px;
  margin: 0 auto;
  margin-top: 20px;
}

.target-inputs {
  margin: 20px 0;
}

.target-details {
  margin: 10px 0;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 5px;
}

.target-details p {
  margin: 5px 0;
  color: #333;
}

.product-input {
  font-size: 1.1rem;
  padding: 10px;
  margin: 10px 0;
  width: 100%;
  max-width: 400px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

.upload-button {
  font-size: 1.1rem;
  padding: 10px 20px;
  color: #fff;
  background-color: #4CAF50;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  width: 100%;
  max-width: 400px;
  margin: 10px auto;
}

.upload-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.loading {
  margin: 20px 0;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  margin: 20px auto;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  color: #ff0000;
  margin: 20px 0;
  padding: 10px;
  background-color: #ffebee;
  border-radius: 5px;
}

.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 5px;
}

.page-size-select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
}

.pagination-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pagination-button {
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
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
  font-size: 0.9rem;
}

.forecast-period-select {
  font-size: 1.1rem;
  padding: 10px;
  margin: 10px 0;
  width: 100%;
  max-width: 400px;
  border: 1px solid #ddd;
  border-radius: 5px;
  background-color: white;
}
</style>
