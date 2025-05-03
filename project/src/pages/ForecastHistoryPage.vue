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
          <tr v-for="row in filteredHistory" :key="row.id" class="history-row">
            <td>{{ row.id }}</td>
            <td>{{ row.product_id }}</td>
            <td>{{ formatDate(row.date_start) }}</td>
            <td>{{ formatDate(row.date_end) }}</td>
            <td>{{ formatDate(row.timestamp) }}</td>
            <td>
              <div class="action-buttons">
                <button 
                  class="view-button" 
                  @click="toggleForecastView(row)"
                  title="View forecast data"
                >
                  <svg class="view-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                    <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                  </svg>
                  View
                </button>
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
              </div>
            </td>
          </tr>
          <!-- Graph row -->
          <tr v-if="selectedRow" class="forecast-details-row">
            <td colspan="6">
              <div class="forecast-controls">
                <h3>Forecast and Real Data</h3>
                <div class="view-selectors">
                  <select v-model="forecastPeriod" class="forecast-period-select" @change="updateForecastView">
                    <option value="year">Year View</option>
                    <option value="month">Month View</option>
                  </select>
                  <select 
                    v-if="forecastPeriod === 'month'" 
                    v-model="selectedMonth" 
                    class="month-select" 
                    @change="updateForecastView"
                  >
                    <option v-for="month in months" :key="month.value" :value="month.value">
                      {{ month.label }}
                    </option>
                  </select>
                </div>
              </div>
              <canvas :ref="`forecastCanvas-${selectedRow.id}`" width="400" height="200"></canvas>
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
import { nextTick } from 'vue'
import Chart from 'chart.js/auto'

export default {
  name: 'ForecastHistoryPage',
  data() {
    return {
      loading: false,
      error: null,
      history: [],
      selectedRow: null,
      loadingForecast: false,
      forecastError: null,
      forecastData: [],
      originalData: [],
      realData: [],
      chartData: [],
      chartLabels: [],
      chartInstance: null,
      currentPage: 1,
      itemsPerPage: 10,
      forecastPeriod: 'year', // Default to Year View
      selectedMonth: '01', // Default to January
      months: [
        { value: '01', label: 'January' },
        { value: '02', label: 'February' },
        { value: '03', label: 'March' },
        { value: '04', label: 'April' },
        { value: '05', label: 'May' },
        { value: '06', label: 'June' },
        { value: '07', label: 'July' },
        { value: '08', label: 'August' },
        { value: '09', label: 'September' },
        { value: '10', label: 'October' },
        { value: '11', label: 'November' },
        { value: '12', label: 'December' },
      ],
    };
  },
  computed: {
    filteredHistory() {
      return this.history; // Apply any filtering logic here if needed
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
    
    async toggleForecastView(row) {
      console.log('toggleForecastView called for row:', row);

      if (this.selectedRow && this.selectedRow.id === row.id) {
        // If clicking the same row, close it
        this.selectedRow = null;
        this.forecastData = [];
        this.realData = [];
        if (this.chartInstance) {
          this.chartInstance.destroy();
          this.chartInstance = null;
        }
        return;
      }

      this.selectedRow = row;
      console.log('Selected row:', this.selectedRow);
      this.loadingForecast = true;
      this.forecastError = null;
      this.currentPage = 1;

      try {
        const filename = row.csv_path.split('/').pop();
        const response = await axios.get(`http://localhost:8000/download/${filename}`, {
          responseType: 'text',
        });
        console.log('CSV data fetched:', response.data);

        // Parse CSV data
        const csvData = response.data;
        const lines = csvData.split('\n');
        const headers = lines[0].split(',');

        // Process CSV data into array of objects
        this.originalData = [];
        for (let i = 1; i < lines.length; i++) {
          if (lines[i].trim() === '') continue;

          const values = lines[i].split(',');
          const entry = {};

          for (let j = 0; j < headers.length; j++) {
            entry[headers[j].trim()] = values[j] ? values[j].trim() : '';
          }

          this.originalData.push(entry);
        }

        // Fetch real data
        const realData = await this.fetchRealData(
          row.product_id,
          row.date_start,
          row.date_end
        );

        // Store real data
        this.realData = realData.map(item => ({
          date: new Date(item.date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }),
          value: item.value,
        }));

        console.log('Real Data:', this.realData);

        // Initial update of the view
        this.updateForecastView();

        // Wait for the DOM to update, then render the chart
        await nextTick();
        this.renderChart();
      } catch (err) {
        this.forecastError = `Failed to load forecast data: ${err.message}`;
        console.error('Forecast data error:', err);
      } finally {
        this.loadingForecast = false;
      }
    },
    
    updateForecastView() {
      if (!this.originalData.length) return;

      if (this.forecastPeriod === 'year') {
        // Process monthly data for the chart
        const monthlyData = {};
        this.originalData.forEach(item => {
          const date = new Date(item.TANGGAL);
          const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;

          if (!monthlyData[monthKey]) {
            monthlyData[monthKey] = {
              total: 0,
              count: 0,
            };
          }

          monthlyData[monthKey].total += parseFloat(item.TOTAL_JUMLAH || 0);
          monthlyData[monthKey].count += 1;
        });

        const monthlyArray = Object.entries(monthlyData)
          .map(([date, data]) => ({
            TANGGAL: date,
            TOTAL_JUMLAH: data.total, // Use the summed value
          }))
          .sort((a, b) => a.TANGGAL.localeCompare(b.TANGGAL));

        this.chartData = monthlyArray.map(item => parseFloat(item.TOTAL_JUMLAH));
        this.chartLabels = monthlyArray.map(item => {
          const [year, month] = item.TANGGAL.split('-');
          return new Date(parseInt(year), parseInt(month) - 1).toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
        });
      } else if (this.forecastPeriod === 'month') {
        // Filter data for the selected month
        const filteredData = this.originalData.filter(item => {
          const date = new Date(item.TANGGAL);
          return String(date.getMonth() + 1).padStart(2, '0') === this.selectedMonth;
        });

        this.chartData = filteredData.map(item => parseFloat(item.TOTAL_JUMLAH || 0));
        this.chartLabels = filteredData.map(item => {
          const date = new Date(item.TANGGAL);
          return date.toLocaleDateString('en-US', { day: 'numeric' });
        });
      }

      console.log('Chart Labels:', this.chartLabels);

      // Re-render the chart
      this.renderChart();
    },

    renderChart() {
      console.log('Rendering chart for row:', this.selectedRow);
      if (!this.selectedRow) return;

      const forecastCanvasRef = `forecastCanvas-${this.selectedRow.id}`;
      const forecastCanvasElement = this.$refs[forecastCanvasRef];
      console.log('Forecast Canvas element:', forecastCanvasElement);

      if (!forecastCanvasElement) {
        console.error(`Forecast canvas element with ref "${forecastCanvasRef}" not found`);
        return;
      }

      const forecastCtx = forecastCanvasElement.getContext('2d');
      if (!forecastCtx) {
        console.error('Context for forecast canvas not found');
        return;
      }

      if (this.chartInstance) {
        this.chartInstance.destroy();
      }

      // Extract real data labels and values directly from the realData array
      const realDataLabels = this.realData.map(item => item.date);
      const realDataValues = this.realData.map(item => item.value);

      console.log('Real Data Labels:', realDataLabels);
      console.log('Real Data Values:', realDataValues);

      this.chartInstance = new Chart(forecastCtx, {
        type: 'line',
        data: {
          labels: this.chartLabels, // Forecasted data labels
          datasets: [
            {
              label: 'Forecasted Data',
              data: this.chartData,
              borderColor: '#4CAF50', // Green line
              backgroundColor: 'rgba(76, 175, 80, 0.2)',
              fill: true,
              tension: 0.4,
            },
            {
              label: 'Real Data',
              data: realDataValues,
              borderColor: '#2196F3', // Blue line
              backgroundColor: 'rgba(33, 150, 243, 0.2)',
              fill: false,
              tension: 0.4,
            },
          ],
        },
        options: {
          responsive: true,
          scales: {
            x: {
              type: 'category',
              title: {
                display: true,
                text: this.forecastPeriod === 'year' ? 'Month' : 'Date',
              },
            },
            y: {
              title: {
                display: true,
                text: this.forecastPeriod === 'year' ? 'Monthly Average' : 'Daily Value',
              },
            },
          },
        },
      });
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
    
    async fetchRealData(productId, startDate, endDate) {
      try {
        const response = await axios.get(`http://localhost:8000/train-data/${productId}`, {
          params: {
            start_date: startDate,
            end_date: endDate,
          },
        });
        console.log('Real data fetched:', response.data);

        // Aggregate real data by summing the JUMLAH values for each unique date
        const aggregatedData = {};
        response.data.forEach(item => {
          const date = item.TANGGAL;
          const jumlah = parseFloat(item.JUMLAH || 0);

          if (!aggregatedData[date]) {
            aggregatedData[date] = 0;
          }

          aggregatedData[date] += jumlah; // Sum the JUMLAH values for the same date
        });

        // Convert aggregated data into an array
        const realData = Object.entries(aggregatedData).map(([date, total]) => ({
          date,
          value: total, // Use the summed value
        }));

        console.log('Aggregated Real Data:', realData);
        return realData;
      } catch (err) {
        console.error('Error fetching real data:', err);
        return [];
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

.action-buttons {
  display: flex;
  gap: 8px;
}

.download-button,
.view-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.download-button {
  background-color: #4CAF50;
}

.download-button:hover {
  background-color: #45a049;
}

.view-button {
  background-color: #2196F3;
}

.view-button:hover {
  background-color: #0b7dda;
}

.download-icon,
.view-icon {
  width: 16px;
  height: 16px;
}

/* Forecast details styling */
.forecast-details-row {
  background-color: #f9f9f9 !important;
}

.forecast-details {
  padding: 20px;
  background-color: #f9f9f9;
  border-top: 1px solid #ddd;
}

.forecast-controls {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.view-selectors {
  display: flex;
  gap: 1rem;
}

.forecast-period-select,
.month-select {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
}

canvas {
  background-color: white;
  padding: 15px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  margin: 1rem 0;
  width: 100%;
}

.forecast-table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.forecast-table th,
.forecast-table td {
  padding: 10px 15px;
  border-bottom: 1px solid #ddd;
  text-align: left;
}

.forecast-table th {
  background-color: #4CAF50;
  color: white;
}

.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding: 10px;
  background-color: white;
  border-radius: 4px;
}

.page-size-select {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.pagination-buttons {
  display: flex;
  align-items: center;
  gap: 15px;
}

.pagination-button {
  padding: 6px 12px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.pagination-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.loading-forecast {
  text-align: center;
  padding: 2rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>