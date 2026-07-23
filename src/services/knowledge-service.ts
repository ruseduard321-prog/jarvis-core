import { apiClient } from "@/services/api-client";
import { API_ENDPOINTS } from "@/constants";
import type { ApiResponse, KnowledgeListResponse, Document } from "@/types";

/**
 * Knowledge Service
 * Handles all knowledge base / document API operations
 */

export const knowledgeService = {
  /**
   * List all knowledge documents
   */
  async listDocuments(): Promise<ApiResponse<KnowledgeListResponse>> {
    return apiClient.get(API_ENDPOINTS.KNOWLEDGE.LIST);
  },

  /**
   * Get a document by ID
   */
  async getDocument(documentId: string): Promise<ApiResponse<Document>> {
    return apiClient.get(API_ENDPOINTS.KNOWLEDGE.GET(documentId));
  },

  /**
   * Delete a document
   */
  async deleteDocument(documentId: string): Promise<ApiResponse<void>> {
    return apiClient.delete(API_ENDPOINTS.KNOWLEDGE.DELETE(documentId));
  },

  /**
   * Upload a document
   * @param file - File to upload
   * @param title - Optional document title
   * @param namespace - Document namespace/category
   * @param tags - Optional tags for the document
   */
  async uploadDocument(
    file: File,
    options?: {
      title?: string;
      namespace?: string;
      tags?: string[];
    }
  ): Promise<ApiResponse<unknown>> {
    const formData = new FormData();
    formData.append("file", file);
    
    if (options?.title) {
      formData.append("title", options.title);
    }
    if (options?.namespace) {
      formData.append("namespace", options.namespace);
    }
    if (options?.tags?.length) {
      formData.append("tags", JSON.stringify(options.tags));
    }

    return apiClient.post(API_ENDPOINTS.KNOWLEDGE.UPLOAD, formData, {
      headers: {
        // Let browser set Content-Type with boundary for multipart/form-data
      },
    });
  },

  /**
   * Search documents by query (client-side filtering)
   * TODO: Implement server-side search endpoint
   */
  searchDocuments(documents: Document[], query: string): Document[] {
    if (!query.trim()) {
      return documents;
    }

    const lowerQuery = query.toLowerCase();
    return documents.filter((doc) =>
      doc.title.toLowerCase().includes(lowerQuery) ||
      doc.source_identifier?.toLowerCase().includes(lowerQuery) ||
      doc.tags.some((tag) => tag.toLowerCase().includes(lowerQuery))
    );
  },

  /**
   * Filter documents by type (based on source_type)
   */
  filterDocuments(
    documents: Document[],
    filters?: {
      type?: string;
    }
  ): Document[] {
    if (!filters?.type || filters.type === "all") {
      return documents;
    }

    const filterType = filters.type.toLowerCase();
    return documents.filter((doc) =>
      doc.source_type?.toLowerCase().includes(filterType)
    );
  },
};
