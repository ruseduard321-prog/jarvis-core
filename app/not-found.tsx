import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <AlertTriangle className="h-12 w-12 text-yellow-600 mx-auto mb-4" />
        <h1 className="text-3xl font-bold mb-2">404</h1>
        <p className="text-lg font-semibold mb-2">Page Not Found</p>
        <p className="text-muted-foreground mb-6">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex gap-3">
          <Link href="/" className="flex-1">
            <Button fullWidth>Go Home</Button>
          </Link>
          <Link href="/dashboard" className="flex-1">
            <Button variant="outline" fullWidth>Dashboard</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
