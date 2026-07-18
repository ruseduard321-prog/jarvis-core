"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full font-medium transition-all duration-200 border",
  {
    variants: {
      variant: {
        default:
          "border-primary/30 bg-primary/10 text-primary hover:bg-primary/20",
        secondary:
          "border-secondary/30 bg-secondary/10 text-secondary hover:bg-secondary/20",
        destructive:
          "border-destructive/30 bg-destructive/10 text-destructive hover:bg-destructive/20",
        success:
          "border-green-600/30 bg-green-600/10 text-green-700 dark:text-green-400 hover:bg-green-600/20",
        warning:
          "border-yellow-600/30 bg-yellow-600/10 text-yellow-700 dark:text-yellow-400 hover:bg-yellow-600/20",
        info: "border-blue-600/30 bg-blue-600/10 text-blue-700 dark:text-blue-400 hover:bg-blue-600/20",
        outline: "border-border bg-transparent hover:bg-muted",
        ghost: "border-transparent bg-transparent hover:bg-muted",
      },
      size: {
        xs: "px-1.5 py-0.5 text-xs gap-1",
        sm: "px-2 py-0.5 text-xs gap-1",
        md: "px-3 py-1 text-sm gap-1.5",
        lg: "px-4 py-1.5 text-base gap-2",
      },
      dot: {
        true: "before:content-[''] before:w-2 before:h-2 before:rounded-full before:bg-current",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  icon?: React.ReactNode;
  onClose?: () => void;
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  (
    { className, variant, size, dot, icon, children, onClose, ...props },
    ref
  ) => (
    <div
      ref={ref}
      className={cn(badgeVariants({ variant, size, dot }), className)}
      {...props}
    >
      {icon && <span>{icon}</span>}
      {children}
      {onClose && (
        <button
          onClick={onClose}
          className="ml-1 hover:opacity-70 transition-opacity"
          aria-label="Remove badge"
        >
          <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
          </svg>
        </button>
      )}
    </div>
  )
);

Badge.displayName = "Badge";

export { Badge, badgeVariants };
export type { BadgeProps };
