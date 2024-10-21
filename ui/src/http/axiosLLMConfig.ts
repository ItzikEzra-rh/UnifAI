import axios from 'axios';

export const AXIOS_LLM_IP= 'http://instructlab.sdn5r.sandbox429.opentlc.com:443'

const axiosInstance = axios.create({
  baseURL: 'http://instructlab.sdn5r.sandbox429.opentlc.com:443',
  timeout: 10000, // 10 seconds
});

export default axiosInstance;