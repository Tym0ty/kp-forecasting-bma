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