"use client";

import { LucideIcon } from "lucide-react";
import { TrendingUp, TrendingDown } from "lucide-react";

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: number;
  trend: "up" | "down" | "neutral";
}

/**
 * Reusable Statistic Card
 * Displays a single metric with icon and trend
 */
export function StatCard({ icon: Icon, label, value, trend }: StatCardProps) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg p-6 border border-gray-200 dark:border-gray-800 hover:shadow-md dark:hover:shadow-md dark:hover:shadow-gray-800 transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{label}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{value.toLocaleString()}</p>
        </div>
        <div className={`p-3 rounded-lg ${
          trend === "up" ? "bg-green-100 dark:bg-green-900" :
          trend === "down" ? "bg-red-100 dark:bg-red-900" :
          "bg-blue-100 dark:bg-blue-900"
        }`}>
          <Icon className={`w-6 h-6 ${
            trend === "up" ? "text-green-600" :
            trend === "down" ? "text-red-600" :
            "text-blue-600"
          }`} />
        </div>
      </div>
      {trend !== "neutral" && (
        <div className="flex items-center mt-4 gap-2">
          {trend === "up" ? (
            <>
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-600 font-medium">Increasing</span>
            </>
          ) : (
            <>
              <TrendingDown className="w-4 h-4 text-red-600" />
              <span className="text-sm text-red-600 font-medium">Decreasing</span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
