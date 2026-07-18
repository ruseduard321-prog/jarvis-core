import { AppShell } from "@/components/layout";

export default function KnowledgeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
