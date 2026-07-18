"use client";

import { ReactNode } from "react";
import { ChevronRight } from "lucide-react";

interface BreadcrumbProps {
  items: Array<{
    label: string;
    href?: string;
  }>;
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav className="flex items-center space-x-1 text-sm">
      {items.map((item, index) => (
        <div key={index} className="flex items-center space-x-1">
          {index > 0 && <ChevronRight className="w-4 h-4 text-muted-foreground" />}
          {item.href ? (
            <a href={item.href} className="text-primary hover:underline">
              {item.label}
            </a>
          ) : (
            <span className="text-foreground">{item.label}</span>
          )}
        </div>
      ))}
    </nav>
  );
}

interface ContainerProps {
  children: ReactNode;
  className?: string;
}

export function Container({ children, className = "" }: ContainerProps) {
  return (
    <div className={`mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 ${className}`}>
      {children}
    </div>
  );
}

interface CardProps {
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
}

export function Card({ children, className = "", hoverable = false }: CardProps) {
  return (
    <div
      className={`rounded-lg border bg-card p-6 ${hoverable ? "hover:shadow-md transition-shadow" : ""} ${className}`}
    >
      {children}
    </div>
  );
}

interface BadgeProps {
  children: ReactNode;
  variant?: "default" | "secondary" | "destructive" | "success";
  className?: string;
}

export function Badge({ children, variant = "default", className = "" }: BadgeProps) {
  const variantClasses = {
    default: "bg-primary text-primary-foreground",
    secondary: "bg-secondary text-secondary-foreground",
    destructive: "bg-destructive text-destructive-foreground",
    success: "bg-green-600 text-white",
  };

  return (
    <span
      className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${variantClasses[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
