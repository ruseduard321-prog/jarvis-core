import { PlaceholderPage } from "@/components/common/placeholder-page";
import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <PlaceholderPage
      title="Settings"
      description="Manage your account, workspace, and preferences."
      icon={<Settings className="h-12 w-12 text-muted-foreground" />}
    />
  );
}
