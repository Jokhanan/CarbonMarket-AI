import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ShieldCheck, RefreshCw, ChevronDown, ChevronUp, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import type { AuditResult } from "@/lib/api";

const SEV_COLORS: Record<string, string> = {
  critical: "text-red-500 bg-red-500/10 border-red-500/20",
  high: "text-orange-400 bg-orange-400/10 border-orange-400/20",
  medium: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20",
  low: "text-blue-400 bg-blue-400/10 border-blue-400/20",
};

const RISK_COLORS: Record<string, string> = {
  LOW: "text-green-400",
  MEDIUM: "text-yellow-400",
  HIGH: "text-orange-400",
  CRITICAL: "text-red-500",
};

export default function AuditTab({ projectId }: { projectId: number }) {
  const { toast } = useToast();
  const [result, setResult] = useState<AuditResult | null>(null);
  const [running, setRunning] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [activeView, setActiveView] = useState<"run" | "history">("run");

  const { data: history, isLoading: loadingHistory } = useQuery<AuditResult[]>({
    queryKey: ["/api/projects", projectId, "audit-history"],
    queryFn: async () => {
      const r = await fetch(`/api/projects/${projectId}/audit-simulation/history`);
      if (!r.ok) throw new Error("Failed");
      return r.json();
    },
    enabled: activeView === "history",
  });

  async function runAudit() {
    setRunning(true);
    try {
      const r = await fetch(`/api/projects/${projectId}/audit-simulation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setResult(data);
    } catch (e) {
      toast({ title: "Audit failed", description: String(e), variant: "destructive" });
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-amber-500/10 flex items-center justify-center">
          <ShieldCheck className="w-4 h-4 text-amber-400" />
        </div>
        <h2 className="text-base font-semibold">Audit Simulation</h2>
        <div className="ml-auto flex gap-1">
          {(["run", "history"] as const).map((t) => (
            <button
              key={t}
              data-testid={`audit-tab-${t}`}
              onClick={() => setActiveView(t)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors capitalize ${
                activeView === t ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {activeView === "run" && (
        <div className="space-y-4">
          <div className="p-4 bg-card border border-border/50 rounded-lg">
            <p className="text-sm text-muted-foreground mb-3">
              Simulate a VVB audit. The AI will check parameter validity, evidence coverage, section consistency, and compliance — then produce findings with severity ratings.
            </p>
            <Button
              data-testid="button-run-audit"
              onClick={runAudit}
              disabled={running}
              className="gap-2 w-full"
            >
              {running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
              {running ? "Running audit simulation..." : "Run Full Audit Simulation"}
            </Button>
          </div>

          {result && (
            <div className="space-y-4">
              <div className="grid grid-cols-5 gap-3">
                <div className="col-span-2 bg-card border border-border/50 rounded-lg p-4 text-center">
                  <div className={`text-3xl font-bold ${RISK_COLORS[result.risk_level] ?? "text-muted-foreground"}`}>
                    {result.risk_level}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">Risk Level</div>
                </div>
                <div className="bg-card border border-border/50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold">{result.overall_score}/100</div>
                  <div className="text-xs text-muted-foreground mt-1">Score</div>
                </div>
                {(["critical", "high", "medium", "low"] as const).slice(0, 2).map((sev) => (
                  <div key={sev} className="bg-card border border-border/50 rounded-lg p-4 text-center">
                    <div className={`text-2xl font-bold ${SEV_COLORS[sev].split(" ")[0]}`}>
                      {result.counts[sev] ?? 0}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1 capitalize">{sev}</div>
                  </div>
                ))}
              </div>

              {result.summary && (
                <p className="text-sm text-muted-foreground px-1">{result.summary}</p>
              )}

              {result.findings?.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Findings ({result.findings.length})</p>
                  {result.findings.map((f, i) => {
                    const isOpen = expanded === i;
                    return (
                      <div key={i} className={`border rounded-lg overflow-hidden ${SEV_COLORS[f.severity] ?? "border-border"}`}>
                        <button
                          data-testid={`finding-${i}`}
                          className="w-full flex items-center justify-between px-4 py-3 bg-card/80 hover:bg-card text-left"
                          onClick={() => setExpanded(isOpen ? null : i)}
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <span className={`shrink-0 text-xs font-bold px-1.5 py-0.5 rounded border ${SEV_COLORS[f.severity]}`}>
                              {f.type?.toUpperCase() ?? "OBS"}
                            </span>
                            <span className="text-sm font-medium truncate">{f.title}</span>
                          </div>
                          <div className="flex items-center gap-2 shrink-0 ml-2">
                            <span className={`text-xs font-medium capitalize ${SEV_COLORS[f.severity].split(" ")[0]}`}>{f.severity}</span>
                            {isOpen ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
                          </div>
                        </button>
                        {isOpen && (
                          <div className="px-4 py-3 border-t border-border/30 bg-background text-sm text-muted-foreground">
                            {f.description}
                            {f.category && (
                              <p className="text-xs mt-2 text-muted-foreground/60">Category: {f.category}</p>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {result.evidence_gaps?.length > 0 && (
                <div className="p-4 bg-orange-500/5 border border-orange-500/15 rounded-lg">
                  <p className="text-xs font-semibold text-orange-400 uppercase tracking-wider mb-2">Evidence Gaps ({result.evidence_gaps.length})</p>
                  {result.evidence_gaps.map((g, i) => (
                    <p key={i} className="text-xs text-muted-foreground">• <strong>{g.param_name}</strong> — no supporting evidence</p>
                  ))}
                </div>
              )}

              {result.recommendations?.length > 0 && (
                <div className="p-4 bg-primary/5 border border-primary/15 rounded-lg">
                  <p className="text-xs font-semibold text-primary uppercase tracking-wider mb-2">Recommendations</p>
                  {result.recommendations.map((r, i) => <p key={i} className="text-xs text-muted-foreground">• {r}</p>)}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeView === "history" && (
        <div className="space-y-3">
          {loadingHistory ? (
            <div className="space-y-2">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}</div>
          ) : !(history as any)?.length ? (
            <div className="py-12 text-center text-sm text-muted-foreground border border-dashed border-border rounded-lg">
              No audit simulations run yet.
            </div>
          ) : (
            (history as any[]).map((sim: any, i: number) => (
              <div key={sim.id ?? i} className="p-4 bg-card border border-border/50 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className={`font-bold ${RISK_COLORS[sim.risk_level] ?? ""}`}>{sim.risk_level ?? "—"}</span>
                  <span className="text-sm font-medium">{sim.overall_score}/100</span>
                  <span className="text-xs text-muted-foreground">
                    {sim.simulated_at ? new Date(sim.simulated_at).toLocaleDateString() : "—"}
                  </span>
                </div>
                {sim.summary && <p className="text-xs text-muted-foreground mt-2">{sim.summary}</p>}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
