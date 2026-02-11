import axios from "axios";

// API_BASE가 필요한 경우 auth.api.js와 비슷하게 import.meta.env 사용
// 여기서는 상대경로 '/api'가 proxy 설정 되어있다고 가정하거나, instance를 가져와 쓸 수 있음.
// 편의상 auth.api.js의 instance를 가져오거나, 또는 직접 axios 호출.
import instance from "./auth.api";

export const marketApi = {
  async getIndices() {
    try {
      const response = await instance.get("/assets/indices");
      return response.data;
    } catch (error) {
      console.error("Failed to fetch market indices:", error);
      return [];
    }
  },

  async getPreference() {
    try {
      const response = await instance.get("/users/preference/market");
      return response.data; // { indices: [...] }
    } catch (error) {
      return null;
    }
  },

  async updatePreference(indices) {
    return instance.post("/users/preference/market/save", { indices });
  },

  async searchStocks(query) {
    try {
      const response = await instance.get("/assets/search", { params: { q: query } });
      return response.data; // [{ name, code }, ...]
    } catch (error) {
      return [];
    }
  }
};