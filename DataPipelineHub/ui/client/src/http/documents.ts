import apiClient from "./axiosConfig";

export const uploadDocument = async (data: any, mode: string): Promise<any> => {
    try {      
      const response = await apiClient.post<{ response: any }>("/api/dpr/install", { data: data, mode: mode });  
      return response.data || {}; 
    } catch (error) {
      console.error("❌ Error starting install:", error);
      return [];
    }
};


export const getDocuments = async (datasetId: string): Promise<any> => {
  try {
    const response = await apiClient.get<{ response: any }>("/api/dpr/getStats", { params: { id: datasetId} });
    return response.data || {};
  } catch (error) {
    console.error("Error fetching statistics:", error);
    return [];
  }
};
