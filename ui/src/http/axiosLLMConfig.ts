import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'http://instructlab.mhsb7.sandbox2006.opentlc.com:443',
  timeout: 3000, // 60 seconds
});

export default axiosInstance;