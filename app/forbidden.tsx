import { Ban } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function ForbiddenPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <Ban className="h-12 w-12 text-destructive mx-auto mb-4" />
        <h1 className="text-4xl font-bold mb-2">403</h1>
        <p className="text-lg font-semibold mb-2">Access Forbidden</p>
        <p className="text-muted-foreground mb-6">
          You don&apos;t have permission to access this resource.
        </p>
        <div className="flex gap-3">
          <Link href="/dashboard" className="flex-1">
            <Button fullWidth>Go to Dashboard</Button>
          </Link>
          <Link href="/" className="flex-1">
            <Button variant="outline" fullWidth>Go Home</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
