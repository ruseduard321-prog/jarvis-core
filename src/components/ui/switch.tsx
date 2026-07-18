"use client";

import React, { useState } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const switchVariants = cva(
  "inline-flex h-6 w-11 items-center rounded-full border-2 border-input bg-background px-0.5 transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "hover:border-primary/30 data-[state=checked]:bg-primary data-[state=checked]:border-primary",
        secondary:
          "data-[state=checked]:bg-secondary data-[state=checked]:border-secondary",
      },
      size: {
        sm: "h-5 w-9",
        md: "h-6 w-11",
        lg: "h-7 w-14",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

interface SwitchProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type" | "size">,
    VariantProps<typeof switchVariants> {
  label?: string;
  description?: string;
}

const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(
  (
    { variant, size, label, description, id, checked, onChange, ...props },
    ref
  ) => {
    const [isChecked, setIsChecked] = useState(!!checked);
    const switchId = id || `switch-${Math.random().toString(36).substr(2, 9)}`;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setIsChecked(e.target.checked);
      onChange?.(e);
    };

    return (
      <div className="flex items-center space-x-3">
        <div className="relative">
          <input
            ref={ref}
            type="checkbox"
            id={switchId}
            checked={isChecked}
            onChange={handleChange}
            className="sr-only"
            {...props}
          />
          <label
            htmlFor={switchId}
            className={cn(
              switchVariants({ variant, size }),
              "cursor-pointer relative"
            )}
          >
            <span
              className={cn(
                "inline-block h-5 w-5 transform rounded-full bg-background transition-transform duration-200 absolute top-0.5 left-0.5",
                isChecked && "translate-x-5"
              )}
            />
          </label>
        </div>
        {label && (
          <div className="flex flex-col space-y-0.5">
            <label
              htmlFor={switchId}
              className="text-sm font-medium cursor-pointer"
            >
              {label}
            </label>
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
        )}
      </div>
    );
  }
);

Switch.displayName = "Switch";

export { Switch, switchVariants };
export type { SwitchProps };
