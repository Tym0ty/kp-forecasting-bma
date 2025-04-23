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

      this.uploading = true;
      this.error = null;

      try {
        const formData = new FormData();
        formData.append('file', this.selectedFile);

        const response = await fetch('http://localhost:8000/upload/', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error('Upload failed');
        }

        // Handle successful upload
        this.$router.push('/');
      } catch (err) {
        this.error = 'Failed to upload file. Please try again.';
      } finally {
        this.uploading = false;
      }
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
  background-color: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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