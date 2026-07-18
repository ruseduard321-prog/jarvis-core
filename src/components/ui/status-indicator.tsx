"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const statusIndicatorVariants = cva(
  "inline-flex items-center justify-center rounded-full flex-shrink-0",
  {
    variants: {
      status: {
        online: "bg-green-600",
        offline: "bg-gray-400",
        away: "bg-yellow-600",
        idle: "bg-blue-600",
        dnd: "bg-red-600",
        busy: "bg-orange-600",
      },
      size: {
        xs: "h-2 w-2",
        sm: "h-3 w-3",
        md: "h-4 w-4",
        lg: "h-6 w-6",
      },
      animate: {
        true: "animate-pulse",
      },
    },
    defaultVariants: {
      status: "online",
      size: "md",
    },
  }
);

interface StatusIndicatorProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof statusIndicatorVariants> {
  label?: string;
}

const StatusIndicator = React.forwardRef<HTMLDivElement, StatusIndicatorProps>(
  (
    { className, status, size, animate, label, ...props },
    ref
  ) => (
    <div className="inline-flex items-center gap-2">
      <div
        ref={ref}
        className={cn(statusIndicatorVariants({ status, size, animate }), className)}
        title={label}
        {...props}
      />
      {label && <span className="text-sm">{label}</span>}
    </div>
  )
);

StatusIndicator.displayName = "StatusIndicator";

export { StatusIndicator, statusIndicatorVariants };
export type { StatusIndicatorProps };
