import { AppShell } from "@/components/layout";

export default function WorkflowsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
