"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const skeletonVariants = cva("animate-pulse bg-muted rounded", {
  variants: {
    shape: {
      default: "rounded",
      circle: "rounded-full",
      square: "rounded-none",
    },
  },
  defaultVariants: {
    shape: "default",
  },
});

interface SkeletonProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof skeletonVariants> {}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, shape, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(skeletonVariants({ shape }), className)}
      {...props}
    />
  )
);

Skeleton.displayName = "Skeleton";

interface SkeletonGroupProps {
  count?: number;
  variant?: "text" | "avatar" | "card" | "list";
  className?: string;
}

const SkeletonGroup: React.FC<SkeletonGroupProps> = ({
  count = 1,
  variant = "text",
  className,
}) => {
  const renderVariant = () => {
    switch (variant) {
      case "avatar":
        return (
          <Skeleton shape="circle" className={cn("h-10 w-10", className)} />
        );
      case "card":
        return (
          <div className="space-y-2">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        );
      case "list":
        return (
          <div className="space-y-3">
            {Array.from({ length: count }).map((_, i) => (
              <div key={i} className="flex gap-2">
                <Skeleton shape="circle" className="h-10 w-10" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-3 w-3/4" />
                </div>
              </div>
            ))}
          </div>
        );
      default:
        return (
          <>
            {Array.from({ length: count }).map((_, i) => (
              <Skeleton key={i} className={cn("h-4 w-full mb-2", className)} />
            ))}
          </>
        );
    }
  };

  return <>{renderVariant()}</>;
};

SkeletonGroup.displayName = "SkeletonGroup";

export { Skeleton, SkeletonGroup, skeletonVariants };
export type { SkeletonProps, SkeletonGroupProps };
