import axios from 'axios';

const API_BASE_URL = 'http://localhost:8001'; // Updated port to 8001

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadCSV = async (file, targetProductId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('target_product_id', targetProductId);
  
  try {
    const response = await api.post('/upload-csv/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error uploading CSV:', error);
    throw error;
  }
};

export const checkTaskStatus = async (taskId) => {
  try {
    const response = await api.get(`/task-status/${taskId}`);
    return response.data;
  } catch (error) {
    console.error('Error checking task status:', error);
    throw error;
  }
};

export const downloadFile = async (filename) => {
  try {
    const response = await api.get(`/download/${filename}`, {
      responseType: 'blob'
    });
    return response.data;
  } catch (error) {
    console.error('Error downloading file:', error);
    throw error;
  }
};

export default api; 