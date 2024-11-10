import axios from 'axios';

export const AXIOS_LLM_IP= 'http://instructlab.jf42w.sandbox1115.opentlc.com:443'

const axiosInstance = axios.create({
  baseURL: 'http://instructlab.jf42w.sandbox1115.opentlc.com:443',
  timeout: 10000, // 100 seconds
});

export default axiosInstance;