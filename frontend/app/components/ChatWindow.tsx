"use client";

import { Activity, BookOpen, History, Wrench, CheckCircle2, Loader2 } from "lucide-react";

export type AgentStatus = "idle" | "running" | "complete" | "error";

export interface AgentCard {
  key: "log_analyst" | "runbook_rag" | "incident_history" | "remediation";
  label: string;
  icon: React.ReactNode;
  description: string;
  status: AgentStatus;
  output: string;
}

interface ChatWindowProps {
  agents: AgentCard[];
}

const statusColors: Record<AgentStatus, string> = {
  idle: "text-muted-foreground border-border",
  running: "text-primary border-primary/50 bg-primary/5",
  complete: "text-emerald-400 border-emerald-500/40 bg-emerald-500/5",
  error: "text-destructive border-destructive/50 bg-destructive/5",
};

const statusBadge: Record<AgentStatus, React.ReactNode> = {
  idle: <span className="text-xs text-muted-foreground px-2 py-0.5 rounded-full border border-border">Waiting</span>,
  running: (
    <span className="flex items-center gap-1 text-xs text-primary px-2 py-0.5 rounded-full border border-primary/40 bg-primary/10">
      <Loader2 className="w-3 h-3 animate-spin" />
      Running
    </span>
  ),
  complete: (
    <span className="flex items-center gap-1 text-xs text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/40 bg-emerald-500/10">
      <CheckCircle2 className="w-3 h-3" />
      Complete
    </span>
  ),
  error: <span className="text-xs text-destructive px-2 py-0.5 rounded-full border border-destructive/40 bg-destructive/10">Error</span>,
};

export default function ChatWindow({ agents }: ChatWindowProps) {
  const hasActivity = agents.some((a) => a.status !== "idle");

  if (!hasActivity) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
        <div className="w-16 h-16 rounded-full bg-secondary border border-border flex items-center justify-center">
          <Activity className="w-7 h-7 text-muted-foreground" />
        </div>
        <div>
          <p className="text-muted-foreground text-sm">No active triage</p>
          <p className="text-muted-foreground/60 text-xs mt-1">
            Describe an incident and click Triage Incident to begin
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 h-full overflow-y-auto pr-1">
      <div className="flex items-center gap-2 pb-2 border-b border-border">
        <Activity className="w-5 h-5 text-primary" />
        <h2 className="font-semibold text-foreground">Agent Pipeline</h2>
      </div>

      {agents.map((agent) => (
        <div
          key={agent.key}
          className={`rounded-lg border p-4 transition-all duration-300 ${statusColors[agent.status]}`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className={agent.status === "running" ? "animate-pulse" : ""}>{agent.icon}</span>
              <span className="font-medium text-sm">{agent.label}</span>
            </div>
            {statusBadge[agent.status]}
          </div>

          <p className="text-xs text-muted-foreground mb-2">{agent.description}</p>

          {agent.status === "running" && (
            <div className="space-y-1.5 mt-3">
              <div className="h-1.5 bg-primary/20 rounded-full overflow-hidden">
                <div className="h-full bg-primary/60 rounded-full animate-pulse w-3/4" />
              </div>
            </div>
          )}

          {agent.output && agent.status !== "idle" && (
            <div className="mt-3 text-xs text-foreground/80 bg-background/40 rounded-md p-3 font-mono whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto fade-in border border-border/50">
              {agent.output}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
