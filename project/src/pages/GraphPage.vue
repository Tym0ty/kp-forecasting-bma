<template>
  <div class="graph-page">
    <h1>Forecasting Results</h1>
    <div class="graph-container">
      <!-- Loading State -->
      <div v-if="loading" class="loading">
        <p>Loading forecast data... Please wait.</p>
        <div class="spinner"></div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="error">{{ error }}</div>

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
  name: 'GraphPage',
  data() {
    return {
      loading: false,
      error: null,
      originalData: [], // Store the complete original data
      forecastData: [], // This will be the filtered view for the table
      chartData: [],
      chartLabels: [],
      chartInstance: null,
      currentPage: 1,
      itemsPerPage: 10,
      forecastPeriod: localStorage.getItem('lastForecastPeriod') || 'month'
    };
  },
  computed: {
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
    forecastPeriod() {
      this.updateForecastView();
    }
  },
  async mounted() {
    await this.loadSavedData();
  },
  methods: {
    async loadSavedData() {
      // First try to load from localStorage
      const cachedData = localStorage.getItem('forecastData');
      const cachedTimestamp = localStorage.getItem('forecastDataTimestamp');
      const cacheExpiry = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

      if (cachedData && cachedTimestamp) {
        const timestamp = parseInt(cachedTimestamp);
        if (Date.now() - timestamp < cacheExpiry) {
          try {
            this.originalData = JSON.parse(cachedData);
            this.updateForecastView();
            return;
          } catch (e) {
            console.error('Error parsing cached data:', e);
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
            // Update cache
            this.updateCache(data);
          }
        }
      } catch (error) {
        console.error('Error loading recent data:', error);
      }
    },

    updateCache(data) {
      try {
        localStorage.setItem('forecastData', JSON.stringify(data));
        localStorage.setItem('forecastDataTimestamp', Date.now().toString());
      } catch (e) {
        console.error('Error caching data:', e);
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
        // For year view, show all data in the table
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
            monthlyData[monthKey] = {
              total: 0,
              count: 0
            };
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
  }
};
</script>

<style scoped>
.graph-page {
  padding: 2rem;
}

.graph-container {
  background-color: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  min-height: 400px;
}

.loading, .error {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  font-size: 1.2rem;
}

.error {
  color: #e74c3c;
}

.result {
  margin-top: 40px;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.forecast-period-select {
  width: 100%;
  max-width: 200px;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
  margin-bottom: 1rem;
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

.spinner {
  width: 50px;
  height: 50px;
  margin: 20px auto;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
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