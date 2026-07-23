export type AgentUiSection = "system" | "business";

export interface AgentUiConfig {
  icon: string;
  color: string;
  shortDescription: string;
  section: AgentUiSection;
}

export const AGENT_UI_CONFIG_BY_SLUG: Record<string, AgentUiConfig> = {
  general: {
    icon: "sparkles",
    color: "slate",
    shortDescription: "Default assistant for broad support tasks.",
    section: "system",
  },
  strategy: {
    icon: "target",
    color: "amber",
    shortDescription: "Opportunity and priority planning.",
    section: "business",
  },
  research: {
    icon: "search",
    color: "sky",
    shortDescription: "Reliable information gathering.",
    section: "business",
  },
  creation: {
    icon: "pen",
    color: "violet",
    shortDescription: "Production-ready content creation.",
    section: "business",
  },
  review: {
    icon: "shield-check",
    color: "emerald",
    shortDescription: "Quality and consistency validation.",
    section: "business",
  },
  media: {
    icon: "image",
    color: "rose",
    shortDescription: "Media asset planning responsibilities.",
    section: "business",
  },
  publishing: {
    icon: "send",
    color: "indigo",
    shortDescription: "Distribution and delivery responsibilities.",
    section: "business",
  },
  analytics: {
    icon: "line-chart",
    color: "teal",
    shortDescription: "KPI measurement and feedback.",
    section: "business",
  },
};
