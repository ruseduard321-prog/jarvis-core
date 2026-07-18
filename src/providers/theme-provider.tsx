"use client";

import { useEffect } from "react";
import { useThemeStore } from "@/store";

interface ThemeProviderProps {
  children: React.ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const { theme, setResolvedTheme } = useThemeStore();

  useEffect(() => {
    // Avoid hydration mismatch by setting theme after mount
    const htmlElement = document.documentElement;

    // Determine resolved theme
    let effectiveTheme = theme;
    if (theme === "system") {
      effectiveTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    }

    // Apply theme
    if (effectiveTheme === "dark") {
      htmlElement.classList.add("dark");
    } else {
      htmlElement.classList.remove("dark");
    }

    setResolvedTheme(effectiveTheme as "light" | "dark");

    // Listen to system theme changes
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = (e: MediaQueryListEvent) => {
      if (theme === "system") {
        const newTheme = e.matches ? "dark" : "light";
        if (newTheme === "dark") {
          htmlElement.classList.add("dark");
        } else {
          htmlElement.classList.remove("dark");
        }
        setResolvedTheme(newTheme as "light" | "dark");
      }
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [theme, setResolvedTheme]);

  return children;
}
