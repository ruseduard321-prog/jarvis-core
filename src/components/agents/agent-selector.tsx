"use client";

import type { Agent } from "@/types";
import { AGENT_UI_CONFIG_BY_SLUG } from "@/config/agent-ui-config";

interface AgentSelectorProps {
  agents: Agent[];
  selectedAgentId: string | null;
  onSelectAgent: (agentId: string) => void;
  disabled?: boolean;
}

export function AgentSelector({
  agents,
  selectedAgentId,
  onSelectAgent,
  disabled = false,
}: AgentSelectorProps) {
  const selectedAgent = agents.find((agent) => agent.id === selectedAgentId) ?? null;
  const systemAgents = agents.filter(
    (agent) => AGENT_UI_CONFIG_BY_SLUG[agent.slug]?.section === "system"
  );
  const businessAgents = agents.filter(
    (agent) => AGENT_UI_CONFIG_BY_SLUG[agent.slug]?.section !== "system"
  );

  const renderAgentCard = (agent: Agent) => {
    const ui = AGENT_UI_CONFIG_BY_SLUG[agent.slug];

    return (
      <button
        key={agent.id}
        type="button"
        onClick={() => onSelectAgent(agent.id)}
        disabled={disabled || agents.length === 0}
        className={`rounded-md border px-3 py-2 text-left transition-colors ${
          agent.id === selectedAgentId
            ? "border-primary bg-primary/10"
            : "border-border bg-background hover:bg-accent"
        } ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
      >
        <div className="flex items-center gap-2">
          <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
            {ui?.icon ?? "agent"}
          </span>
          <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
            {ui?.color ?? "default"}
          </span>
        </div>
        <p className="mt-2 text-sm font-semibold text-foreground">{agent.name}</p>
        <p className="mt-1 text-xs text-muted-foreground">
          {ui?.shortDescription ?? "AI business agent"}
        </p>
        <p className="mt-2 text-xs text-foreground/90">Mission: {agent.mission}</p>
      </button>
    );
  };

  return (
    <div className="border-b border-border bg-muted/20 p-3">
      <p className="mb-2 text-sm font-medium text-foreground">Agent</p>
      <div className="space-y-4">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">System</p>
          <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">{systemAgents.map(renderAgentCard)}</div>
        </div>
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Business</p>
          <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">{businessAgents.map(renderAgentCard)}</div>
        </div>
      </div>
      {selectedAgent && (
        <p className="mt-2 text-xs text-muted-foreground">
          Selected: {selectedAgent.name}
        </p>
      )}
    </div>
  );
}
