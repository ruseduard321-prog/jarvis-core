"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const chipVariants = cva(
  "inline-flex items-center gap-2 rounded-full border-2 px-3 py-1 text-sm font-medium transition-all duration-200",
  {
    variants: {
      variant: {
        default: "border-primary/30 bg-primary/10 text-primary hover:bg-primary/20",
        secondary:
          "border-secondary/30 bg-secondary/10 text-secondary hover:bg-secondary/20",
        destructive:
          "border-destructive/30 bg-destructive/10 text-destructive hover:bg-destructive/20",
        success:
          "border-green-600/30 bg-green-600/10 text-green-700 dark:text-green-400 hover:bg-green-600/20",
        outline: "border-border bg-transparent hover:bg-muted",
      },
      size: {
        sm: "text-xs px-2 py-0.5",
        md: "text-sm px-3 py-1",
        lg: "text-base px-4 py-1.5",
      },
      removable: {
        true: "pr-1",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

interface ChipProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof chipVariants> {
  icon?: React.ReactNode;
  onRemove?: () => void;
  avatar?: React.ReactNode;
}

const Chip = React.forwardRef<HTMLDivElement, ChipProps>(
  (
    { className, variant, size, children, icon, onRemove, avatar, ...props },
    ref
  ) => (
    <div
      ref={ref}
      className={cn(
        chipVariants({ variant, size, removable: !!onRemove }),
        className
      )}
      {...props}
    >
      {avatar && <div className="flex-shrink-0">{avatar}</div>}
      {icon && <div className="flex-shrink-0">{icon}</div>}
      <span className="flex-1">{children}</span>
      {onRemove && (
        <button
          onClick={onRemove}
          className="flex-shrink-0 ml-1 hover:opacity-70 transition-opacity"
          aria-label="Remove"
        >
          <svg
            className="h-4 w-4"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
          </svg>
        </button>
      )}
    </div>
  )
);

Chip.displayName = "Chip";

export { Chip, chipVariants };
export type { ChipProps };
