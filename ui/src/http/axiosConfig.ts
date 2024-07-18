import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'http://your-api-base-url.com',
});

export default axiosInstance;