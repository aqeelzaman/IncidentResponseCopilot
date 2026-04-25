"use client";

import { ShieldAlert, Zap, Clock, TrendingUp } from "lucide-react";

interface TriageReportProps {
  remediation: string;
  traceId: string;
  isComplete: boolean;
}

interface ParsedReport {
  rootCause: string;
  immediateActions: string[];
  followupActions: string[];
  confidence: number | null;
  reasoning: string;
}

function parseRemediation(text: string): ParsedReport {
  const lines = text.split("\n");
  let rootCause = "";
  let confidence: number | null = null;
  let reasoning = "";
  const immediateActions: string[] = [];
  const followupActions: string[] = [];

  let section = "";
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    if (trimmed.startsWith("ROOT CAUSE:")) {
      rootCause = trimmed.replace("ROOT CAUSE:", "").trim();
      section = "root";
    } else if (trimmed.startsWith("CONFIDENCE:")) {
      const val = parseFloat(trimmed.replace("CONFIDENCE:", "").trim());
      if (!isNaN(val)) confidence = val;
    } else if (trimmed.startsWith("IMMEDIATE ACTIONS:")) {
      section = "immediate";
    } else if (trimmed.startsWith("FOLLOW-UP ACTIONS:")) {
      section = "followup";
    } else if (trimmed.startsWith("REASONING:")) {
      reasoning = trimmed.replace("REASONING:", "").trim();
      section = "reasoning";
    } else if (section === "immediate" && /^\d+\./.test(trimmed)) {
      immediateActions.push(trimmed.replace(/^\d+\.\s*/, ""));
    } else if (section === "followup" && trimmed.startsWith("-")) {
      followupActions.push(trimmed.replace(/^-\s*/, ""));
    } else if (section === "reasoning" && reasoning) {
      reasoning += " " + trimmed;
    }
  }

  return { rootCause, immediateActions, followupActions, confidence, reasoning };
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80 ? "bg-emerald-500" : pct >= 60 ? "bg-yellow-500" : "bg-orange-500";
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 bg-secondary rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span
        className={`text-sm font-bold tabular-nums ${
          pct >= 80
            ? "text-emerald-400"
            : pct >= 60
            ? "text-yellow-400"
            : "text-orange-400"
        }`}
      >
        {pct}%
      </span>
    </div>
  );
}

export default function TriageReport({ remediation, traceId, isComplete }: TriageReportProps) {
  if (!isComplete || !remediation) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
        <div className="w-16 h-16 rounded-full bg-secondary border border-border flex items-center justify-center">
          <ShieldAlert className="w-7 h-7 text-muted-foreground" />
        </div>
        <div>
          <p className="text-muted-foreground text-sm">Triage report will appear here</p>
          <p className="text-muted-foreground/60 text-xs mt-1">
            Waiting for all agents to complete…
          </p>
        </div>
      </div>
    );
  }

  const report = parseRemediation(remediation);

  return (
    <div className="flex flex-col gap-4 h-full overflow-y-auto pr-1">
      <div className="flex items-center gap-2 pb-2 border-b border-border">
        <ShieldAlert className="w-5 h-5 text-primary" />
        <h2 className="font-semibold text-foreground">Triage Report</h2>
      </div>

      {/* Root Cause */}
      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
        <div className="flex items-center gap-2 mb-2">
          <ShieldAlert className="w-4 h-4 text-destructive" />
          <span className="text-xs font-semibold text-destructive uppercase tracking-wider">Root Cause</span>
        </div>
        <p className="text-sm text-foreground">{report.rootCause || remediation.slice(0, 200)}</p>
      </div>

      {/* Confidence */}
      {report.confidence !== null && (
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-primary" />
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Confidence</span>
          </div>
          <ConfidenceBar value={report.confidence} />
        </div>
      )}

      {/* Immediate Actions */}
      {report.immediateActions.length > 0 && (
        <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-4 h-4 text-primary" />
            <span className="text-xs font-semibold text-primary uppercase tracking-wider">Immediate Actions</span>
          </div>
          <ol className="space-y-2">
            {report.immediateActions.map((action, i) => (
              <li key={i} className="flex gap-2.5 text-sm text-foreground">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary/20 text-primary text-xs flex items-center justify-center font-bold">
                  {i + 1}
                </span>
                <span>{action}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Follow-up Actions */}
      {report.followupActions.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Clock className="w-4 h-4 text-muted-foreground" />
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Follow-up Actions</span>
          </div>
          <ul className="space-y-2">
            {report.followupActions.map((action, i) => (
              <li key={i} className="flex gap-2 text-sm text-foreground/80">
                <span className="flex-shrink-0 text-muted-foreground mt-0.5">•</span>
                <span>{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Reasoning */}
      {report.reasoning && (
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">{report.reasoning}</p>
        </div>
      )}

      {/* Trace ID */}
      {traceId && (
        <div className="mt-auto pt-2 border-t border-border">
          <p className="text-xs text-muted-foreground/60 font-mono">
            trace_id: {traceId}
          </p>
        </div>
      )}
    </div>
  );
}
