import axios from 'axios';

export const AXIOS_AGENTS_IP= 'http://bastion.9jk6c.sandbox1471.opentlc.com:8002'

const axiosInstance = axios.create({
  baseURL: 'http://bastion.9jk6c.sandbox1471.opentlc.com:8002',
  timeout: 300000, // 300 seconds
});

export default axiosInstance;