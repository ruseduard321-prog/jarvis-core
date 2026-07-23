"use client";

import { useRef, useState } from "react";
import { Upload, AlertCircle, CheckCircle } from "lucide-react";
import { useKnowledgeUpload } from "@/hooks/use-knowledge";

/**
 * Upload Zone
 * Handles drag & drop and file picker for document uploads
 */
export function UploadZone() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle");
  const [uploadMessage, setUploadMessage] = useState("");

  const uploadMutation = useKnowledgeUpload();

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files?.length) {
      handleFiles(files);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = async (files: FileList) => {
    const file = files[0];
    if (!file) return;

    // Validate file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      setUploadStatus("error");
      setUploadMessage("File size must be less than 50MB");
      setTimeout(() => setUploadStatus("idle"), 3000);
      return;
    }

    setUploading(true);
    setUploadStatus("idle");

    try {
      await uploadMutation.mutateAsync({
        file,
        title: file.name,
        namespace: "default",
        tags: [],
      });

      setUploadStatus("success");
      setUploadMessage(`${file.name} uploaded successfully`);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      setTimeout(() => setUploadStatus("idle"), 3000);
    } catch (error) {
      setUploadStatus("error");
      setUploadMessage((error as Error).message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-3">
      {/* Upload Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative rounded-lg border-2 border-dashed transition-colors ${
          dragActive
            ? "border-blue-500 bg-blue-50 dark:bg-blue-900"
            : "border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileInput}
          disabled={uploading}
          className="hidden"
          accept=".pdf,.txt,.md,.docx,.csv,.json"
        />

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="w-full px-6 py-8 flex flex-col items-center justify-center gap-3 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Upload className={`h-8 w-8 ${uploading ? "text-gray-400" : "text-gray-600 dark:text-gray-400"}`} />
          <div className="text-center">
            <p className="font-medium text-gray-900 dark:text-white">
              {uploading ? "Uploading..." : "Drop your files here or click to browse"}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Supported: PDF, TXT, MD, DOCX, CSV, JSON (Max 50MB)
            </p>
          </div>
        </button>
      </div>

      {/* Status Message */}
      {uploadStatus !== "idle" && (
        <div
          className={`flex items-center gap-2 px-4 py-3 rounded-lg ${
            uploadStatus === "success"
              ? "bg-green-50 text-green-800 dark:bg-green-900 dark:text-green-200"
              : "bg-red-50 text-red-800 dark:bg-red-900 dark:text-red-200"
          }`}
        >
          {uploadStatus === "success" ? (
            <CheckCircle className="h-5 w-5 flex-shrink-0" />
          ) : (
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
          )}
          <p className="text-sm font-medium">{uploadMessage}</p>
        </div>
      )}
    </div>
  );
}
