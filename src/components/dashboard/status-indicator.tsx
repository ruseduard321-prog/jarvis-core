"use client";

import { StatusIndicator as StatusIndicatorType } from "@/types";
import { CheckCircle, AlertCircle, XCircle } from "lucide-react";

interface StatusIndicatorProps {
  indicator: StatusIndicatorType;
}

/**
 * Status Indicator
 * Displays health status of a system component
 */
export function StatusIndicator({ indicator }: StatusIndicatorProps) {
  const getStatusStyles = () => {
    switch (indicator.status) {
      case "online":
        return {
          icon: CheckCircle,
          bg: "bg-green-100 dark:bg-green-900",
          text: "text-green-600 dark:text-green-400",
          badge: "bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-100",
        };
      case "degraded":
        return {
          icon: AlertCircle,
          bg: "bg-yellow-100 dark:bg-yellow-900",
          text: "text-yellow-600 dark:text-yellow-400",
          badge: "bg-yellow-200 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-100",
        };
      case "offline":
        return {
          icon: XCircle,
          bg: "bg-red-100 dark:bg-red-900",
          text: "text-red-600 dark:text-red-400",
          badge: "bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-100",
        };
      default:
        return {
          icon: AlertCircle,
          bg: "bg-gray-100 dark:bg-gray-800",
          text: "text-gray-600 dark:text-gray-400",
          badge: "bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-100",
        };
    }
  };

  const styles = getStatusStyles();
  const Icon = styles.icon;

  return (
    <div className={`${styles.bg} rounded-lg p-4`}>
      <div className="flex items-start gap-3">
        <Icon className={`${styles.text} w-6 h-6 mt-0.5 flex-shrink-0`} />
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 dark:text-white">{indicator.name}</h3>
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{indicator.message}</p>
          <div className="mt-3 flex items-center gap-2">
            <span className={`px-2 py-1 rounded text-xs font-medium ${styles.badge}`}>
              {indicator.status.charAt(0).toUpperCase() + indicator.status.slice(1)}
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {new Date(indicator.timestamp).toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
