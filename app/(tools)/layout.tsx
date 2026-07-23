import { AppShell } from "@/components/layout";

export default function ToolsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
