import axios, { AxiosError } from "axios";
interface APIErrorResponse {
  error?: string; // Mark `error` as optional since it may not always exist
}

const axiosInstance = axios.create({
  baseURL: 'http://127.0.0.1:13456',
  // baseURL: '/',
  timeout: 20000, // 20 seconds
});

axiosInstance.interceptors.response.use(
  (response) => response, // If response is OK, just return it
  (error: AxiosError) => {
    console.error("API Error:", error);

    // Default error message
    let errorMsg = "Failed to fetch data. Please try again.";

    // Cast error.response.data to our custom type
    const errorData = error.response?.data as APIErrorResponse;

    if (errorData?.error) {
      errorMsg = errorData.error;
    }

    return Promise.reject(new Error(errorMsg)); // Reject with cleaned-up error message
  }
);

export default axiosInstance;