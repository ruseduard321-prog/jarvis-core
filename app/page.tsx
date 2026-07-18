import Link from "next/link";
import { Container } from "@/components/common";

export default function Home() {
  return (
    <Container className="py-20">
      <div className="flex flex-col items-center justify-center min-h-[70vh]">
        <div className="text-center space-y-6">
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight">
            Welcome to <span className="text-primary">Jarvis</span>
          </h1>
          <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl">
            An intelligent AI-powered platform for productivity and automation
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-6">
            <Link
              href="/chat"
              className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 font-medium transition-all"
            >
              Start Chatting
            </Link>
            <Link
              href="/dashboard"
              className="px-6 py-3 border border-input rounded-lg hover:bg-muted font-medium transition-all"
            >
              Go to Dashboard
            </Link>
          </div>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-3xl">
          <div className="p-6 rounded-lg border bg-card space-y-2">
            <h3 className="font-semibold">AI Chat</h3>
            <p className="text-sm text-muted-foreground">
              Have intelligent conversations powered by advanced AI
            </p>
          </div>
          <div className="p-6 rounded-lg border bg-card space-y-2">
            <h3 className="font-semibold">Knowledge Base</h3>
            <p className="text-sm text-muted-foreground">
              Manage and organize your documents and information
            </p>
          </div>
          <div className="p-6 rounded-lg border bg-card space-y-2">
            <h3 className="font-semibold">Automation</h3>
            <p className="text-sm text-muted-foreground">
              Automate workflows with tools and agents
            </p>
          </div>
        </div>
      </div>
    </Container>
  );
}
