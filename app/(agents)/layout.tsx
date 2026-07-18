import { AppShell } from "@/components/layout";

export default function AgentsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
