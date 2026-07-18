"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const tagVariants = cva(
  "inline-flex items-center gap-1 rounded-md border-2 px-2 py-1 text-xs font-medium transition-all duration-200",
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
        sm: "text-xs px-1.5 py-0.5",
        md: "text-sm px-2 py-1",
        lg: "text-base px-3 py-1.5",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

interface TagProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof tagVariants> {
  icon?: React.ReactNode;
  onClose?: () => void;
}

const Tag = React.forwardRef<HTMLDivElement, TagProps>(
  (
    { className, variant, size, icon, onClose, children, ...props },
    ref
  ) => (
    <div
      ref={ref}
      className={cn(tagVariants({ variant, size }), className)}
      {...props}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      <span className="flex-1">{children}</span>
      {onClose && (
        <button
          onClick={onClose}
          className="flex-shrink-0 ml-1 hover:opacity-70 transition-opacity"
          aria-label="Remove tag"
        >
          <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
          </svg>
        </button>
      )}
    </div>
  )
);

Tag.displayName = "Tag";

export { Tag, tagVariants };
export type { TagProps };
