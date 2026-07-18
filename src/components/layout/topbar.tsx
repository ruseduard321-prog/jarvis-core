"use client";

import React from "react";
import { Search, Bell, Moon, Sun, LogOut, Settings, HelpCircle, User, Loader2 } from "lucide-react";
import { cn } from "@/utils";
import { useBreadcrumbs } from "@/hooks/use-navigation";
import { useThemeStore } from "@/store";
import { Button } from "@/components/ui/button";
import { Popover } from "@/components/ui/popover";
import { Tooltip } from "@/components/ui/tooltip";
import { useBoolean } from "@/hooks";
import { useAuth } from "@/providers/auth-provider";

interface TopBarProps {
  className?: string;
}

/**
 * Top Navigation Bar
 * Features: logo area, breadcrumbs, global search, theme toggle, notifications, user menu, command button
 */
export const TopBar = React.forwardRef<HTMLDivElement, TopBarProps>(
  ({ className }, ref) => {
    const breadcrumbs = useBreadcrumbs();

    return (
      <header
        ref={ref}
        className={cn(
          "sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60",
          className
        )}
        role="banner"
      >
        <div className="flex h-16 items-center justify-between gap-4 px-6">
          {/* Left: Breadcrumbs */}
          <div className="flex-1">
            <Breadcrumbs items={breadcrumbs} />
          </div>

          {/* Center: Search (hidden on mobile) */}
          <div className="hidden flex-1 md:flex md:max-w-sm">
            <GlobalSearch />
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-2">
            {/* Command Button */}
            <Tooltip content="Open command palette (Ctrl+K)">
              <Button
                size="sm"
                variant="ghost"
                aria-label="Open command palette"
                title="Ctrl+K"
                className="px-2"
              >
                <Search className="h-5 w-5" />
              </Button>
            </Tooltip>

            {/* Notifications */}
            <NotificationsButton />

            {/* Theme Toggle */}
            <ThemeToggle />

            {/* User Menu */}
            <UserMenu />
          </div>
        </div>
      </header>
    );
  }
);

TopBar.displayName = "TopBar";

/**
 * Breadcrumbs Navigation
 */
interface BreadcrumbsProps {
  items: Array<{ label: string; href?: string }>;
}

function Breadcrumbs({ items }: BreadcrumbsProps) {
  return (
    <nav
      className="hidden text-sm text-muted-foreground lg:flex items-center gap-1"
      aria-label="Breadcrumbs"
    >
      {items.map((item, index) => (
        <React.Fragment key={index}>
          {index > 0 && <span className="mx-1 text-muted-foreground/50">/</span>}
          {item.href ? (
            <a
              href={item.href}
              className="hover:text-foreground transition-colors"
            >
              {item.label}
            </a>
          ) : (
            <span className="text-foreground">{item.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}

/**
 * Global Search Component (Placeholder)
 */
function GlobalSearch() {
  const [isFocused, { on: setFocused, off: setBlurred }] = useBoolean(false);

  return (
    <div className={cn(
      "relative flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2 transition-colors",
      isFocused && "border-primary/50 bg-muted"
    )}>
      <Search className="h-4 w-4 text-muted-foreground" />
      <input
        type="text"
        placeholder="Search..."
        className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        onFocus={setFocused}
        onBlur={setBlurred}
        aria-label="Global search"
      />
      <kbd className="hidden rounded px-2 py-1 text-xs font-medium text-muted-foreground bg-background/50 sm:inline">
        ⌘K
      </kbd>
    </div>
  );
}

/**
 * Notifications Button (Placeholder)
 */
function NotificationsButton() {

  return (
    <Popover
      trigger={
        <Tooltip content="Notifications">
          <Button
            size="sm"
            variant="ghost"
            aria-label="Notifications"
            className="px-2 relative"
          >
            <Bell className="h-5 w-5" />
            <span className="absolute top-1 right-1 h-2 w-2 bg-destructive rounded-full" />
          </Button>
        </Tooltip>
      }
    >
      <NotificationPanel />
    </Popover>
  );
}

/**
 * Notification Panel (Mock Data)
 */
function NotificationPanel() {
  const mockNotifications = [
    { id: "1", title: "Welcome to Jarvis", message: "Get started with your AI assistant", time: "2 minutes ago", read: false },
    { id: "2", title: "System Update", message: "New features are available", time: "1 hour ago", read: true },
    { id: "3", title: "Workflow Complete", message: "Your automation workflow finished", time: "3 hours ago", read: true },
  ];

  return (
    <div className="w-96 max-h-96 overflow-y-auto">
      <div className="border-b border-border p-4">
        <h3 className="font-semibold">Notifications</h3>
      </div>
      <div className="divide-y divide-border">
        {mockNotifications.map((notification) => (
          <div
            key={notification.id}
            className={cn(
              "p-4 hover:bg-muted/50 transition-colors cursor-pointer",
              !notification.read && "bg-muted/30"
            )}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className={cn(
                  "text-sm font-medium",
                  !notification.read && "font-semibold"
                )}>
                  {notification.title}
                </h4>
                <p className="text-xs text-muted-foreground mt-1">{notification.message}</p>
              </div>
              {!notification.read && (
                <div className="ml-2 h-2 w-2 bg-primary rounded-full flex-shrink-0 mt-1" />
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-2">{notification.time}</p>
          </div>
        ))}
      </div>
      <div className="border-t border-border p-4">
        <Button variant="ghost" size="sm" fullWidth>
          View all notifications
        </Button>
      </div>
    </div>
  );
}

/**
 * Theme Toggle
 */
function ThemeToggle() {
  const { theme, setTheme } = useThemeStore();

  return (
    <Tooltip content={`Switch to ${theme === "light" ? "dark" : "light"} mode`}>
      <Button
        size="sm"
        variant="ghost"
        onClick={() => setTheme(theme === "light" ? "dark" : "light")}
        aria-label="Toggle theme"
        className="px-2"
      >
        {theme === "light" ? (
          <Moon className="h-5 w-5" />
        ) : (
          <Sun className="h-5 w-5" />
        )}
      </Button>
    </Tooltip>
  );
}

/**
 * User Menu (Authenticated)
 */
function UserMenu() {
  const { user, logout, isLoading } = useAuth();

  // Get initials from user name or email
  const getInitials = (user: any) => {
    if (user?.full_name) {
      return user.full_name
        .split(" ")
        .map((n: string) => n[0])
        .join("")
        .toUpperCase();
    }
    return user?.email?.[0]?.toUpperCase() || "?";
  };

  return (
    <Popover
      trigger={
        <Button size="sm" variant="ghost" aria-label="User menu" className="px-2">
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-xs font-bold text-primary-foreground">
            {getInitials(user)}
          </div>
        </Button>
      }
    >
      <UserMenuPanel user={user} logout={logout} isLoading={isLoading} />
    </Popover>
  );
}

interface UserMenuPanelProps {
  user: any;
  logout: () => Promise<void>;
  isLoading: boolean;
}

/**
 * User Menu Panel (Authenticated)
 */
function UserMenuPanel({ user, logout, isLoading }: UserMenuPanelProps) {
  const [isLoggingOut, setIsLoggingOut] = React.useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
    } catch (error) {
      console.error("Logout failed:", error);
    } finally {
      setIsLoggingOut(false);
    }
  };

  const displayName = user?.full_name || user?.email?.split("@")[0] || "User";
  const displayEmail = user?.email || "";

  return (
    <div className="w-56">
      {/* User Info */}
      <div className="border-b border-border p-4">
        <h4 className="font-semibold truncate">{displayName}</h4>
        <p className="text-xs text-muted-foreground truncate">{displayEmail}</p>
      </div>

      {/* Menu Items */}
      <div className="divide-y divide-border">
        <div className="p-2">
          <button
            disabled={isLoading || isLoggingOut}
            className="w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md hover:bg-muted transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <User className="h-4 w-4" />
            Profile
          </button>
          <button
            disabled={isLoading || isLoggingOut}
            className="w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md hover:bg-muted transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Settings className="h-4 w-4" />
            Preferences
          </button>
          <button
            disabled={isLoading || isLoggingOut}
            className="w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md hover:bg-muted transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <HelpCircle className="h-4 w-4" />
            Help & Support
          </button>
        </div>

        {/* Logout */}
        <div className="p-2">
          <button
            onClick={handleLogout}
            disabled={isLoading || isLoggingOut}
            className="w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md hover:bg-destructive/10 transition-colors text-destructive disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoggingOut ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Logging out...
              </>
            ) : (
              <>
                <LogOut className="h-4 w-4" />
                Logout
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default TopBar;
