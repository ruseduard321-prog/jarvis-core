"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Search, Command } from "lucide-react";
import { cn } from "@/utils";
import { Dialog } from "@/components/ui/dialog";
import { mainNavigation } from "@/config/navigation";

interface CommandPaletteProps {
  isOpen?: boolean;
  onClose?: () => void;
}

/**
 * Command Palette Component
 * Keyboard shortcut: Ctrl+K or Cmd+K
 * Features: search, categories, keyboard navigation, empty state
 */
export const CommandPalette = React.forwardRef<HTMLDivElement, CommandPaletteProps>(
  ({ isOpen = false, onClose }, ref) => {
    const [internalOpen, setInternalOpen] = useState(isOpen);
    const [search, setSearch] = useState("");
    const [selectedIndex, setSelectedIndex] = useState(0);

    const open = internalOpen || isOpen;

    // Get all commands
    const allCommands = getAllCommands();
    const filteredCommands = search
      ? allCommands.filter(
        (cmd) =>
          cmd.title.toLowerCase().includes(search.toLowerCase()) ||
          cmd.category.toLowerCase().includes(search.toLowerCase())
      )
      : [];

    // Group by category
    const groupedCommands = search
      ? {}
      : filteredCommands.reduce(
        (acc, cmd) => {
          if (!acc[cmd.category]) acc[cmd.category] = [];
          acc[cmd.category].push(cmd);
          return acc;
        },
        {} as Record<string, Command[]>
      );

    const handleClose = useCallback(() => {
      setInternalOpen(false);
      setSearch("");
      setSelectedIndex(0);
      onClose?.();
    }, [onClose]);

    const handleSelectCommand = useCallback((cmd: Command) => {
      window.location.href = cmd.href;
      handleClose();
    }, [handleClose]);

    // Handle keyboard shortcuts
    useEffect(() => {
      const handleKeyDown = (e: KeyboardEvent) => {
        // Ctrl+K or Cmd+K to toggle
        if ((e.ctrlKey || e.metaKey) && e.key === "k") {
          e.preventDefault();
          setInternalOpen((prev) => !prev);
        }

        // Escape to close
        if (e.key === "Escape" && open) {
          handleClose();
        }

        // Arrow keys for navigation
        if (open && filteredCommands.length > 0) {
          if (e.key === "ArrowDown") {
            e.preventDefault();
            setSelectedIndex((prev) => (prev + 1) % filteredCommands.length);
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setSelectedIndex((prev) => (prev - 1 + filteredCommands.length) % filteredCommands.length);
          } else if (e.key === "Enter") {
            e.preventDefault();
            const cmd = filteredCommands[selectedIndex];
            if (cmd) {
              handleSelectCommand(cmd);
            }
          }
        }
      };

      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }, [open, filteredCommands, selectedIndex, handleClose, handleSelectCommand]);

    return (
      <Dialog
        isOpen={open}
        onClose={handleClose}
        size="md"
      >
        <div ref={ref} className="w-full">
          {/* Search Input */}
          <div className="relative border-b border-border p-4">
            <Search className="absolute left-7 top-6 h-4 w-4 text-muted-foreground pointer-events-none" />
            <input
              type="text"
              placeholder="Search commands or navigate..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setSelectedIndex(0);
              }}
              className="w-full pl-10 pr-4 py-2 text-sm border border-border rounded-md outline-none focus:border-primary bg-background"
              autoFocus
              aria-label="Search commands"
            />
            <kbd className="absolute right-4 top-5 text-xs text-muted-foreground pointer-events-none">
              ESC
            </kbd>
          </div>

          {/* Commands List */}
          <div className="max-h-96 overflow-y-auto p-2">
            {filteredCommands.length > 0 ? (
              <div className="space-y-4">
                {/* Grouped by category */}
                {Object.entries(groupedCommands).map(([category, commands]) => (
                  <div key={category}>
                    <h3 className="px-2 py-1.5 text-xs font-semibold uppercase text-muted-foreground">
                      {category}
                    </h3>
                    <div className="space-y-1">
                      {commands.map((cmd) => {
                        const globalIndex = filteredCommands.indexOf(cmd);
                        const isSelected = globalIndex === selectedIndex;

                        return (
                          <button
                            key={cmd.id}
                            onClick={() => handleSelectCommand(cmd)}
                            onMouseEnter={() => setSelectedIndex(globalIndex)}
                            className={cn(
                              "w-full flex items-center justify-between gap-3 px-3 py-2 text-sm rounded-md transition-colors",
                              isSelected
                                ? "bg-primary text-primary-foreground"
                                : "hover:bg-muted text-foreground"
                            )}
                            role="menuitem"
                          >
                            <span className="flex items-center gap-2">
                              {cmd.icon}
                              <span>{cmd.title}</span>
                            </span>
                            {cmd.shortcut && (
                              <kbd className="text-xs text-muted-foreground">
                                {cmd.shortcut}
                              </kbd>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            ) : search ? (
              <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
                <Search className="h-8 w-8 text-muted-foreground/30" />
                <div>
                  <p className="text-sm font-medium text-foreground">No results found</p>
                  <p className="text-xs text-muted-foreground">Try searching for a different term</p>
                </div>
              </div>
            ) : (
              <EmptyCommandPalette />
            )}
          </div>

          {/* Footer */}
          {filteredCommands.length > 0 && (
            <div className="border-t border-border px-4 py-3">
              <p className="text-xs text-muted-foreground">
                Use <kbd className="inline px-1 text-xs">↑↓</kbd> to navigate,{" "}
                <kbd className="inline px-1 text-xs">Enter</kbd> to select,{" "}
                <kbd className="inline px-1 text-xs">ESC</kbd> to close
              </p>
            </div>
          )}
        </div>
      </Dialog>
    );
  }
);

CommandPalette.displayName = "CommandPalette";

/**
 * Empty State for Command Palette
 */
function EmptyCommandPalette() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12 px-4">
      <Command className="h-8 w-8 text-muted-foreground/30" />
      <div className="text-center">
        <p className="text-sm font-medium text-foreground mb-1">Welcome to Command Palette</p>
        <p className="text-xs text-muted-foreground mb-6">
          Start typing to search for commands or navigate
        </p>
      </div>

      {/* Quick Links */}
      <div className="w-full space-y-3 text-xs">
        <div>
          <p className="font-medium text-muted-foreground mb-2">Quick Access</p>
          <div className="space-y-1 text-muted-foreground">
            <p>• Type to search all commands</p>
            <p>• Use arrow keys to navigate</p>
            <p>• Press Enter to select</p>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Command Interface
 */
interface Command {
  id: string;
  title: string;
  category: string;
  href: string;
  icon?: React.ReactNode;
  shortcut?: string;
}

/**
 * Get all available commands
 */
function getAllCommands(): Command[] {
  const commands: Command[] = [];

  // Extract navigation items as commands
  mainNavigation.forEach((group) => {
    group.items.forEach((item) => {
      commands.push({
        id: item.id,
        title: item.label,
        category: group.label,
        href: item.href,
        icon: item.icon,
      });

      // Add child items
      if (item.children) {
        item.children.forEach((child) => {
          commands.push({
            id: child.id,
            title: child.label,
            category: `${group.label} > ${item.label}`,
            href: child.href,
            icon: child.icon,
          });
        });
      }
    });
  });

  // Add common actions
  commands.push(
    {
      id: "toggle-theme",
      title: "Toggle Theme",
      category: "Appearance",
      href: "#toggle-theme",
      shortcut: "Ctrl+Shift+L",
    },
    {
      id: "search",
      title: "Global Search",
      category: "Navigation",
      href: "#search",
      shortcut: "Ctrl+/",
    }
  );

  return commands;
}

export default CommandPalette;
