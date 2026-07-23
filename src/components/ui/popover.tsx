"use client";

import React from "react";
import { cn } from "@/utils";

interface PopoverProps {
  trigger: React.ReactNode;
  children: React.ReactNode;
  side?: "top" | "right" | "bottom" | "left";
  align?: "start" | "center" | "end";
  onOpenChange?: (open: boolean) => void;
}

const Popover = React.forwardRef<HTMLDivElement, PopoverProps>(
  (
    {
      trigger,
      children,
      side = "bottom",
      align = "center",
      onOpenChange,
    },
    ref
  ) => {
    const [isOpen, setIsOpen] = React.useState(false);
    const triggerRef = React.useRef<HTMLDivElement>(null);
    const contentRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
      onOpenChange?.(isOpen);
    }, [isOpen, onOpenChange]);

    React.useEffect(() => {
      const handleClickOutside = (e: MouseEvent) => {
        if (
          contentRef.current &&
          !contentRef.current.contains(e.target as Node) &&
          triggerRef.current &&
          !triggerRef.current.contains(e.target as Node)
        ) {
          setIsOpen(false);
        }
      };

      if (isOpen) {
        document.addEventListener("mousedown", handleClickOutside);
      }
      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
      };
    }, [isOpen]);

    const sideClasses = {
      top: "bottom-full mb-2",
      bottom: "top-full mt-2",
      left: "right-full mr-2",
      right: "left-full ml-2",
    };

    const alignClasses = {
      start: {
        top: "left-0",
        bottom: "left-0",
        left: "top-0",
        right: "top-0",
      },
      center: {
        top: "left-1/2 -translate-x-1/2",
        bottom: "left-1/2 -translate-x-1/2",
        left: "top-1/2 -translate-y-1/2",
        right: "top-1/2 -translate-y-1/2",
      },
      end: {
        top: "right-0",
        bottom: "right-0",
        left: "bottom-0",
        right: "bottom-0",
      },
    };

    return (
      <div ref={ref} className="relative inline-block">
        {/* Use a div wrapper so any trigger (button, link, etc.) is valid HTML */}
        <div
          ref={triggerRef}
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex"
          role="presentation"
        >
          {trigger}
        </div>
        {isOpen && (
          <div
            ref={contentRef}
            className={cn(
              "absolute z-popover bg-background border border-border rounded-lg shadow-lg p-4 min-w-max",
              sideClasses[side],
              alignClasses[align][side]
            )}
          >
            {children}
          </div>
        )}
      </div>
    );
  }
);

Popover.displayName = "Popover";

export { Popover };
export type { PopoverProps };
