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
      <table class="data-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Forecasted Value</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(data, index) in forecastData" :key="index">
            <td>{{ data.TANGGAL }}</td>
            <td>{{ data.BERAT_TOTAL }}</td>
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
      parsedTarget: null
    };
  },
  computed: {
    isValidTarget() {
      return this.parsedTarget !== null;
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

          this.forecastData = data;
          this.chartData = data.map(item => parseFloat(item.TOTAL_JUMLAH));
          this.chartLabels = data.map(item => item.TANGGAL);

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
            label: 'BERAT_TOTAL',
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
                text: 'Date'
              }
            },
            y: {
              title: {
                display: true,
                text: 'Total Weight (BERAT_TOTAL)'
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
</style>
