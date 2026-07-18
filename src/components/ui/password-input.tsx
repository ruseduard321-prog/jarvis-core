"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";
import { Eye, EyeOff } from "lucide-react";

const passwordInputVariants = cva(
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

interface PasswordInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof passwordInputVariants> {
  error?: string;
  label?: string;
  description?: string;
  showStrengthMeter?: boolean;
}

const PasswordInput = React.forwardRef<HTMLInputElement, PasswordInputProps>(
  (
    {
      className,
      variant,
      size,
      error,
      label,
      description,
      showStrengthMeter,
      value,
      ...props
    },
    ref
  ) => {
    const [showPassword, setShowPassword] = React.useState(false);
    const isError = error || props["aria-invalid"];

    const getPasswordStrength = (pwd: string) => {
      if (!pwd) return 0;
      let strength = 0;
      if (pwd.length >= 8) strength++;
      if (pwd.length >= 12) strength++;
      if (/[a-z]/.test(pwd)) strength++;
      if (/[A-Z]/.test(pwd)) strength++;
      if (/[0-9]/.test(pwd)) strength++;
      if (/[^A-Za-z0-9]/.test(pwd)) strength++;
      return Math.min(strength, 4);
    };

    const strength = getPasswordStrength(String(value || ""));
    const strengthLabels = ["Very Weak", "Weak", "Fair", "Good", "Strong"];
    const strengthColors = [
      "bg-destructive",
      "bg-yellow-600",
      "bg-blue-600",
      "bg-blue-600",
      "bg-green-600",
    ];

    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium mb-1 text-foreground">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          <input
            ref={ref}
            type={showPassword ? "text" : "password"}
            className={cn(
              passwordInputVariants({
                variant: isError ? "error" : variant,
                size,
              }),
              "pr-10",
              className
            )}
            aria-invalid={!!isError}
            value={value}
            {...props}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 text-muted-foreground hover:text-foreground transition-colors"
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </button>
        </div>
        {showStrengthMeter && value && (
          <div className="mt-2 space-y-1">
            <div className="flex gap-1">
              {Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "h-1 flex-1 rounded-full bg-muted transition-colors",
                    i < strength && strengthColors[strength]
                  )}
                />
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              Strength: {strengthLabels[strength]}
            </p>
          </div>
        )}
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
        {error && <p className="text-xs text-destructive mt-1">{error}</p>}
      </div>
    );
  }
);

PasswordInput.displayName = "PasswordInput";

export { PasswordInput, passwordInputVariants };
export type { PasswordInputProps };
