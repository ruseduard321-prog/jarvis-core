"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const iconButtonVariants = cva(
  "inline-flex items-center justify-center rounded-md font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-offset-background",
  {
    variants: {
      variant: {
        solid: "bg-primary text-primary-foreground hover:opacity-90 active:opacity-75",
        outline: "border-2 border-primary text-primary hover:bg-primary/10 active:bg-primary/20",
        ghost: "text-primary hover:bg-primary/10 active:bg-primary/20",
        destructive: "bg-destructive text-destructive-foreground hover:opacity-90 active:opacity-75",
      },
      size: {
        sm: "h-8 w-8",
        md: "h-10 w-10",
        lg: "h-12 w-12",
      },
    },
    defaultVariants: {
      variant: "solid",
      size: "md",
    },
  }
);

interface IconButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof iconButtonVariants> {
  children: React.ReactNode;
}

const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    { className, variant, size, children, ...props },
    ref
  ) => (
    <button
      className={cn(iconButtonVariants({ variant, size }), className)}
      ref={ref}
      {...props}
    >
      {children}
    </button>
  )
);

IconButton.displayName = "IconButton";

export { IconButton, iconButtonVariants };
export type { IconButtonProps };
