import { Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function UnauthorizedPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <Lock className="h-12 w-12 text-destructive mx-auto mb-4" />
        <h1 className="text-4xl font-bold mb-2">401</h1>
        <p className="text-lg font-semibold mb-2">Unauthorized</p>
        <p className="text-muted-foreground mb-6">
          You need to be logged in to access this page.
        </p>
        <div className="flex gap-3">
          <Link href="/login" className="flex-1">
            <Button fullWidth>Sign In</Button>
          </Link>
          <Link href="/" className="flex-1">
            <Button variant="outline" fullWidth>Go Home</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
