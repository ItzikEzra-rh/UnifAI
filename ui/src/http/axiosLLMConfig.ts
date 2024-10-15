import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'http://instructlab.t79zz.sandbox1904.opentlc.com:443',
  timeout: 10000, // 10 seconds
});

export default axiosInstance;