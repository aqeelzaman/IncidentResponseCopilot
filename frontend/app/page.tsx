"use client";

import { useState, useCallback } from "react";
import { Activity, BookOpen, History, Wrench } from "lucide-react";
import IncidentInput from "./components/IncidentInput";
import ChatWindow, { AgentCard, AgentStatus } from "./components/ChatWindow";
import TriageReport from "./components/TriageReport";

const INITIAL_AGENTS: AgentCard[] = [
  {
    key: "log_analyst",
    label: "Log Analyst",
    icon: <Activity className="w-4 h-4" />,
    description: "Queries BigQuery for error spikes and anomalous metrics",
    status: "idle",
    output: "",
  },
  {
    key: "runbook_rag",
    label: "Runbook RAG",
    icon: <BookOpen className="w-4 h-4" />,
    description: "Semantic search over 50 SRE runbooks in Pinecone",
    status: "idle",
    output: "",
  },
  {
    key: "incident_history",
    label: "Incident History",
    icon: <History className="w-4 h-4" />,
    description: "Finds similar past incidents and their resolutions",
    status: "idle",
    output: "",
  },
  {
    key: "remediation",
    label: "Remediation Agent",
    icon: <Wrench className="w-4 h-4" />,
    description: "Self-reflection chain: draft → critique → final recommendation",
    status: "idle",
    output: "",
  },
];

type AgentKey = AgentCard["key"];

export default function Home() {
  const [agents, setAgents] = useState<AgentCard[]>(INITIAL_AGENTS);
  const [isLoading, setIsLoading] = useState(false);
  const [traceId, setTraceId] = useState("");
  const [isComplete, setIsComplete] = useState(false);

  const remediationOutput =
    agents.find((a) => a.key === "remediation")?.output ?? "";

  const updateAgent = useCallback(
    (key: AgentKey, updates: Partial<Pick<AgentCard, "status" | "output">>) => {
      setAgents((prev) =>
        prev.map((a) => (a.key === key ? { ...a, ...updates } : a))
      );
    },
    []
  );

  const handleSubmit = useCallback(
    async (incident: string) => {
      // Reset state
      setIsLoading(true);
      setIsComplete(false);
      setTraceId("");
      setAgents(
        INITIAL_AGENTS.map((a) => ({ ...a, status: "idle" as AgentStatus, output: "" }))
      );

      // Mark all parallel agents as running immediately
      setAgents((prev) =>
        prev.map((a) =>
          a.key !== "remediation" ? { ...a, status: "running" as AgentStatus } : a
        )
      );

      try {
        const res = await fetch("/api/triage", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ incident }),
        });

        if (!res.ok || !res.body) {
          throw new Error(`HTTP ${res.status}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const event = JSON.parse(line.slice(6));

              if (event.agent && event.status === "complete") {
                const key = event.agent as AgentKey;
                updateAgent(key, { status: "complete", output: event.output });
                // Kick off remediation running indicator
                if (key === "incident_history") {
                  updateAgent("remediation", { status: "running" });
                }
              }

              if (event.status === "done") {
                setTraceId(event.trace_id ?? "");
                setIsComplete(true);
              }

              if (event.status === "error") {
                setAgents((prev) =>
                  prev.map((a) =>
                    a.status === "running"
                      ? { ...a, status: "error", output: event.message }
                      : a
                  )
                );
              }
            } catch {
              // Non-JSON SSE line — ignore
            }
          }
        }
      } catch (err) {
        console.error("Triage error:", err);
        setAgents((prev) =>
          prev.map((a) =>
            a.status === "running"
              ? { ...a, status: "error", output: String(err) }
              : a
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [updateAgent]
  );

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border px-6 py-4 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-primary/20 border border-primary/30 flex items-center justify-center">
          <Activity className="w-4 h-4 text-primary" />
        </div>
        <div>
          <h1 className="font-bold text-foreground text-lg leading-none">
            Incident Response Copilot
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            AI-powered triage · LangGraph · BigQuery · Pinecone
          </p>
        </div>
        {isComplete && traceId && (
          <div className="ml-auto">
            <span className="text-xs text-muted-foreground font-mono bg-secondary px-2 py-1 rounded border border-border">
              {traceId.slice(0, 8)}…
            </span>
          </div>
        )}
      </header>

      {/* Three-panel layout */}
      <div className="flex flex-1 divide-x divide-border overflow-hidden">
        {/* Left: Incident Input */}
        <div className="w-80 flex-shrink-0 p-5 flex flex-col overflow-y-auto">
          <IncidentInput onSubmit={handleSubmit} isLoading={isLoading} />
        </div>

        {/* Center: Agent Pipeline */}
        <div className="flex-1 p-5 overflow-y-auto">
          <ChatWindow agents={agents} />
        </div>

        {/* Right: Triage Report */}
        <div className="w-96 flex-shrink-0 p-5 overflow-y-auto">
          <TriageReport
            remediation={remediationOutput}
            traceId={traceId}
            isComplete={isComplete}
          />
        </div>
      </div>
    </div>
  );
}
