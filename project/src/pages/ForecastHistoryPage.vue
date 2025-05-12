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
                <!-- View selectors here -->
                <div class="view-selectors">
                  <label>
                    <select v-model="forecastPeriod" class="forecast-period-select" @change="updateForecastView">
                      <option value="year">Year View (Monthly)</option>
                      <option value="month">Month View (Daily)</option>
                    </select>
                  </label>
                  <label v-if="forecastPeriod === 'month'">
                    <select v-model="selectedMonth" class="month-select" @change="updateForecastView">
                      <option v-for="month in months" :key="month.value" :value="month.value">
                        {{ month.label }}
                      </option>
                    </select>
                  </label>
                </div>
                <!-- Only one canvas for the joined chart -->
                <canvas :ref="`forecastCanvas-${selectedRow.id}`" width="400" height="200"></canvas>
              </div>
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
      forecastChartInstance: null,
      realDataChartInstance: null,
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
      dailyForecastByMonth: {}, // { '01': [dailyDataForJan], '02': [dailyDataForFeb], ... }
      dailyRealByMonth: {}, // { '01': [dailyRealDataForJan], ... }
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
      this.loading = true;
      this.error = null;
      try {
        const res = await axios.get('http://localhost:8000/forecast-history/');
        this.history = Array.isArray(res.data)
          ? res.data.map(item => {
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
              return item;
            })
          : [];
      } catch (err) {
        this.error = 'Failed to load forecast history. Please try again.';
      } finally {
        this.loading = false;
      }
    },

    async toggleForecastView(row) {
      if (this.selectedRow && this.selectedRow.id === row.id) {
        this.selectedRow = null;
        this.forecastData = [];
        this.realData = [];
        if (this.forecastChartInstance) {
          this.forecastChartInstance.destroy();
          this.forecastChartInstance = null;
        }
        if (this.realDataChartInstance) {
          this.realDataChartInstance.destroy();
          this.realDataChartInstance = null;
        }
        return;
      }

      this.selectedRow = row;
      this.loadingForecast = true;
      this.forecastError = null;

      try {
        const response = await axios.get(`http://localhost:8000/forecast-history/${row.id}`);
        let forecastArr = [];
        if (Array.isArray(response.data)) {
          forecastArr = response.data;
        } else if (Array.isArray(response.data.forecast)) {
          forecastArr = response.data.forecast;
        }
        this.originalData = forecastArr;

        this.chartLabels = this.originalData.map(item => item.TANGGAL);
        this.chartData = this.originalData.map(item => parseFloat(item.TOTAL_JUMLAH));
        this.renderChart();

        const forecastStart = this.originalData.length > 0 ? this.originalData[0].TANGGAL : row.date_start;
        const forecastEnd = this.originalData.length > 0 ? this.originalData[this.originalData.length - 1].TANGGAL : row.date_end;

        const realData = await this.fetchRealData(
          row.product_id,
          forecastStart,
          forecastEnd
        );

        this.realData = realData.map(item => ({
          date: new Date(item.date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }),
          value: item.value,
        }));

        this.dailyRealByMonth = {};
        this.realData.forEach(item => {
          const date = new Date(item.date);
          const month = String(date.getMonth() + 1).padStart(2, '0');
          if (!this.dailyRealByMonth[month]) {
            this.dailyRealByMonth[month] = [];
          }
          this.dailyRealByMonth[month].push({
            ...item,
            day: date.getDate(),
          });
        });

        this.updateForecastView();
        await nextTick();
        this.renderChart();
      } catch (err) {
        this.forecastError = `Failed to load forecast data: ${err.message}`;
      } finally {
        this.loadingForecast = false;
      }
    },

    updateForecastView() {
      if (!this.originalData.length) return;

      this.dailyForecastByMonth = {};
      this.originalData.forEach(item => {
        const date = new Date(item.TANGGAL);
        const month = String(date.getMonth() + 1).padStart(2, '0');
        if (!this.dailyForecastByMonth[month]) {
          this.dailyForecastByMonth[month] = [];
        }
        this.dailyForecastByMonth[month].push({
          ...item,
          day: date.getDate(),
        });
      });

      if (this.forecastPeriod === 'year') {
        const monthlyData = {};
        this.originalData.forEach(item => {
          const date = new Date(item.TANGGAL);
          const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          if (!monthlyData[monthKey]) {
            monthlyData[monthKey] = { total: 0, count: 0 };
          }
          monthlyData[monthKey].total += parseFloat(item.TOTAL_JUMLAH || 0);
          monthlyData[monthKey].count += 1;
        });

        const monthlyArray = Object.entries(monthlyData)
          .map(([date, data]) => ({
            TANGGAL: date,
            TOTAL_JUMLAH: data.total,
          }))
          .sort((a, b) => a.TANGGAL.localeCompare(b.TANGGAL));

        this.chartData = monthlyArray.map(item => parseFloat(item.TOTAL_JUMLAH));
        this.chartLabels = monthlyArray.map(item => {
          const [year, month] = item.TANGGAL.split('-');
          return new Date(parseInt(year), parseInt(month) - 1).toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
        });
      } else if (this.forecastPeriod === 'month') {
        const dailyData = this.dailyForecastByMonth[this.selectedMonth] || [];
        this.chartData = dailyData.map(item => parseFloat(item.TOTAL_JUMLAH || 0));
        this.chartLabels = dailyData.map(item => item.day.toString());
      }

      this.renderChart();
    },

    renderChart() {
      if (!this.selectedRow) return;

      const forecastCanvasRef = `forecastCanvas-${this.selectedRow.id}`;
      const forecastCanvasElement = this.$refs[forecastCanvasRef];

      if (!forecastCanvasElement) return;

      const forecastCtx = forecastCanvasElement.getContext('2d');
      if (!forecastCtx) return;

      if (this.forecastChartInstance) {
        this.forecastChartInstance.destroy();
      }

      // Prepare real data for the joined chart
      let realDataLabels = [];
      let realDataValues = [];

      if (this.forecastPeriod === 'year') {
        const monthlyRealData = {};
        this.realData.forEach(item => {
          const date = new Date(item.date);
          const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          if (!monthlyRealData[monthKey]) {
            monthlyRealData[monthKey] = 0;
          }
          monthlyRealData[monthKey] += item.value;
        });

        const sortedMonths = Object.keys(monthlyRealData).sort();
        realDataLabels = sortedMonths.map(monthKey => {
          const [year, month] = monthKey.split('-');
          return new Date(parseInt(year), parseInt(month) - 1).toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
        });
        realDataValues = sortedMonths.map(monthKey => monthlyRealData[monthKey]);
      } else {
        const dailyReal = this.dailyRealByMonth[this.selectedMonth] || [];
        realDataLabels = dailyReal.map(item => item.day.toString());
        realDataValues = dailyReal.map(item => item.value);
      }

      // Sync labels for both datasets
      let labels = this.chartLabels;
      let forecastData = this.chartData;
      let realData = labels.map(label => {
        let idx = realDataLabels.findIndex(realLabel => realLabel === label);
        return idx !== -1 ? realDataValues[idx] : 0;
      });

      this.forecastChartInstance = new Chart(forecastCtx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Forecasted Data',
              data: forecastData,
              borderColor: '#4CAF50',
              backgroundColor: 'rgba(76, 175, 80, 0.2)',
              fill: true,
              tension: 0.4,
            },
            {
              label: 'Real Data',
              data: realData,
              borderColor: '#2196F3',
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
                text: this.forecastPeriod === 'year' ? 'Monthly Total' : 'Daily Value',
              },
            },
          },
        },
      });
    },

    async downloadForecast(path) {
      try {
        const filename = path.split('/').pop();
        const response = await axios.get(`http://localhost:8000/download/${filename}`, {
          responseType: 'blob'
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);
      } catch (err) {
        this.error = `Failed to download forecast: ${err.message}`;
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
        return response.data.map(item => ({
          date: item.TANGGAL,
          value: parseFloat(item.JUMLAH || 0),
        }));
      } catch (err) {
        return [];
      }
    },

    formatDate(dateString) {
      if (!dateString) return 'N/A';
      try {
        const date = new Date(dateString);
        return date.toLocaleString();
      } catch (e) {
        return dateString;
      }
    }
  }
}
</script>