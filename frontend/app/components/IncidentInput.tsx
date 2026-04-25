"use client";

import { useState } from "react";
import { AlertCircle, Zap } from "lucide-react";

interface IncidentInputProps {
  onSubmit: (incident: string) => void;
  isLoading: boolean;
}

const DEMO_INCIDENT =
  "checkout-service is returning 503s, orders are failing, started about 90 minutes ago";

export default function IncidentInput({ onSubmit, isLoading }: IncidentInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = () => {
    const text = value.trim();
    if (!text || isLoading) return;
    onSubmit(text);
  };

  const handleDemo = () => {
    setValue(DEMO_INCIDENT);
  };

  return (
    <div className="flex flex-col h-full gap-4">
      <div className="flex items-center gap-2 pb-2 border-b border-border">
        <AlertCircle className="w-5 h-5 text-destructive" />
        <h2 className="font-semibold text-foreground">Incident Description</h2>
      </div>

      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Describe the production incident…&#10;&#10;e.g. checkout-service is returning 503s, orders are failing, started about 90 minutes ago"
        className="
          flex-1 w-full rounded-lg bg-secondary border border-border
          text-foreground placeholder:text-muted-foreground
          p-4 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring
          font-mono leading-relaxed
        "
        disabled={isLoading}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit();
        }}
      />

      <div className="flex flex-col gap-2">
        <button
          onClick={handleSubmit}
          disabled={!value.trim() || isLoading}
          className="
            w-full flex items-center justify-center gap-2 px-4 py-3
            bg-primary text-primary-foreground font-semibold rounded-lg
            hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed
            transition-colors text-sm
          "
        >
          {isLoading ? (
            <>
              <span className="inline-block w-4 h-4 border-2 border-primary-foreground/40 border-t-primary-foreground rounded-full animate-spin" />
              Triaging incident…
            </>
          ) : (
            <>
              <Zap className="w-4 h-4" />
              Triage Incident
            </>
          )}
        </button>

        <button
          onClick={handleDemo}
          disabled={isLoading}
          className="
            w-full px-4 py-2 text-xs text-muted-foreground border border-border
            rounded-lg hover:bg-secondary transition-colors disabled:opacity-40
          "
        >
          Load demo scenario
        </button>
      </div>

      <p className="text-xs text-muted-foreground">
        Press <kbd className="px-1 py-0.5 bg-secondary border border-border rounded text-xs">⌘↵</kbd> to submit
      </p>
    </div>
  );
}
