import { PlaceholderPage } from "@/components/common/placeholder-page";
import { MessageSquare } from "lucide-react";

export default function ChatPage() {
  return (
    <PlaceholderPage
      title="Chat"
      description="Start a conversation with your AI assistant. Real-time chat interface coming soon."
      icon={<MessageSquare className="h-12 w-12 text-muted-foreground" />}
    />
  );
}
