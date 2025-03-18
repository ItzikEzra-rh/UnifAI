import axios from 'axios';

//export const AXIOS_LLM_IP= 'http://instructlab.jf42w.sandbox1115.opentlc.com:443'
// export const AXIOS_LLM_IP= '/'
export const AXIOS_LLM_IP= 'http://genie-ui-tag-ai--runtime-int.apps.stc-ai-e1-pp.imap.p1.openshiftapps.com/'

const axiosInstance = axios.create({
  //baseURL: 'http://instructlab.jf42w.sandbox1115.opentlc.com:443',
  baseURL: '/',
  timeout: 300000, // 300 seconds
});

export default axiosInstance;
