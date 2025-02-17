import axios from 'axios';

export const AXIOS_LLM_IP= 'http://instructlab.dlvxc.sandbox1300.opentlc.com:443'
// export const AXIOS_LLM_IP= '/'

const axiosInstance = axios.create({
  baseURL: 'http://instructlab.dlvxc.sandbox1300.opentlc.com:443',
  // baseURL: '/',
  timeout: 300000, // 300 seconds
});

export default axiosInstance;
