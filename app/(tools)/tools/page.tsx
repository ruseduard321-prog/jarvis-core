"use client";

import { useTools } from "@/hooks/use-tool-queries";

export default function ToolsPage() {
  const { data: tools = [], isLoading, error } = useTools();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <p className="text-sm text-muted-foreground">Loading tools...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="text-sm text-red-600">Failed to load tools</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Tools</h1>
        <p className="text-sm text-muted-foreground">Available internal tools and metadata.</p>
      </div>

      <div className="overflow-hidden rounded-md border border-border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-left text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Slug</th>
              <th className="px-4 py-3">Capabilities</th>
              <th className="px-4 py-3">Description</th>
            </tr>
          </thead>
          <tbody>
            {tools.map((tool) => (
              <tr key={tool.slug} className="border-t border-border">
                <td className="px-4 py-3 font-medium text-foreground">{tool.name}</td>
                <td className="px-4 py-3 text-muted-foreground">{tool.slug}</td>
                <td className="px-4 py-3 text-muted-foreground">{tool.capabilities.join(", ")}</td>
                <td className="px-4 py-3 text-muted-foreground">{tool.description}</td>
              </tr>
            ))}
            {tools.length === 0 && (
              <tr>
                <td className="px-4 py-6 text-center text-muted-foreground" colSpan={4}>
                  No tools available.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
