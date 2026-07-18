"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";
import { AlertCircle, CheckCircle, Info } from "lucide-react";

const emptyStateVariants = cva("text-center py-12 px-4", {
  variants: {
    variant: {
      default: "text-muted-foreground",
      error: "text-destructive",
      success: "text-green-600",
      info: "text-blue-600",
    },
  },
  defaultVariants: {
    variant: "default",
  },
});

interface EmptyStateProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, 'title'>,
    VariantProps<typeof emptyStateVariants> {
  icon?: React.ReactNode;
  title: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
}

const EmptyState = React.forwardRef<HTMLDivElement, EmptyStateProps>(
  (
    {
      className,
      variant,
      icon,
      title,
      description,
      action,
      ...props
    },
    ref
  ) => {
    const iconMap = {
      default: null,
      error: <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />,
      success: <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />,
      info: <Info className="h-12 w-12 mx-auto mb-4 opacity-50" />,
    };

    return (
      <div
        ref={ref}
        className={cn(emptyStateVariants({ variant }), className)}
        {...props}
      >
        <div className="flex flex-col items-center">
          {icon || iconMap[variant || "default"]}
          <h3 className="text-lg font-semibold mt-4 mb-2">{title}</h3>
          {description && (
            <p className="text-sm max-w-md mb-6">{description}</p>
          )}
          {action}
        </div>
      </div>
    );
  }
);

EmptyState.displayName = "EmptyState";

export { EmptyState, emptyStateVariants };
export type { EmptyStateProps };
