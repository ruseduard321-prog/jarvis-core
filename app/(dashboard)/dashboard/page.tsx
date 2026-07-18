import { PlaceholderPage } from "@/components/common/placeholder-page";
import { BarChart3 } from "lucide-react";

export default function DashboardPage() {
  return (
    <PlaceholderPage
      title="Dashboard"
      description="Your AI-powered dashboard. Coming soon with real-time insights and analytics."
      icon={<BarChart3 className="h-12 w-12 text-muted-foreground" />}
    />
  );
}
