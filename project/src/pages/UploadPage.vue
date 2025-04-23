<template>
  <div class="upload-page">
    <h1>Upload Data</h1>
    <div class="upload-container">
      <div class="target-inputs">
        <input type="text" v-model="targetProductId" placeholder="Enter Target Product ID" class="product-input" />
        <div class="target-details" v-if="parsedTarget">
          <p>KODE_BARANG: {{ parsedTarget.kodeBarang }}</p>
          <p>KLASIFIKASI_BARANG: {{ parsedTarget.klasifikasiBarang }}</p>
          <p>WARNA_BARANG: {{ parsedTarget.warnaBarang }}</p>
          <p>UKURAN_BARANG: {{ parsedTarget.ukuranBarang }}</p>
        </div>
      </div>

      <div class="upload-area" 
           @dragover.prevent 
           @drop.prevent="handleFileDrop"
           :class="{ 'dragging': isDragging }">
        <input 
          type="file" 
          ref="fileInput" 
          @change="handleFileSelect" 
          accept=".csv"
          class="file-input"
        >
        <div class="upload-content">
          <i class="fas fa-cloud-upload-alt"></i>
          <p>Drag and drop your CSV file here or click to browse</p>
          <p class="file-types">Supported format: CSV</p>
        </div>
      </div>

      <div v-if="selectedFile" class="file-info">
        <p>Selected file: {{ selectedFile.name }}</p>
        <button @click="uploadCSV" :disabled="!selectedFile || !isValidTarget || uploading" class="upload-button">
          {{ uploading ? 'Uploading...' : 'Upload and Process' }}
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="isProcessing" class="loading">
        <p>Processing your file... Please wait.</p>
        <div class="spinner"></div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="error">{{ error }}</div>
    </div>
  </div>
</template>

<script>
import { uploadCSV, checkTaskStatus, downloadFile } from '../services/api';

export default {
  name: 'UploadPage',
  data() {
    return {
      selectedFile: null,
      targetProductId: '',
      isDragging: false,
      uploading: false,
      isProcessing: false,
      error: null,
      taskId: null,
      statusCheckInterval: null,
      parsedTarget: null
    }
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

    handleFileSelect(event) {
      this.selectedFile = event.target.files[0];
      this.error = null;
    },

    handleFileDrop(event) {
      this.isDragging = false;
      this.selectedFile = event.dataTransfer.files[0];
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
          this.$router.push('/');
        } else if (status.error) {
          clearInterval(this.statusCheckInterval);
          this.error = 'Processing failed: ' + status.error;
          this.isProcessing = false;
        }
      } catch (error) {
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

          // Store the data in localStorage
          localStorage.setItem('forecastData', JSON.stringify(data));
          localStorage.setItem('forecastDataTimestamp', Date.now().toString());
        };

        reader.readAsText(blob);
      } catch (error) {
        this.error = 'Error processing downloaded file. Please try again.';
        this.isProcessing = false;
      }
    }
  },
  beforeUnmount() {
    if (this.statusCheckInterval) {
      clearInterval(this.statusCheckInterval);
    }
  }
}
</script>

<style scoped>
.upload-page {
  padding: 2rem;
}

.upload-container {
  max-width: 600px;
  margin: 0 auto;
}

.target-inputs {
  width: 100%;
  margin-bottom: 2rem;
}

.product-input {
  width: 100%;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
  margin-bottom: 1rem;
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

.upload-area {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  margin-bottom: 2rem;
}

.upload-area.dragging {
  border-color: #4CAF50;
  background-color: #f8f9fa;
}

.file-input {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  opacity: 0;
  cursor: pointer;
}

.upload-content {
  color: #666;
}

.upload-content i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #4CAF50;
}

.file-types {
  font-size: 0.9rem;
  color: #999;
  margin-top: 0.5rem;
}

.file-info {
  margin-top: 1rem;
  text-align: center;
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
  color: #e74c3c;
  margin: 20px 0;
  padding: 15px;
  background-color: #ffebee;
  border-radius: 8px;
  text-align: center;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 