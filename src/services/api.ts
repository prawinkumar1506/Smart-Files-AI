import axios from "axios";
import { tauriAPI } from "./tauriApi";

// Default base URL (works for both SSR and browser)
let baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL,
  timeout: 45000,
});

// Client-side only: Listen for port updates from Tauri
if (typeof window !== 'undefined') {
  tauriAPI.onBackendPort((port) => {
    baseURL = `http://localhost:${port}`;
    api.defaults.baseURL = baseURL;
    console.log(`Updated backend URL: ${baseURL}`);
  });
}

export interface IndexRequest {
  folder_paths: string[]
}

export interface SearchRequest {
  query: string
  limit?: number
  threshold?: number
}

export interface QueryRequest {
  question: string;
  session_id?: number;
  llm_provider?: string;
}

export interface OrganiseRequest {
  folder_id: number;
  dry_run?: boolean;
}

export interface ExecuteOrganiseRequest {
  folder_id: number;
  actions: any[];
  confirm?: boolean;
}

export interface CreateChatSessionRequest {
  session_name: string;
}

export interface Image {
  id: number;
  file_name: string;
  caption: string;
  file_size: string;
  date_created: string;
  date_indexed: string;
  format: string;
  resolution: string;
  tags: string[];
}

export class ApiService {
  static getApiBaseUrl() {
    return api.defaults.baseURL || baseURL;
  }

  static getImageContentUrl(imageId: number) {
    return `${ApiService.getApiBaseUrl()}/api/images/${imageId}/content`;
  }

  static async healthCheck() {
    const response = await api.get("/health")
    return response.data
  }

  static async getIndexedImages(): Promise<Image[]> {
    const response = await api.get("/api/images");
    if (!response.data.success) {
      throw new Error(response.data.message || 'Failed to fetch indexed images');
    }
    return response.data.images;
  }

  static async searchImages(query: string): Promise<Image[]> {
    const response = await api.post("/api/images/search", { query });
    if (!response.data.success) {
      throw new Error(response.data.message || 'Failed to search images');
    }
    return response.data.images;
  }

  static async renameImage(imageId: number, newName: string): Promise<boolean> {
    const response = await api.post("/api/images/rename", { image_id: imageId, new_name: newName });
    if (!response.data.success) {
      throw new Error(response.data.message || 'Failed to rename image');
    }
    return response.data.success;
  }

  static async deleteImage(imageId: number): Promise<boolean> {
    const response = await api.delete(`/api/images/${imageId}`);
    if (!response.data.success) {
      throw new Error(response.data.message || 'Failed to delete image');
    }
    return response.data.success;
  }

  static async indexFolders(request: IndexRequest) {
    const response = await api.post("/api/index", request)
    return response.data
  }

  static async getIndexStatus() {
    const response = await api.get("/api/index/status")
    return response.data
  }

  static async searchFiles(request: SearchRequest) {
    const response = await api.post("/api/search", request)
    return response.data
  }

  static async queryWithLLM(request: QueryRequest) {
    const llm_provider = localStorage.getItem("llm_provider") || "gemini";
    const response = await api.post("/api/query", {...request, llm_provider})
    return response.data
  }

  static async getFolders() {
    const response = await api.get("/api/folders")
    return response.data
  }

  static async getIndexedFiles() {
    const response = await api.get("/api/files")
    return response.data
  }

  static async removeFolder(folderId: number) {
    const response = await api.delete(`/api/folders/${folderId}`)
    return response.data
  }

  static async clearIndex() {
    const response = await api.delete("/api/index/clear")
    return response.data
  }

  static async getFolderHierarchy(rootId?: number) {
    const response = await api.get("/api/folders/hierarchy", {
      params: rootId ? { root_id: rootId } : {},
    });
    return response.data;
  }

  static async analyzeFolderForOrganisation(request: OrganiseRequest) {
    const response = await api.post("/api/organise/analyze", request);
    return response.data;
  }

  static async executeOrganisation(request: ExecuteOrganiseRequest) {
    const response = await api.post("/api/organise/execute", request);
    return response.data;
  }

  // Chat History
  static async createChatSession(request: CreateChatSessionRequest) {
    const response = await api.post("/api/chat/sessions", request);
    return response.data;
  }

  static async getChatSessions() {
    const response = await api.get("/api/chat/sessions");
    return response.data;
  }

  static async getChatMessages(sessionId: number) {
    const response = await api.get(`/api/chat/sessions/${sessionId}/messages`);
    return response.data;
  }

  static async deleteChatSession(sessionId: number) {
    const response = await api.delete(`/api/chat/sessions/${sessionId}`);
    return response.data;
  }

  static async generateChatName(message: string, sessionId: number) {
    const llm_provider = localStorage.getItem("llm_provider") || "gemini";
    const response = await api.post("/api/chat/generate-name", { message, session_id: sessionId, llm_provider });
    return response.data.session_name;
  }

  static async saveApiKey(key: string) {
    const response = await api.post("/api/settings/api-key", { key });
    return response.data;
  }

  static async getApiKey() {
    const response = await api.get("/api/settings/api-key");
    return response.data;
  }
}
