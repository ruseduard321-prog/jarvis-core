/**
 * Centralized Navigation Configuration
 *
 * This file defines all navigation items, routes, and metadata.
 * Avoid hardcoding links - use this config as the single source of truth.
 */

import type { ReactNode } from "react";

export interface NavItem {
  id: string;
  label: string;
  href: string;
  icon?: ReactNode;
  badge?: string | number;
  description?: string;
  children?: NavItem[];
  divider?: boolean;
  disabled?: boolean;
  visible?: boolean;
  requiresAuth?: boolean;
}

export interface NavGroup {
  id: string;
  label: string;
  items: NavItem[];
}

/**
 * Main navigation structure for the application
 * Icons are dynamically imported in components to avoid JSX in .ts files
 */
export const mainNavigation: NavGroup[] = [
  {
    id: "main",
    label: "Main",
    items: [
      {
        id: "dashboard",
        label: "Dashboard",
        href: "/dashboard",
        description: "Overview and insights",
      },
    ],
  },
  {
    id: "features",
    label: "Features",
    items: [
      {
        id: "chat",
        label: "Chat",
        href: "/chat",
        badge: "New",
        description: "Conversation with AI",
      },
      {
        id: "knowledge",
        label: "Knowledge",
        href: "/knowledge",
        description: "Knowledge base",
      },
      {
        id: "agents",
        label: "Agents",
        href: "/agents",
        description: "AI agents",
      },
      {
        id: "tools",
        label: "Tools",
        href: "/tools",
        description: "Available tool catalog",
      },
      {
        id: "workflows",
        label: "Workflows",
        href: "/workflows",
        description: "Automation workflows",
      },
    ],
  },
  {
    id: "workspace",
    label: "Workspace",
    items: [
      {
        id: "analytics",
        label: "Analytics",
        href: "/analytics",
        description: "Analytics and reports",
        disabled: true,
      },
    ],
  },
  {
    id: "settings",
    label: "Settings",
    items: [
      {
        id: "settings",
        label: "Settings",
        href: "/settings",
        description: "Account and workspace settings",
      },
    ],
  },
];

/**
 * Breadcrumb mapping for routes
 * Maps routes to human-readable breadcrumb labels
 */
export const breadcrumbMap: Record<string, string> = {
  "/": "Home",
  "/dashboard": "Dashboard",
  "/chat": "Chat",
  "/knowledge": "Knowledge",
  "/agents": "Agents",
  "/tools": "Tools",
  "/workflows": "Workflows",
  "/settings": "Settings",
  "/settings/profile": "Profile",
  "/settings/preferences": "Preferences",
  "/settings/workspace": "Workspace",
};

/**
 * Flatten navigation for easier searching
 */
export function flattenNavigation(): NavItem[] {
  const items: NavItem[] = [];

  const traverse = (item: NavItem) => {
    items.push(item);
    if (item.children) {
      item.children.forEach(traverse);
    }
  };

  mainNavigation.forEach((group) => {
    group.items.forEach(traverse);
  });

  return items;
}

/**
 * Get navigation item by ID
 */
export function getNavItemById(id: string): NavItem | undefined {
  return flattenNavigation().find((item) => item.id === id);
}

/**
 * Get navigation item by href
 */
export function getNavItemByHref(href: string): NavItem | undefined {
  return flattenNavigation().find((item) => item.href === href);
}

/**
 * Check if a route is visible in navigation
 */
export function isNavItemVisible(item: NavItem): boolean {
  return item.visible !== false;
}
