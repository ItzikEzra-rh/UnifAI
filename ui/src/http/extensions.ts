import apiClient from "./axiosConfig";

export const fetchExtensions = async (): Promise<any> => {
  try {
    const response = await apiClient.get<{ data: any }>("/api/extensions/");
    return response.data || [];
  } catch (error) {
    console.error("Error fetching extensions:", error);
    return [];
  }
};
