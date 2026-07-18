"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const separatorVariants = cva("shrink-0 bg-border", {
  variants: {
    orientation: {
      horizontal: "h-px w-full",
      vertical: "h-full w-px",
    },
  },
  defaultVariants: {
    orientation: "horizontal",
  },
});

interface SeparatorProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof separatorVariants> {
  decorative?: boolean;
}

const Separator = React.forwardRef<HTMLDivElement, SeparatorProps>(
  ({ className, orientation = "horizontal", decorative, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(separatorVariants({ orientation }), className)}
      role={decorative ? "none" : "separator"}
      aria-orientation={orientation === "vertical" ? "vertical" : "horizontal"}
      {...props}
    />
  )
);

Separator.displayName = "Separator";

export { Separator, separatorVariants };
export type { SeparatorProps };
