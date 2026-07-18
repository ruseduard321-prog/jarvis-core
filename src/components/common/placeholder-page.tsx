/**
 * Placeholder Page Component
 * Reusable component for all placeholder pages
 */

import { EmptyState } from "@/components/ui";
import { AlertCircle } from "lucide-react";

interface PlaceholderPageProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
}

export function PlaceholderPage({
  title,
  description,
  icon = <AlertCircle className="h-12 w-12" />,
}: PlaceholderPageProps) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <EmptyState
        icon={icon}
        title={title}
        description={description}
      />
    </div>
  );
}
