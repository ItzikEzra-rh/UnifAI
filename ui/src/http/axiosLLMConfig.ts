import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'http://instructlab.sdn5r.sandbox429.opentlc.com:443',
  timeout: 10000, // 10 seconds
});

export default axiosInstance;