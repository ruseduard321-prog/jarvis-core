"use client";

import React from "react";
import { cn } from "@/utils";
import { Sidebar } from "./sidebar";
import { TopBar } from "./topbar";
import { CommandPalette } from "./command-palette";
import { useBoolean } from "@/hooks";

interface AppShellProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Main Application Shell Layout
 * Combines sidebar, top navigation, and main content area
 * Features: responsive, accessible, full theme support
 */
export const AppShell = React.forwardRef<HTMLDivElement, AppShellProps>(
  ({ children, className }, ref) => {
    const [commandPaletteOpen, { off: closeCommandPalette }] = useBoolean(false);

    return (
      <div ref={ref} className={cn("flex h-screen flex-col bg-background text-foreground", className)}>
        {/* Command Palette */}
        <CommandPalette isOpen={commandPaletteOpen} onClose={closeCommandPalette} />

        {/* Main Layout */}
        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <Sidebar />

          {/* Main Content */}
          <div className="flex flex-1 flex-col overflow-hidden">
            {/* Top Navigation */}
            <TopBar />

            {/* Page Content */}
            <main
              className="flex-1 overflow-y-auto"
              role="main"
              aria-label="Main content"
            >
              {children}
            </main>
          </div>
        </div>
      </div>
    );
  }
);

AppShell.displayName = "AppShell";

export default AppShell;
