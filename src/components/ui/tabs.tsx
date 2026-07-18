"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const tabsVariants = cva("", {
  variants: {
    variant: {
      line: "",
      pill: "",
      enclosed: "",
    },
  },
  defaultVariants: {
    variant: "line",
  },
});

interface Tab {
  id: string;
  label: React.ReactNode;
  content: React.ReactNode;
  disabled?: boolean;
  icon?: React.ReactNode;
}

interface TabsProps extends VariantProps<typeof tabsVariants> {
  tabs: Tab[];
  defaultTab?: string;
  onChange?: (tabId: string) => void;
  className?: string;
  fullWidth?: boolean;
}

const Tabs = React.forwardRef<HTMLDivElement, TabsProps>(
  (
    {
      tabs,
      defaultTab,
      onChange,
      className,
      fullWidth,
      variant = "line",
    },
    ref
  ) => {
    const [activeTab, setActiveTab] = React.useState(
      defaultTab || tabs[0]?.id
    );

    const handleTabChange = (tabId: string) => {
      setActiveTab(tabId);
      onChange?.(tabId);
    };

    return (
      <div ref={ref} className={cn("w-full", className)}>
        <div
          className={cn(
            "flex border-b border-border",
            fullWidth && "justify-between"
          )}
          role="tablist"
        >
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              disabled={tab.disabled}
              className={cn(
                "px-4 py-3 text-sm font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed relative",
                fullWidth && "flex-1",
                activeTab === tab.id
                  ? "text-primary border-b-2 border-primary"
                  : "text-muted-foreground hover:text-foreground",
                variant === "pill" &&
                  activeTab === tab.id &&
                  "bg-primary/10 rounded-t-lg border-0",
                variant === "enclosed" &&
                  activeTab === tab.id &&
                  "bg-background border border-b-0 border-border rounded-t-lg"
              )}
              role="tab"
              aria-selected={activeTab === tab.id}
              aria-controls={`panel-${tab.id}`}
            >
              <span className="flex items-center gap-2">
                {tab.icon}
                {tab.label}
              </span>
            </button>
          ))}
        </div>
        {tabs.map((tab) => (
          <div
            key={`panel-${tab.id}`}
            id={`panel-${tab.id}`}
            role="tabpanel"
            hidden={activeTab !== tab.id}
            className="mt-4"
          >
            {activeTab === tab.id && tab.content}
          </div>
        ))}
      </div>
    );
  }
);

Tabs.displayName = "Tabs";

export { Tabs, tabsVariants };
export type { TabsProps, Tab };
