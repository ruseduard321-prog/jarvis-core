"use client";

import React from "react";
import { cn } from "@/utils";
import { ChevronDown } from "lucide-react";

interface AccordionItem {
  id: string;
  title: React.ReactNode;
  content: React.ReactNode;
  icon?: React.ReactNode;
  disabled?: boolean;
}

interface AccordionProps {
  items: AccordionItem[];
  defaultExpanded?: string[];
  allowMultiple?: boolean;
  onChange?: (expandedIds: string[]) => void;
  className?: string;
}

const Accordion = React.forwardRef<HTMLDivElement, AccordionProps>(
  (
    {
      items,
      defaultExpanded = [],
      allowMultiple = false,
      onChange,
      className,
    },
    ref
  ) => {
    const [expandedItems, setExpandedItems] = React.useState<string[]>(
      defaultExpanded
    );

    const toggleItem = (id: string) => {
      let newExpanded: string[];
      if (expandedItems.includes(id)) {
        newExpanded = expandedItems.filter((item) => item !== id);
      } else if (allowMultiple) {
        newExpanded = [...expandedItems, id];
      } else {
        newExpanded = [id];
      }
      setExpandedItems(newExpanded);
      onChange?.(newExpanded);
    };

    return (
      <div ref={ref} className={cn("space-y-2 border border-border rounded-lg overflow-hidden", className)}>
        {items.map((item) => {
          const isExpanded = expandedItems.includes(item.id);
          return (
            <div
              key={item.id}
              className={cn(
                "border-b border-border last:border-b-0",
                isExpanded && "bg-muted/30"
              )}
            >
              <button
                onClick={() => toggleItem(item.id)}
                disabled={item.disabled}
                className="w-full px-4 py-3 flex items-center justify-between text-sm font-medium hover:bg-muted/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                aria-expanded={isExpanded}
                aria-controls={`content-${item.id}`}
              >
                <span className="flex items-center gap-2">
                  {item.icon}
                  {item.title}
                </span>
                <ChevronDown
                  className={cn(
                    "h-4 w-4 text-muted-foreground transition-transform duration-200",
                    isExpanded && "rotate-180"
                  )}
                />
              </button>
              {isExpanded && (
                <div
                  id={`content-${item.id}`}
                  className="px-4 py-3 text-sm text-muted-foreground border-t border-border/50"
                >
                  {item.content}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  }
);

Accordion.displayName = "Accordion";

export { Accordion };
export type { AccordionProps, AccordionItem };
