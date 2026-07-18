import { ProtectedAppLayout } from "@/components/layout/protected-app-layout";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Jarvis - Application",
};

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ProtectedAppLayout>{children}</ProtectedAppLayout>;
}
