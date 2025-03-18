import apiClient from "./axiosConfig";

export const dprInstall = async (formId: string): Promise<any> => {
    try {      
      const response = await apiClient.post<{ response: any }>("/api/parser/start", { formId });  
      return response.data || ''; 
    } catch (error) {
      console.error("❌ Error starting parser:", error);
      return [];
    }
};
