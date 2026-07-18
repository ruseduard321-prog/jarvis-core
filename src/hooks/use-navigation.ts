/**
 * Navigation Hooks
 * Custom hooks for navigation, breadcrumbs, and active routes
 */

"use client";

import { usePathname } from "next/navigation";
import { breadcrumbMap, getNavItemByHref, mainNavigation } from "@/config/navigation";
import type { NavItem } from "@/config/navigation";
import { useCallback, useMemo } from "react";

/**
 * Hook to get breadcrumb items for current route
 */
export function useBreadcrumbs(): Array<{ label: string; href?: string }> {
  const pathname = usePathname();

  return useMemo(() => {
    // Split the pathname and generate breadcrumbs
    const segments = pathname.split("/").filter(Boolean);
    const breadcrumbs: Array<{ label: string; href?: string }> = [];

    // Add home
    breadcrumbs.push({ label: "Home", href: "/" });

    // Add each segment
    let currentPath = "";
    segments.forEach((segment, index) => {
      currentPath += `/${segment}`;

      // Try to find label from breadcrumb map
      const label = breadcrumbMap[currentPath] || segment.charAt(0).toUpperCase() + segment.slice(1);
      const isLast = index === segments.length - 1;

      breadcrumbs.push({
        label,
        href: isLast ? undefined : currentPath,
      });
    });

    return breadcrumbs;
  }, [pathname]);
}

/**
 * Hook to check if a route is active
 */
export function useIsActive(href: string, exact = false): boolean {
  const pathname = usePathname();

  if (exact) {
    return pathname === href;
  }

  return pathname.startsWith(href);
}

/**
 * Hook to get current navigation item
 */
export function useCurrentNavItem(): NavItem | undefined {
  const pathname = usePathname();

  return useMemo(() => {
    return getNavItemByHref(pathname);
  }, [pathname]);
}

/**
 * Hook to get all navigation items
 */
export function useNavigation() {
  return useMemo(() => mainNavigation, []);
}

/**
 * Hook for mobile sidebar state
 */
export function useMobileSidebar() {
  return useMobileNavigation();
}

/**
 * Hook for mobile navigation state
 */
export function useMobileNavigation() {
  const [isOpen, setIsOpen] = useLocalStorageState("mobile-nav-open", false);

  const toggle = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, [setIsOpen]);

  const close = useCallback(() => {
    setIsOpen(false);
  }, [setIsOpen]);

  const open = useCallback(() => {
    setIsOpen(true);
  }, [setIsOpen]);

  return { isOpen, toggle, close, open };
}

/**
 * Hook for sidebar collapsed state
 */
export function useSidebarCollapsed() {
  return useLocalStorageState("sidebar-collapsed", false);
}

/**
 * Helper hook for localStorage state
 */
function useLocalStorageState<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void] {
  const [state, setState] = useStorageState(key, initialValue);

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      setState(value);
    },
    [setState]
  );

  return [state, setValue];
}

/**
 * Base storage state hook
 */
function useStorageState<T>(key: string, initialValue: T): [T, (value: T | ((prev: T) => T)) => void] {
  const [state, setState] = useStorageValue(key, initialValue);

  const updateState = useCallback(
    (value: T | ((prev: T) => T)) => {
      const valueToStore = value instanceof Function ? value(state) : value;
      setState(valueToStore);
      // Persist to localStorage
      if (typeof window !== "undefined") {
        try {
          window.localStorage.setItem(key, JSON.stringify(valueToStore));
        } catch (e) {
          console.error(`Error saving to localStorage: ${e}`);
        }
      }
    },
    [key, state]
  );

  return [state, updateState];
}

/**
 * Hook to read from storage
 */
function useStorageValue<T>(key: string, initialValue: T): [T, (value: T) => void] {
  const [value, setValue] = useReactState<T>(() => {
    if (typeof window === "undefined") return initialValue;

    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  return [value, setValue];
}

// Re-export useState for clarity
import { useState as useReactState } from "react";
