import { PlaceholderPage } from "@/components/common/placeholder-page";
import { Workflow } from "lucide-react";

export default function WorkflowsPage() {
  return (
    <PlaceholderPage
      title="Workflows"
      description="Design and manage automation workflows. Visual workflow builder coming soon."
      icon={<Workflow className="h-12 w-12 text-muted-foreground" />}
    />
  );
}
