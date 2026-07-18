"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const inputVariants = cva(
  "flex rounded-md border-2 border-input bg-background px-3 py-2 text-sm ring-ring placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 transition-colors duration-200",
  {
    variants: {
      variant: {
        default: "border-input hover:border-primary/30 focus-visible:border-primary",
        error:
          "border-destructive hover:border-destructive/70 focus-visible:border-destructive focus-visible:ring-destructive",
      },
      size: {
        sm: "h-8 text-xs px-2 py-1",
        md: "h-10 text-sm px-3 py-2",
        lg: "h-12 text-base px-4 py-3",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  error?: string;
  label?: string;
  description?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      variant,
      size,
      error,
      label,
      description,
      leftIcon,
      rightIcon,
      ...props
    },
    ref
  ) => {
    const isError = error || props["aria-invalid"];

    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium mb-1 text-foreground">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3 text-muted-foreground pointer-events-none">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            className={cn(
              inputVariants({
                variant: isError ? "error" : variant,
                size,
              }),
              leftIcon && "pl-10",
              rightIcon && "pr-10",
              className
            )}
            aria-invalid={!!isError}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 text-muted-foreground pointer-events-none">
              {rightIcon}
            </div>
          )}
        </div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
        {error && <p className="text-xs text-destructive mt-1">{error}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input, inputVariants };
export type { InputProps };
