"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const textareaVariants = cva(
  "flex rounded-md border-2 border-input bg-background px-3 py-2 text-sm ring-ring placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 transition-colors duration-200 font-mono resize-none",
  {
    variants: {
      variant: {
        default: "border-input hover:border-primary/30 focus-visible:border-primary",
        error:
          "border-destructive hover:border-destructive/70 focus-visible:border-destructive focus-visible:ring-destructive",
      },
      size: {
        sm: "min-h-20 text-xs px-2 py-1",
        md: "min-h-24 text-sm px-3 py-2",
        lg: "min-h-32 text-base px-4 py-3",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement>,
    VariantProps<typeof textareaVariants> {
  error?: string;
  label?: string;
  description?: string;
  charLimit?: number;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      className,
      variant,
      size,
      error,
      label,
      description,
      charLimit,
      value,
      onChange,
      ...props
    },
    ref
  ) => {
    const isError = error || props["aria-invalid"];
    const charCount = value ? String(value).length : 0;
    const exceedsLimit = charLimit && charCount > charLimit;

    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium mb-1 text-foreground">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          className={cn(
            textareaVariants({
              variant: isError || exceedsLimit ? "error" : variant,
              size,
            }),
            className
          )}
          aria-invalid={isError ? true : exceedsLimit ? true : false}
          value={value}
          onChange={onChange}
          {...props}
        />
        <div className="flex items-center justify-between mt-1">
          <div>
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>
          {charLimit && (
            <p
              className={cn(
                "text-xs",
                exceedsLimit ? "text-destructive" : "text-muted-foreground"
              )}
            >
              {charCount}/{charLimit}
            </p>
          )}
        </div>
      </div>
    );
  }
);

Textarea.displayName = "Textarea";

export { Textarea, textareaVariants };
export type { TextareaProps };
