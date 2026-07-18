"use client";

import { ReactNode } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { useBoolean } from "@/hooks";

// Container component
function Container({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 ${className}`}>
      {children}
    </div>
  );
}

// Header component
export function Header({ children }: { children?: ReactNode }) {
  const [mobileMenuOpen, { toggle: toggleMobileMenu }] = useBoolean();

  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <Container className="flex items-center justify-between h-16">
        <Link href="/" className="font-bold text-xl">
          Jarvis
        </Link>

        <nav className="hidden md:flex items-center gap-6">
          <Link href="/" className="text-sm hover:text-primary transition-colors">
            Home
          </Link>
          <Link href="/chat" className="text-sm hover:text-primary transition-colors">
            Chat
          </Link>
          <Link href="/dashboard" className="text-sm hover:text-primary transition-colors">
            Dashboard
          </Link>
          <Link href="/settings" className="text-sm hover:text-primary transition-colors">
            Settings
          </Link>
        </nav>

        <button
          onClick={toggleMobileMenu}
          className="md:hidden p-2 hover:bg-muted rounded"
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        {children}
      </Container>

      {mobileMenuOpen && (
        <nav className="md:hidden border-t bg-card p-4 space-y-2">
          <Link href="/" className="block px-2 py-2 hover:bg-muted rounded">
            Home
          </Link>
          <Link href="/chat" className="block px-2 py-2 hover:bg-muted rounded">
            Chat
          </Link>
          <Link href="/dashboard" className="block px-2 py-2 hover:bg-muted rounded">
            Dashboard
          </Link>
          <Link href="/settings" className="block px-2 py-2 hover:bg-muted rounded">
            Settings
          </Link>
        </nav>
      )}
    </header>
  );
}

// Sidebar component
export function Sidebar({ children }: { children: ReactNode }) {
  return (
    <aside className="hidden lg:block w-64 border-r bg-card min-h-[calc(100vh-4rem)] p-4 overflow-y-auto">
      {children}
    </aside>
  );
}

// Main component
export function Main({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <main className={`flex-1 overflow-y-auto ${className}`}>{children}</main>;
}

// Footer component
export function Footer({ children }: { children?: ReactNode }) {
  return (
    <footer className="border-t bg-muted py-8 mt-auto">
      <Container>
        {children || (
          <p className="text-sm text-muted-foreground text-center">
            © 2024 Jarvis. All rights reserved.
          </p>
        )}
      </Container>
    </footer>
  );
}
