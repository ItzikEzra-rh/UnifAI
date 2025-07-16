import axios from 'axios';

export const AXIOS_AGENTS_IP= 'http://bastion.9jk6c.sandbox1471.opentlc.com:8003'

const axiosInstance = axios.create({
  baseURL: '/api2',
  timeout: 300000, // 300 seconds
});

export default axiosInstance;