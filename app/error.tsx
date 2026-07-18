"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
        <h1 className="text-3xl font-bold mb-2">500</h1>
        <p className="text-lg font-semibold mb-2">Server Error</p>
        <p className="text-muted-foreground mb-2">
          Something went wrong on our end. Our team has been notified.
        </p>
        {process.env.NODE_ENV === "development" && (
          <details className="mb-6 p-4 bg-muted/50 rounded-lg text-left">
            <summary className="cursor-pointer font-mono text-sm">Error details</summary>
            <pre className="mt-2 text-xs overflow-auto max-h-32 text-destructive">
              {error.message}
            </pre>
          </details>
        )}
        <div className="flex gap-3">
          <Button onClick={() => reset()} fullWidth>
            Try Again
          </Button>
          <Button variant="outline" onClick={() => (window.location.href = "/")} fullWidth>
            Go Home
          </Button>
        </div>
      </div>
    </div>
  );
}
