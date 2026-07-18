import { AppShell } from "@/components/layout";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Jarvis - Application",
};

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
