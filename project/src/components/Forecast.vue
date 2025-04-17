<template>
  <div class="container">
    <div class="header">
      <h1>Time Series Forecasting</h1>
      <p>Upload your CSV data to get forecasts and visualizations.</p>
    </div>

    <!-- File input for CSV upload -->
    <div class="file-upload">
      <input type="file" class="file-input" @change="handleFileUpload" accept=".csv" />
    </div>

    <!-- Forecast Graph - this will be shown right after CSV is uploaded -->
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
            <td>{{ data.DATE }}</td>
            <td>{{ data.BERAT_TOTAL }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
// Import Vue's nextTick to ensure DOM updates are complete before rendering the chart
import { nextTick } from 'vue';
import { Chart } from 'chart.js';

export default {
  name: 'TimeSeriesForecast',
  data() {
    return {
      forecastData: [],  // Forecast data to populate the table and chart
      chartData: [],      // Chart data points
      chartLabels: []     // Chart labels (dates)
    };
  },
  methods: {
    // Handle file upload (mocking the backend response)
    handleFileUpload() {
      // Simulating the backend response
      this.uploadCSV();
    },

    // Mock the backend CSV processing and response
    uploadCSV() {
      // Mocked forecast data based on the format you provided
      const mockData = [
        { "BERAT_TOTAL": 681.0, "DATE": "2023-01-02" },
        { "BERAT_TOTAL": 2742.0, "DATE": "2023-01-03" },
        { "BERAT_TOTAL": 647.0, "DATE": "2023-01-04" },
        { "BERAT_TOTAL": 123.0, "DATE": "2023-01-05" },
        { "BERAT_TOTAL": 341.0, "DATE": "2023-01-06" },
        { "BERAT_TOTAL": 535.0, "DATE": "2023-12-18" },
        { "BERAT_TOTAL": 280.0, "DATE": "2023-12-19" },
        { "BERAT_TOTAL": 8.0, "DATE": "2023-12-20" },
        { "BERAT_TOTAL": 6.0, "DATE": "2023-12-26" },
        { "BERAT_TOTAL": 7.0, "DATE": "2023-12-27" }
      ];

      // Simulating the backend response
      this.forecastData = mockData;

      // Prepare data for the chart
      this.chartData = mockData.map(item => item.BERAT_TOTAL); // Extract BERAT_TOTAL for the chart
      this.chartLabels = mockData.map(item => item.DATE);      // Extract DATE for the chart labels

      // Use nextTick to wait for the DOM to update before rendering the chart
      nextTick(() => {
        this.renderChart();
      });
    },

    // Render the Chart.js chart
    renderChart() {
      const ctx = document.getElementById('forecastChart').getContext('2d');

      // If the chart already exists, destroy it and create a new one
      if (this.chartInstance) {
        this.chartInstance.destroy();
      }

      // Create new chart instance
      this.chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: this.chartLabels,  // Labels (dates)
          datasets: [{
            label: 'BERAT_TOTAL',
            data: this.chartData,     // Total weight values (BERAT_TOTAL)
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
</style>
