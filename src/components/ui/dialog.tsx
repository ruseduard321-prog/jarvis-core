"use client";

import React from "react";
import { cn } from "@/utils";
import { X } from "lucide-react";

interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  description?: React.ReactNode;
  children?: React.ReactNode;
  footer?: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
  closeButton?: boolean;
  backdrop?: boolean;
}

const sizeClasses = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
};

const Dialog = React.forwardRef<HTMLDivElement, DialogProps>(
  (
    {
      isOpen,
      onClose,
      title,
      description,
      children,
      footer,
      size = "md",
      closeButton = true,
      backdrop = true,
    },
    ref
  ) => {
    React.useEffect(() => {
      if (isOpen) {
        document.body.style.overflow = "hidden";
      } else {
        document.body.style.overflow = "unset";
      }
      return () => {
        document.body.style.overflow = "unset";
      };
    }, [isOpen]);

    if (!isOpen) return null;

    return (
      <div className="fixed inset-0 z-modal flex items-center justify-center">
        {backdrop && (
          <div
            className="absolute inset-0 bg-background/80 backdrop-blur-sm"
            onClick={onClose}
            aria-hidden="true"
          />
        )}
        <div
          ref={ref}
          role="dialog"
          aria-modal="true"
          aria-labelledby="dialog-title"
          className={cn(
            "relative bg-background border border-border rounded-lg shadow-lg p-6 w-full mx-4",
            sizeClasses[size]
          )}
        >
          {closeButton && (
            <button
              onClick={onClose}
              className="absolute right-4 top-4 p-1 hover:bg-muted rounded transition-colors"
              aria-label="Close dialog"
            >
              <X className="h-4 w-4" />
            </button>
          )}

          {title && (
            <h2 id="dialog-title" className="text-lg font-semibold mb-2">
              {title}
            </h2>
          )}
          {description && (
            <p className="text-sm text-muted-foreground mb-4">{description}</p>
          )}

          <div className="mb-6">{children}</div>

          {footer && <div className="flex gap-2 justify-end">{footer}</div>}
        </div>
      </div>
    );
  }
);

Dialog.displayName = "Dialog";

export { Dialog };
export type { DialogProps };
