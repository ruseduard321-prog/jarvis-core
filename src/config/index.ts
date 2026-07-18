// Environment configuration
export const env = {
  API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  NODE_ENV: process.env.NODE_ENV || "development",
  IS_DEV: process.env.NODE_ENV === "development",
  IS_PROD: process.env.NODE_ENV === "production",
};

// Feature flags
export const features = {
  ENABLE_BETA: process.env.NEXT_PUBLIC_ENABLE_BETA === "true",
  ENABLE_ANALYTICS: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS !== "false",
  ENABLE_DEBUG: process.env.NEXT_PUBLIC_ENABLE_DEBUG === "true",
};

// App configuration
export const appConfig = {
  name: "Jarvis",
  description: "AI-powered platform",
  version: "0.1.0",
};
