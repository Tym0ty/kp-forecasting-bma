<template>
  <div class="upload-page">
    <h1>Upload Data</h1>
    <div class="upload-container">
      <div class="upload-area" 
           @dragover.prevent 
           @drop.prevent="handleFileDrop"
           :class="{ 'dragging': isDragging }">
        <input 
          type="file" 
          ref="fileInput" 
          @change="handleFileSelect" 
          accept=".csv, .xlsx, .xls"
          class="file-input"
        >
        <div class="upload-content">
          <i class="fas fa-cloud-upload-alt"></i>
          <p>Drag and drop your CSV or Excel file here or click to browse</p>
          <p class="file-types">Supported formats: CSV, XLSX, XLS</p>
        </div>
      </div>

      <div v-if="selectedFile" class="file-info">
        <p>Selected file: {{ selectedFile.name }}</p>
        <button @click="uploadFile" class="upload-button" :disabled="uploading">
          {{ uploading ? 'Uploading...' : 'Upload' }}
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
import * as XLSX from 'xlsx';

export default {
  name: 'UploadPage',
  data() {
    return {
      selectedFile: null,
      isDragging: false,
      uploading: false,
      isProcessing: false,
      error: null
    }
  },
  methods: {
    handleFileSelect(event) {
      this.selectedFile = event.target.files[0];
      this.error = null;
    },

    handleFileDrop(event) {
      this.isDragging = false;
      this.selectedFile = event.dataTransfer.files[0];
      this.error = null;
    },

    async uploadFile() {
      if (!this.selectedFile) {
        this.error = 'Please select a file';
        return;
      }

      const allowedTypes = [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      ];
      const allowedExtensions = ['.csv', '.xlsx', '.xls'];
      const fileName = this.selectedFile.name.toLowerCase();
      const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
      if (!allowedTypes.includes(this.selectedFile.type) && !hasValidExtension) {
        this.error = 'Invalid file type. Please upload a CSV or Excel file.';
        return;
      }

      this.uploading = true;
      this.error = null;

      try {
        // Read and process file before upload
        const processedCsv = await this.processFile(this.selectedFile);

        // Send processed CSV as a Blob
        const formData = new FormData();
        formData.append('file', new Blob([processedCsv], { type: 'text/csv' }), 'processed.csv');

        const response = await fetch('http://localhost:8000/upload/', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error('Upload failed');
        }

        this.$router.push('/');
      } catch (err) {
        this.error = 'Failed to upload file. Please try again.';
      } finally {
        this.uploading = false;
      }
    },

    async processFile(file) {
      // Returns processed CSV string
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          let data, ws, jsonData;
          const ext = file.name.split('.').pop().toLowerCase();
          if (ext === 'csv') {
            // Parse CSV
            data = e.target.result;
            ws = XLSX.read(data, { type: 'string' }).Sheets;
            const sheetName = Object.keys(ws)[0];
            jsonData = XLSX.utils.sheet_to_json(ws[sheetName]);
          } else {
            // Parse Excel
            data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            const sheetName = workbook.SheetNames[0];
            jsonData = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName]);
          }

          // Process data
          const processed = jsonData.map(row => {
            // Parse TANGGAL
            let tanggal = row['TANGGAL'];
            // let dateObj; // Remove unused variable
            if (typeof tanggal === 'string') {
              // Try to parse with format MM/DD/YYYY HH:mm:ss
              const [datePart, timePart] = tanggal.split(' ');
              const [month, day, year] = datePart.split('/');
              const [hour = 0, minute = 0, second = 0] = (timePart || '0:0:0').split(':');
              // const dateObj = new Date( // Remove unused variable
              //   Number(year), Number(month) - 1, Number(day),
              //   Number(hour), Number(minute), Number(second)
              // );
              // No need to assign dateObj since it's not used
            } else if (tanggal instanceof Date) {
              // const dateObj = tanggal; // Remove unused variable
            } else {
              // const dateObj = new Date(tanggal); // Remove unused variable
            }

            // Remove MATCH, BULAN, TAHUN columns
            // eslint-disable-next-line no-unused-vars
            const { MATCH: _MATCH, BULAN: _BULAN, TAHUN: _TAHUN, ...rest } = row;
            return rest;
          });

          // Convert to CSV
          const csv = XLSX.utils.sheet_to_csv(XLSX.utils.json_to_sheet(processed));
          resolve(csv);
        };

        const ext = file.name.split('.').pop().toLowerCase();
        if (ext === 'csv') {
          reader.readAsText(file);
        } else {
          reader.readAsArrayBuffer(file);
        }
      });
    }
  }
}
</script>

<style scoped>
.upload-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

h1 {
  text-align: center;
  color: #333;
}

.upload-container {
  background: #f9f9f9;
  border: 1px dashed #ccc;
  border-radius: 8px;
  padding: 20px;
  margin-top: 20px;
}

.upload-area {
  border: 2px dashed #007bff;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: background 0.3s;
}

.upload-area.dragging {
  background: #e9f5ff;
}

.file-input {
  display: none;
}

.upload-content {
  color: #007bff;
}

.upload-content i {
  font-size: 48px;
  margin-bottom: 10px;
}

.file-types {
  font-size: 12px;
  color: #666;
}

.file-info {
  margin-top: 20px;
  text-align: center;
}

.upload-button {
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 10px 20px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.3s;
}

.upload-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  margin-top: 20px;
}

.spinner {
  border: 4px solid rgba(0, 123, 255, 0.1);
  border-left-color: #007bff;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  color: red;
  margin-top: 20px;
  text-align: center;
}
</style>