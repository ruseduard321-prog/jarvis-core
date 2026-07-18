"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

const avatarVariants = cva(
  "relative inline-flex items-center justify-center bg-muted text-muted-foreground font-semibold rounded-full flex-shrink-0",
  {
    variants: {
      size: {
        xs: "h-6 w-6 text-xs",
        sm: "h-8 w-8 text-sm",
        md: "h-10 w-10 text-base",
        lg: "h-12 w-12 text-lg",
        xl: "h-16 w-16 text-2xl",
      },
    },
    defaultVariants: {
      size: "md",
    },
  }
);

interface AvatarProps
  extends React.ImgHTMLAttributes<HTMLImageElement>,
    VariantProps<typeof avatarVariants> {
  initials?: string;
  status?: "online" | "offline" | "away" | "idle";
  fallback?: React.ReactNode;
}

const Avatar = React.forwardRef<HTMLImageElement, AvatarProps>(
  (
    {
      className,
      size,
      alt = "Avatar",
      initials,
      status,
      fallback,
      src,
      ...props
    },
    ref
  ) => {
    const [imageError, setImageError] = React.useState(false);

    return (
      <div className="relative inline-flex">
        {!imageError && src ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            ref={ref}
            src={src}
            alt={alt}
            className={cn(avatarVariants({ size }), className)}
            onError={() => setImageError(true)}
            {...props}
          />
        ) : (
          <div
            className={cn(
              avatarVariants({ size }),
              "bg-gradient-to-br from-primary to-primary/60",
              className
            )}
          >
            {fallback || initials || "?"}
          </div>
        )}
        {status && (
          <span
            className={cn(
              "absolute bottom-0 right-0 rounded-full border-2 border-background",
              {
                xs: "h-2 w-2",
                sm: "h-2.5 w-2.5",
                md: "h-3 w-3",
                lg: "h-3.5 w-3.5",
                xl: "h-4 w-4",
              }[size || "md"],
              {
                online: "bg-green-600",
                offline: "bg-gray-400",
                away: "bg-yellow-600",
                idle: "bg-blue-600",
              }[status]
            )}
            title={`Status: ${status}`}
          />
        )}
      </div>
    );
  }
);

Avatar.displayName = "Avatar";

export { Avatar, avatarVariants };
export type { AvatarProps };
