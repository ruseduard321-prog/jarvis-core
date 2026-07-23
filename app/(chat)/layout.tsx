import { ProtectedAppLayout } from "@/components/layout/protected-app-layout";
import { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Chat - Jarvis",
  description: "Chat with your AI assistant",
};

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedAppLayout>{children}</ProtectedAppLayout>;
}
