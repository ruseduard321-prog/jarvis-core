"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

interface RadioOption {
  value: string;
  label: string;
  description?: string;
}

interface RadioGroupProps extends VariantProps<typeof radioVariants> {
  options: RadioOption[];
  value?: string;
  onChange?: (value: string) => void;
  name?: string;
  disabled?: boolean;
  error?: string;
  label?: string;
  direction?: "horizontal" | "vertical";
}

const radioVariants = cva(
  "peer appearance-none h-4 w-4 border-2 border-primary rounded-full checked:bg-primary checked:border-primary checked:shadow-inner focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200",
  {
    variants: {
      size: {
        sm: "h-3 w-3",
        md: "h-4 w-4",
        lg: "h-5 w-5",
      },
    },
    defaultVariants: {
      size: "md",
    },
  }
);

const RadioGroup = React.forwardRef<
  HTMLFieldSetElement,
  RadioGroupProps
>(
  (
    {
      options,
      value,
      onChange,
      name = "radio-group",
      disabled,
      error,
      label,
      direction = "vertical",
      size,
    },
    ref
  ) => {
    const [selected, setSelected] = React.useState(value);

    const handleChange = (newValue: string) => {
      setSelected(newValue);
      onChange?.(newValue);
    };

    return (
      <fieldset ref={ref} disabled={disabled} className="space-y-2">
        {label && (
          <legend className="text-sm font-medium text-foreground mb-3">
            {label}
          </legend>
        )}
        <div
          className={cn(
            "space-y-2",
            direction === "horizontal" && "flex flex-wrap gap-4"
          )}
        >
          {options.map((option) => (
            <div key={option.value} className="flex items-start space-x-2">
              <input
                type="radio"
                id={`${name}-${option.value}`}
                name={name}
                value={option.value}
                checked={selected === option.value}
                onChange={(e) => handleChange(e.target.value)}
                className={cn(radioVariants({ size }))}
              />
              <div>
                <label
                  htmlFor={`${name}-${option.value}`}
                  className="text-sm font-medium cursor-pointer"
                >
                  {option.label}
                </label>
                {option.description && (
                  <p className="text-xs text-muted-foreground">
                    {option.description}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
        {error && <p className="text-xs text-destructive mt-2">{error}</p>}
      </fieldset>
    );
  }
);

RadioGroup.displayName = "RadioGroup";

export { RadioGroup, radioVariants };
export type { RadioGroupProps, RadioOption };
