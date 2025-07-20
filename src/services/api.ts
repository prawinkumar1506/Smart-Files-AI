// import axios from "axios";
//
// // Default base URL (works for both SSR and browser)
// let baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
//
// // Client-side only: Listen for port updates from Electron
// if (typeof window !== 'undefined' && window.electronAPI) {
//   window.electronAPI.onBackendPort((event, port) => {
//     baseURL = `http://localhost:${port}`;
//     console.log(`Updated backend URL: ${baseURL}`);
//   });
// }
//
// const api = axios.create({
//   baseURL,
//   timeout: 30000,
// });
//
// // ... rest of ApiService class remains unchanged ...
//
// export interface IndexRequest {
//   folder_paths: string[]
// }
//
// export interface SearchRequest {
//   query: string
//   limit?: number
//   threshold?: number
// }
//
// export interface QueryRequest {
//   question: string
// }
//
// export class ApiService {
//   static async healthCheck() {
//     const response = await api.get("/health")
//     return response.data
//   }
//
//   static async indexFolders(request: IndexRequest) {
//     const response = await api.post("/api/index", request)
//     return response.data
//   }
//
//   static async getIndexStatus() {
//     const response = await api.get("/api/index/status")
//     return response.data
//   }
//
//   static async searchFiles(request: SearchRequest) {
//     const response = await api.post("/api/search", request)
//     return response.data
//   }
//
//   static async queryWithLLM(request: QueryRequest) {
//     const response = await api.post("/api/query", request)
//     return response.data
//   }
//
//   static async getFolders() {
//     const response = await api.get("/api/folders")
//     return response.data
//   }
//
//   static async getIndexedFiles() {
//     const response = await api.get("/api/files")
//     return response.data
//   }
//
//   static async removeFolder(folderId: number) {
//     const response = await api.delete(`/api/folders/${folderId}`)
//     return response.data
//   }
//
//   static async clearIndex() {
//     const response = await api.delete("/api/index/clear")
//     return response.data
//   }
// }

import axios from "axios";

// Default base URL (works for both SSR and browser)
let baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Client-side only: Listen for port updates from Electron
if (typeof window !== 'undefined' && window.electronAPI) {
  window.electronAPI.onBackendPort((event, port) => {
    baseURL = `http://localhost:${port}`;
    console.log(`Updated backend URL: ${baseURL}`);
  });
}

const api = axios.create({
  baseURL,
  timeout: 30000,
});

export interface IndexRequest {
    folder_paths: string[]
}

export interface SearchRequest {
    query: string
    limit?: number
    threshold?: number
}

export interface QueryRequest {
    question: string
}

export class ApiService {
    static async healthCheck() {
        const response = await api.get("/health")
        return response.data
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
        const response = await api.post("/api/query", request)
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
}
