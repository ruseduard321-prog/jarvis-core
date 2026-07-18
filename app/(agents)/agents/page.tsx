import { PlaceholderPage } from "@/components/common/placeholder-page";
import { Zap } from "lucide-react";

export default function AgentsPage() {
  return (
    <PlaceholderPage
      title="AI Agents"
      description="Create and manage autonomous AI agents. Agent builder interface coming soon."
      icon={<Zap className="h-12 w-12 text-muted-foreground" />}
    />
  );
}
