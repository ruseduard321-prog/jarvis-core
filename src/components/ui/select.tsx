"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";
import { ChevronDown } from "lucide-react";

const selectVariants = cva(
  "flex items-center justify-between rounded-md border-2 border-input bg-background px-3 py-2 text-sm ring-ring placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 transition-colors duration-200 w-full cursor-pointer",
  {
    variants: {
      variant: {
        default: "border-input hover:border-primary/30 focus-visible:border-primary",
        error:
          "border-destructive hover:border-destructive/70 focus-visible:border-destructive",
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

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "children" | "size">,
    VariantProps<typeof selectVariants> {
  options: SelectOption[];
  placeholder?: string;
  error?: string;
  label?: string;
  description?: string;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      className,
      variant,
      size,
      options,
      placeholder = "Select an option",
      error,
      label,
      description,
      value,
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
        <div className="relative">
          <select
            ref={ref}
            className={cn(
              selectVariants({
                variant: isError ? "error" : variant,
                size,
              }),
              "appearance-none pr-8",
              className
            )}
            aria-invalid={!!isError}
            value={value}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option
                key={option.value}
                value={option.value}
                disabled={option.disabled}
              >
                {option.label}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        </div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
        {error && <p className="text-xs text-destructive mt-1">{error}</p>}
      </div>
    );
  }
);

Select.displayName = "Select";

export { Select, selectVariants };
export type { SelectProps, SelectOption };
