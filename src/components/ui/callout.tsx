"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const calloutVariants = cva(
  "relative w-full rounded-lg border-l-4 p-4 text-sm transition-all duration-200",
  {
    variants: {
      variant: {
        default:
          "border-l-primary bg-primary/5 text-primary [&>svg]:text-primary",
        destructive:
          "border-l-destructive bg-destructive/5 text-destructive [&>svg]:text-destructive",
        success:
          "border-l-green-600 bg-green-600/5 text-green-700 dark:text-green-400 [&>svg]:text-green-600",
        warning:
          "border-l-yellow-600 bg-yellow-600/5 text-yellow-700 dark:text-yellow-400 [&>svg]:text-yellow-600",
        info: "border-l-blue-600 bg-blue-600/5 text-blue-700 dark:text-blue-400 [&>svg]:text-blue-600",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

interface CalloutProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, 'title'>,
    VariantProps<typeof calloutVariants> {
  icon?: React.ReactNode;
  title?: React.ReactNode;
}

const Callout = React.forwardRef<HTMLDivElement, CalloutProps>(
  (
    { className, variant, icon, title, children, ...props },
    ref
  ) => (
    <div
      ref={ref}
      className={cn(calloutVariants({ variant }), className)}
      role="note"
      {...props}
    >
      <div className="flex gap-3">
        {icon && <div className="flex-shrink-0 mt-0.5">{icon}</div>}
        <div className="flex-1">
          {title && <h4 className="font-semibold mb-1">{title}</h4>}
          {children}
        </div>
      </div>
    </div>
  )
);

Callout.displayName = "Callout";

export { Callout, calloutVariants };
export type { CalloutProps };
