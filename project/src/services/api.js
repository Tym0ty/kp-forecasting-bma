import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000'; 

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false // Disable sending credentials
});

export const uploadCSV = async (file, targetProductId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('target_product_id', targetProductId);
  
  try {
    const response = await api.post('/upload-csv/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Accept': 'application/json',
      },
      maxRedirects: 5,
      validateStatus: status => status >= 200 && status < 400,
      timeout: 30000, // 30 second timeout
      responseType: 'json',
    });

    if (!response.data) {
      throw new Error('No response data received');
    }
    
    return response.data;
  } catch (error) {
    console.error('Error uploading CSV:', error);
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('Response data:', error.response.data);
      console.error('Response status:', error.response.status);
      console.error('Response headers:', error.response.headers);
    } else if (error.request) {
      // The request was made but no response was received
      console.error('No response received:', error.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('Error setting up request:', error.message);
    }
    throw error;
  }
};

export const checkTaskStatus = async (taskId) => {
  try {
    const response = await api.get(`/task-status/${taskId}/`, {
      headers: {
        'Accept': 'application/json'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error checking task status:', error);
    throw error;
  }
};

export const downloadFile = async (filename) => {
  try {
    const response = await api.get(`/download/${filename}/`, {
      responseType: 'blob',
      headers: {
        'Accept': 'application/octet-stream'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error downloading file:', error);
    throw error;
  }
};

export default api; 