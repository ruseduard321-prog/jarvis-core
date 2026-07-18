import { PlaceholderPage } from "@/components/common/placeholder-page";
import { BookOpen } from "lucide-react";

export default function KnowledgePage() {
  return (
    <PlaceholderPage
      title="Knowledge Base"
      description="Manage your knowledge base and documents. Document management interface coming soon."
      icon={<BookOpen className="h-12 w-12 text-muted-foreground" />}
    />
  );
}
