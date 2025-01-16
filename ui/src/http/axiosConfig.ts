import axios from 'axios';

const axiosInstance = axios.create({
  //baseURL: 'http://127.0.0.1:13456',
  baseURL: 'http://genie-be:8080',
  timeout: 20000, // 20 seconds
});

export default axiosInstance;
