"use client";

import React from "react";
import { cn } from "@/utils";

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  side?: "top" | "right" | "bottom" | "left";
  delayMs?: number;
}

const Tooltip = React.forwardRef<HTMLDivElement, TooltipProps>(
  (
    {
      content,
      children,
      side = "top",
      delayMs = 200,
    },
    ref
  ) => {
    const [isVisible, setIsVisible] = React.useState(false);
    const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);
    const [position, setPosition] = React.useState({ top: 0, left: 0 });
    const triggerRef = React.useRef<HTMLDivElement>(null);
    const tooltipRef = React.useRef<HTMLDivElement>(null);

    const showTooltip = () => {
      timeoutRef.current = setTimeout(() => {
        if (triggerRef.current) {
          const rect = triggerRef.current.getBoundingClientRect();
          const tooltipTop = side === "top" ? rect.top - 8 : rect.bottom + 8;
          const tooltipLeft = rect.left + rect.width / 2;
          setPosition({ top: tooltipTop, left: tooltipLeft });
          setIsVisible(true);
        }
      }, delayMs);
    };

    const hideTooltip = () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      setIsVisible(false);
    };

    const sideClasses = {
      top: "-translate-y-full",
      bottom: "translate-y-0",
      left: "-translate-x-full",
      right: "translate-x-0",
    };

    return (
      <div
        ref={ref}
        className="inline-block"
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
      >
        <div ref={triggerRef}>{children}</div>
        {isVisible && (
          <div
            ref={tooltipRef}
            role="tooltip"
            className={cn(
              "fixed z-tooltip bg-foreground text-background px-2 py-1 text-xs rounded pointer-events-none -translate-x-1/2 whitespace-nowrap",
              sideClasses[side]
            )}
            style={{
              top: `${position.top}px`,
              left: `${position.left}px`,
            }}
          >
            {content}
            <div
              className={cn(
                "absolute w-2 h-2 bg-foreground",
                {
                  top: "bottom-[-4px] left-1/2 -translate-x-1/2 rotate-45",
                  bottom: "top-[-4px] left-1/2 -translate-x-1/2 rotate-45",
                  left: "right-[-4px] top-1/2 -translate-y-1/2 rotate-45",
                  right: "left-[-4px] top-1/2 -translate-y-1/2 rotate-45",
                }[side]
              )}
            />
          </div>
        )}
      </div>
    );
  }
);

Tooltip.displayName = "Tooltip";

export { Tooltip };
export type { TooltipProps };
