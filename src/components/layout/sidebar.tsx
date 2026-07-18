"use client";

import React, { useCallback } from "react";
import Link from "next/link";
import { ChevronDown, ChevronLeft, ChevronRight, Menu, X } from "lucide-react";
import { cn } from "@/utils";
import { mainNavigation } from "@/config/navigation";
import { useIsActive, useMobileSidebar, useSidebarCollapsed } from "@/hooks/use-navigation";
import { useBoolean } from "@/hooks";
import type { NavItem, NavGroup } from "@/config/navigation";

interface SidebarProps {
  className?: string;
}

/**
 * Main Sidebar Component
 * Features: collapse, expand, mobile drawer, nested navigation, active routes, icons, groups, tooltips, keyboard nav
 */
export const Sidebar = React.forwardRef<HTMLDivElement, SidebarProps>(
  ({ className }, ref) => {
    const [isCollapsed, setIsCollapsed] = useSidebarCollapsed() || [false, () => {}];
    const { isOpen: isMobileOpen, toggle: toggleMobileOpen, close: closeMobileOpen } = useMobileSidebar();

    const toggleCollapse = useCallback(() => {
      setIsCollapsed((prev) => !prev);
    }, [setIsCollapsed]);

    return (
      <>
        {/* Mobile Sidebar Backdrop */}
        {isMobileOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/50 md:hidden"
            onClick={closeMobileOpen}
            aria-hidden="true"
          />
        )}

        {/* Sidebar Container */}
        <aside
          ref={ref}
          className={cn(
            "fixed left-0 top-0 z-50 flex h-screen w-64 flex-col border-r border-border bg-background transition-all duration-300 md:relative md:z-0",
            isCollapsed && "md:w-20",
            !isMobileOpen && "md:translate-x-0 -translate-x-full",
            isMobileOpen && "translate-x-0",
            className
          )}
          role="navigation"
          aria-label="Main navigation"
        >
          {/* Header */}
          <SidebarHeader isCollapsed={isCollapsed} onClose={closeMobileOpen} onToggle={toggleCollapse} />

          {/* Navigation Groups */}
          <nav className="flex-1 overflow-y-auto px-2 py-4">
            {mainNavigation.map((group) => (
              <SidebarGroup
                key={group.id}
                group={group}
                isCollapsed={isCollapsed}
                onNavigate={closeMobileOpen}
              />
            ))}
          </nav>

          {/* Footer */}
          <SidebarFooter isCollapsed={isCollapsed} />
        </aside>

        {/* Mobile Menu Button */}
        <MobileMenuButton onClick={toggleMobileOpen} />
      </>
    );
  }
);

Sidebar.displayName = "Sidebar";

/**
 * Sidebar Header with Logo and Controls
 */
interface SidebarHeaderProps {
  isCollapsed: boolean;
  onClose: () => void;
  onToggle: () => void;
}

function SidebarHeader({ isCollapsed, onClose, onToggle }: SidebarHeaderProps) {
  return (
    <div className={cn(
      "flex items-center justify-between border-b border-border px-4 py-4 transition-all",
      isCollapsed ? "flex-col gap-2" : ""
    )}>
      {!isCollapsed && (
        <h1 className="text-lg font-bold text-primary">Jarvis</h1>
      )}
      {isCollapsed && (
        <div className="h-8 w-8 rounded-md bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">
          J
        </div>
      )}
      <div className="flex items-center gap-2">
        <button
          onClick={onToggle}
          className="hidden rounded-md p-1.5 hover:bg-muted md:inline-flex"
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={isCollapsed ? "Expand" : "Collapse"}
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
        <button
          onClick={onClose}
          className="rounded-md p-1.5 hover:bg-muted md:hidden"
          aria-label="Close sidebar"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

/**
 * Sidebar Navigation Group
 */
interface SidebarGroupProps {
  group: NavGroup;
  isCollapsed: boolean;
  onNavigate: () => void;
}

function SidebarGroup({ group, isCollapsed, onNavigate }: SidebarGroupProps) {
  return (
    <div className="mb-6">
      {!isCollapsed && (
        <h3 className="mb-3 px-2 text-xs font-semibold uppercase text-muted-foreground tracking-wider">
          {group.label}
        </h3>
      )}
      <ul className="space-y-1">
        {group.items.map((item) => (
          <SidebarItem
            key={item.id}
            item={item}
            isCollapsed={isCollapsed}
            onNavigate={onNavigate}
          />
        ))}
      </ul>
    </div>
  );
}

/**
 * Sidebar Navigation Item
 */
interface SidebarItemProps {
  item: NavItem;
  isCollapsed: boolean;
  onNavigate: () => void;
  level?: number;
}

function SidebarItem({
  item,
  isCollapsed,
  onNavigate,
  level = 0,
}: SidebarItemProps) {
  const isActive = useIsActive(item.href);
  const [isOpen, { toggle: toggleOpen }] = useBoolean(false);

  if (item.disabled) {
    return null;
  }

  const hasChildren = item.children && item.children.length > 0;

  return (
    <li>
      <Link
        href={item.href}
        className={cn(
          "group relative flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
          "hover:bg-muted hover:text-foreground",
          isActive
            ? "bg-primary/10 text-primary"
            : "text-muted-foreground",
          level > 0 && "ml-4 border-l border-border/50 pl-2",
          item.disabled && "cursor-not-allowed opacity-50"
        )}
        onClick={(e) => {
          if (hasChildren) {
            e.preventDefault();
            toggleOpen();
            return;
          }
          onNavigate();
        }}
        title={isCollapsed && !hasChildren ? item.label : undefined}
        aria-current={isActive ? "page" : undefined}
        aria-disabled={item.disabled}
      >
        {item.icon && (
          <span className="flex-shrink-0">
            {item.icon}
          </span>
        )}
        {!isCollapsed && (
          <>
            <span className="flex-1 truncate">{item.label}</span>
            {item.badge && (
              <span className="ml-auto inline-flex items-center rounded-full bg-primary/20 px-2 py-0.5 text-xs font-medium text-primary">
                {item.badge}
              </span>
            )}
            {hasChildren && (
              <ChevronDown
                className={cn(
                  "h-4 w-4 transition-transform",
                  isOpen && "rotate-180"
                )}
              />
            )}
          </>
        )}
      </Link>

      {/* Children */}
      {hasChildren && !isCollapsed && isOpen && (
        <ul className="mt-1 space-y-0.5">
          {item.children!.map((child) => (
            <SidebarItem
              key={child.id}
              item={child}
              isCollapsed={isCollapsed}
              onNavigate={onNavigate}
              level={level + 1}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

/**
 * Sidebar Footer
 */
interface SidebarFooterProps {
  isCollapsed: boolean;
}

function SidebarFooter({ isCollapsed }: SidebarFooterProps) {
  return (
    <div className={cn(
      "border-t border-border p-4",
      isCollapsed && "flex justify-center"
    )}>
      {!isCollapsed && (
        <p className="text-xs text-muted-foreground">
          © 2026 Jarvis. All rights reserved.
        </p>
      )}
      {isCollapsed && (
        <p className="text-xs text-muted-foreground" title="Jarvis 2026">
          ©
        </p>
      )}
    </div>
  );
}

/**
 * Mobile Menu Button (appears only on mobile)
 */
interface MobileMenuButtonProps {
  onClick: () => void;
}

function MobileMenuButton({ onClick }: MobileMenuButtonProps) {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 z-40 md:hidden rounded-lg bg-primary text-primary-foreground p-3 shadow-lg hover:bg-primary/90 transition-colors"
      aria-label="Open mobile menu"
    >
      <Menu className="h-6 w-6" />
    </button>
  );
}

export default Sidebar;
