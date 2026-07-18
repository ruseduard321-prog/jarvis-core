"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const alertVariants = cva(
  "relative w-full rounded-lg border-2 p-4 text-sm transition-all duration-200",
  {
    variants: {
      variant: {
        default:
          "border-primary/20 bg-primary/5 text-primary [&>svg]:text-primary",
        destructive:
          "border-destructive/20 bg-destructive/5 text-destructive [&>svg]:text-destructive",
        success:
          "border-green-600/20 bg-green-600/5 text-green-700 dark:text-green-400 [&>svg]:text-green-600",
        warning:
          "border-yellow-600/20 bg-yellow-600/5 text-yellow-700 dark:text-yellow-400 [&>svg]:text-yellow-600",
        info: "border-blue-600/20 bg-blue-600/5 text-blue-700 dark:text-blue-400 [&>svg]:text-blue-600",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

interface AlertProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, 'title'>,
    VariantProps<typeof alertVariants> {
  icon?: React.ReactNode;
  title?: React.ReactNode;
  closable?: boolean;
  onClose?: () => void;
}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  (
    { className, variant, icon, title, closable, onClose, children, ...props },
    ref
  ) => {
    const [isVisible, setIsVisible] = React.useState(true);

    const handleClose = () => {
      setIsVisible(false);
      onClose?.();
    };

    if (!isVisible) return null;

    return (
      <div
        ref={ref}
        className={cn(alertVariants({ variant }), className)}
        role="alert"
        {...props}
      >
        <div className="flex gap-3">
          {icon && <div className="flex-shrink-0 mt-0.5">{icon}</div>}
          <div className="flex-1">
            {title && <h3 className="font-semibold mb-1">{title}</h3>}
            {children}
          </div>
          {closable && (
            <button
              onClick={handleClose}
              className="flex-shrink-0 ml-2 text-current opacity-70 hover:opacity-100 transition-opacity"
              aria-label="Close alert"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>
      </div>
    );
  }
);

Alert.displayName = "Alert";

export { Alert, alertVariants };
export type { AlertProps };
