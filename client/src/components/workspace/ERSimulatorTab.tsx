import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { TrendingUp, Play, Save, Star, RefreshCw } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import type { ERResult, ERScenario, Project } from "@/lib/api";

function fmt(n: number | undefined): string {
  if (n == null) return "—";
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n.toFixed(0);
}

export default function ERSimulatorTab({ project }: { project: Project }) {
  const { toast } = useToast();
  const qc = useQueryClient();
  const projectId = project.id;

  const [result, setResult] = useState<ERResult | null>(null);
  const [running, setRunning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [scenarioName, setScenarioName] = useState("");
  const [overrides, setOverrides] = useState<Record<string, number>>({});
  const [activeTab, setActiveTab] = useState<"simulator" | "scenarios">("simulator");

  const { data: scenarios, isLoading: loadingScenarios } = useQuery<ERScenario[]>({
    queryKey: ["/api/projects", projectId, "er-scenarios"],
    queryFn: async () => {
      const r = await fetch(`/api/projects/${projectId}/er-scenarios`);
      if (!r.ok) throw new Error("Failed");
      return r.json();
    },
  });

  async function runSimulation() {
    setRunning(true);
    try {
      const r = await fetch(`/api/projects/${projectId}/er-scenarios/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ overrides }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setResult(data);
    } catch (e) {
      toast({ title: "Simulation failed", description: String(e), variant: "destructive" });
    } finally {
      setRunning(false);
    }
  }

  async function saveScenario() {
    if (!result || !scenarioName.trim()) {
      toast({ title: "Enter a scenario name", variant: "destructive" });
      return;
    }
    setSaving(true);
    try {
      const r = await fetch(`/api/projects/${projectId}/er-scenarios`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_name: scenarioName, result }),
      });
      if (!r.ok) throw new Error(await r.text());
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "er-scenarios"] });
      toast({ title: "Scenario saved" });
      setScenarioName("");
    } catch (e) {
      toast({ title: "Save failed", description: String(e), variant: "destructive" });
    } finally {
      setSaving(false);
    }
  }

  async function selectScenario(scenarioId: number) {
    try {
      await fetch(`/api/projects/${projectId}/er-scenarios/${scenarioId}/select`, { method: "POST" });
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "er-scenarios"] });
      toast({ title: "Scenario selected for drafting" });
    } catch (e) {
      toast({ title: "Error", description: String(e), variant: "destructive" });
    }
  }

  const chartData = result
    ? (result.year_by_year ?? result.years ?? []).map((y) => ({
        year: y.calendar_year,
        baseline: Math.round(y.baseline_emissions),
        project: Math.round(y.project_emissions),
        net_er: Math.round(y.net_er),
      }))
    : [];

  const SUPPORTED = ["VM0050", "TPDDTEC", "ACM0002", "AMS-I.D.", "AMSID", "MECD", "GS-MECD"];
  const meth = (project.methodology ?? "").toUpperCase().replace("GS-", "");
  const isSupported = SUPPORTED.some((s) => meth.includes(s));

  if (!isSupported) {
    return (
      <div className="py-12 text-center text-sm text-muted-foreground border border-dashed border-border rounded-lg">
        ER simulation is not yet available for methodology: {project.methodology}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-green-500/10 flex items-center justify-center">
          <TrendingUp className="w-4 h-4 text-green-400" />
        </div>
        <h2 className="text-base font-semibold">ER Simulator</h2>
        <div className="ml-auto flex gap-1">
          {(["simulator", "scenarios"] as const).map((t) => (
            <button
              key={t}
              data-testid={`er-tab-${t}`}
              onClick={() => setActiveTab(t)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors capitalize ${
                activeTab === t
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {t}
              {t === "scenarios" && scenarios?.length ? (
                <span className="ml-1 bg-primary/20 text-primary rounded-full px-1.5 text-[10px]">{scenarios.length}</span>
              ) : null}
            </button>
          ))}
        </div>
      </div>

      {activeTab === "simulator" && (
        <div className="space-y-4">
          <div className="p-4 bg-card border border-border/50 rounded-lg space-y-3">
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Parameter Overrides (optional)</p>
            <div className="grid grid-cols-3 gap-3">
              {[
                { key: "num_devices", label: "Devices / Households", unit: "" },
                { key: "fNRB", label: "fNRB", unit: "" },
                { key: "leakage_pct", label: "Leakage %", unit: "%" },
              ].map(({ key, label }) => (
                <div key={key} className="space-y-1">
                  <Label className="text-xs text-muted-foreground">{label}</Label>
                  <Input
                    type="number"
                    step="any"
                    placeholder="Use project value"
                    value={overrides[key] ?? ""}
                    onChange={(e) => {
                      const v = e.target.value;
                      setOverrides((o) => {
                        const next = { ...o };
                        if (v === "") delete next[key]; else next[key] = parseFloat(v);
                        return next;
                      });
                    }}
                    className="bg-input border-border h-8 text-sm"
                  />
                </div>
              ))}
            </div>
            <Button
              data-testid="button-run-simulation"
              onClick={runSimulation}
              disabled={running}
              className="gap-2 w-full"
            >
              {running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              {running ? "Calculating..." : "Run Simulation"}
            </Button>
          </div>

          {result && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-card border border-border/50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-primary">{fmt(result.summary.total_er)}</div>
                  <div className="text-xs text-muted-foreground mt-1">Total ER (tCO₂e)</div>
                </div>
                <div className="bg-card border border-border/50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold">{fmt(result.summary.average_annual_er)}</div>
                  <div className="text-xs text-muted-foreground mt-1">Avg Annual ER</div>
                </div>
                <div className="bg-card border border-border/50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold">{result.summary.crediting_years}</div>
                  <div className="text-xs text-muted-foreground mt-1">Crediting Years</div>
                </div>
              </div>

              {chartData.length > 0 && (
                <div className="bg-card border border-border/50 rounded-lg p-4">
                  <p className="text-xs font-medium text-muted-foreground mb-3 uppercase tracking-wider">Year-by-Year ER (tCO₂e)</p>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="year" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                      <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                      <Tooltip
                        contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
                        formatter={(v: number) => [`${v.toLocaleString()} tCO₂e`]}
                      />
                      <Legend wrapperStyle={{ fontSize: 11 }} />
                      <Bar dataKey="baseline" name="Baseline" fill="hsl(var(--muted))" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="net_er" name="Net ER" fill="hsl(var(--primary))" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {(result.year_by_year ?? result.years ?? []).length > 0 && (
                <div className="border border-border rounded-lg overflow-hidden">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-card border-b border-border text-muted-foreground uppercase tracking-wider">
                        <th className="text-left px-4 py-2">Year</th>
                        <th className="text-right px-4 py-2">Baseline</th>
                        <th className="text-right px-4 py-2">Project</th>
                        <th className="text-right px-4 py-2">Gross ER</th>
                        <th className="text-right px-4 py-2">Net ER</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(result.year_by_year ?? result.years ?? []).map((y) => (
                        <tr key={y.year_number} className="border-b border-border/40 hover:bg-accent/10">
                          <td className="px-4 py-1.5 font-medium">{y.calendar_year}</td>
                          <td className="px-4 py-1.5 text-right text-muted-foreground">{y.baseline_emissions?.toLocaleString()}</td>
                          <td className="px-4 py-1.5 text-right text-muted-foreground">{y.project_emissions?.toLocaleString()}</td>
                          <td className="px-4 py-1.5 text-right">{(y.gross_er ?? (y.baseline_emissions - y.project_emissions))?.toLocaleString()}</td>
                          <td className="px-4 py-1.5 text-right font-medium text-primary">{y.net_er?.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {result.warnings && result.warnings.length > 0 && (
                <div className="px-3 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded text-xs text-yellow-400">
                  {result.warnings.map((w, i) => <div key={i}>• {w}</div>)}
                </div>
              )}

              <div className="flex items-center gap-2 pt-1">
                <Input
                  placeholder="Scenario name (e.g. Base Case, Conservative)"
                  value={scenarioName}
                  onChange={(e) => setScenarioName(e.target.value)}
                  className="bg-input border-border h-8 text-sm"
                  data-testid="input-scenario-name"
                />
                <Button
                  data-testid="button-save-scenario"
                  size="sm"
                  onClick={saveScenario}
                  disabled={saving || !scenarioName.trim()}
                  className="gap-1.5 shrink-0"
                >
                  <Save className="w-4 h-4" />
                  {saving ? "Saving..." : "Save"}
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "scenarios" && (
        <div className="space-y-3">
          {loadingScenarios ? (
            <div className="space-y-2">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}</div>
          ) : !scenarios?.length ? (
            <div className="py-12 text-center text-sm text-muted-foreground border border-dashed border-border rounded-lg">
              No saved scenarios yet. Run a simulation and save it.
            </div>
          ) : (
            scenarios.map((s) => (
              <div
                key={s.id}
                data-testid={`scenario-card-${s.id}`}
                className={`p-4 bg-card border rounded-lg flex items-center justify-between ${s.is_selected ? "border-primary/50" : "border-border/50"}`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{s.scenario_name}</span>
                    {s.is_selected && (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-primary/10 text-primary rounded text-xs font-medium">
                        <Star className="w-3 h-3" /> Selected
                      </span>
                    )}
                    {s.purpose && <span className="text-xs text-muted-foreground">{s.purpose}</span>}
                  </div>
                  {s.summary && (
                    <div className="text-xs text-muted-foreground mt-1">
                      Total: {fmt(s.summary.total_er)} tCO₂e · Avg: {fmt(s.summary.average_annual_er)}/yr · {s.summary.crediting_years} yrs
                    </div>
                  )}
                </div>
                {!s.is_selected && (
                  <Button
                    data-testid={`button-select-scenario-${s.id}`}
                    size="sm"
                    variant="outline"
                    onClick={() => selectScenario(s.id)}
                    className="text-xs h-7"
                  >
                    Use for Drafting
                  </Button>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
