import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const uploadCSV = async (file, targetProductId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('target_product_id', targetProductId);

  const response = await axios.post(`${API_BASE_URL}/upload/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });

  return response.data;
};

export const checkTaskStatus = async (taskId) => {
  const response = await axios.get(`${API_BASE_URL}/task-status/${taskId}/`);
  return response.data;
};

export const downloadFile = async (filename) => {
  const response = await axios.get(`${API_BASE_URL}/download/${filename}/`, {
    responseType: 'blob'
  });
  return response.data;
};

export default {
  uploadCSV,
  checkTaskStatus,
  downloadFile
}; 