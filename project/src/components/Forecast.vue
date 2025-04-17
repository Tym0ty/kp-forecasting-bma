<template>
  <div class="container">
    <h1>Time Series Forecasting</h1>
    <!-- File input for CSV upload -->
    <input type="file" class="file-input" @change="handleFileUpload" accept=".csv" />
    
    <!-- Forecast Image Display -->
    <div v-if="forecastImage" class="result">
      <h3>Forecast Result</h3>
      <img :src="forecastImage" alt="Forecast Image" />
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
            <td>{{ data.time }}</td>
            <td>{{ data.forecast }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TimeSeriesForecast',
  data() {
    return {
      file: null,
      forecastImage: null,
      forecastData: []
    };
  },
  methods: {
    // Handle file upload
    handleFileUpload(event) {
      const file = event.target.files[0];
      if (file) {
        this.uploadCSV(file);
      }
    },

    // Upload CSV file to the backend
    async uploadCSV(file) {
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch('http://localhost:5000/forecast', {
          method: 'POST',
          body: formData
        });
        const data = await response.json();

        if (data.image && data.forecast) {
          this.forecastImage = data.image;  // URL for forecast image
          this.forecastData = data.forecast;  // Array of forecasted data
        } else {
          alert("Error: Could not retrieve forecast data.");
        }
      } catch (error) {
        alert("Error uploading file: " + error.message);
      }
    }
  }
};
</script>

<style scoped>
/* Add styles here */

body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
  background-color: #f4f4f9;
}

.container {
  width: 80%;
  margin: 0 auto;
  padding: 30px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

h1 {
  text-align: center;
  color: #333;
}

.file-input {
  display: block;
  margin: 20px auto;
  padding: 10px;
  background-color: #4CAF50;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}

.file-input:hover {
  background-color: #45a049;
}

.result {
  text-align: center;
  margin-top: 20px;
}

.result img {
  width: 80%;
  height: auto;
  border-radius: 8px;
}

.data-table {
  width: 100%;
  margin-top: 20px;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 8px;
  text-align: center;
  border: 1px solid #ddd;
}

.data-table th {
  background-color: #4CAF50;
  color: white;
}

.data-table tr:nth-child(even) {
  background-color: #f2f2f2;
}
</style>
