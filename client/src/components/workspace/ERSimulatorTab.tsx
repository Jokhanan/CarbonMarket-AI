import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { TrendingUp, Play, Save, Star, RefreshCw, RotateCcw, Trash2, ChevronDown, ChevronUp } from "lucide-react";
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
  return n >= 1_000_000
    ? `${(n / 1_000_000).toFixed(2)}M`
    : n >= 1000
    ? `${(n / 1000).toFixed(1)}k`
    : n.toFixed(0);
}

// All methodology codes that the backend er_simulator supports
const SUPPORTED_CODES = [
  "RECH", "GS-RECH", "GS_RECH",
  "VM0050", "TPDDTEC", "ACM0002", "AMS-I.D.", "AMSID",
  "MECD", "GS-MECD",
];

function isMethodologySupported(methodology: string | null | undefined): boolean {
  if (!methodology) return false;
  const upper = methodology.toUpperCase().replace(/[\s_]/g, "-");
  return SUPPORTED_CODES.some((code) => upper.includes(code.toUpperCase()));
}

// Override fields vary by methodology
const OVERRIDE_FIELDS: Record<string, { key: string; label: string; step: number; unit: string }[]> = {
  default: [
    { key: "num_devices", label: "Devices / Households", step: 1, unit: "" },
    { key: "fNRB", label: "fNRB", step: 0.01, unit: "" },
    { key: "leakage_pct", label: "Leakage", step: 0.001, unit: "%" },
  ],
  RECH: [
    { key: "num_devices", label: "Devices", step: 1, unit: "" },
    { key: "fNRB", label: "fNRB", step: 0.01, unit: "" },
    { key: "leakage_pct", label: "Leakage", step: 0.001, unit: "%" },
    { key: "baseline_fuel_consumption", label: "Baseline Fuel Consumption", step: 0.01, unit: "t/device/yr" },
  ],
  VM0050: [
    { key: "num_devices", label: "Households", step: 1, unit: "" },
    { key: "fNRB", label: "fNRB", step: 0.01, unit: "" },
    { key: "leakage_pct", label: "Leakage", step: 0.001, unit: "%" },
    { key: "usage_rate", label: "Usage Rate", step: 0.01, unit: "" },
  ],
  TPDDTEC: [
    { key: "num_devices", label: "Devices", step: 1, unit: "" },
    { key: "SFC_baseline", label: "Baseline Fuel Consumption", step: 0.01, unit: "kg/device/day" },
    { key: "SFC_project", label: "Project Fuel Consumption", step: 0.01, unit: "kg/device/day" },
    { key: "fNRB", label: "fNRB", step: 0.01, unit: "" },
    { key: "leakage_pct", label: "Leakage", step: 0.001, unit: "%" },
  ],
};

function getOverrideFields(methodology: string | null | undefined) {
  if (!methodology) return OVERRIDE_FIELDS.default;
  const upper = methodology.toUpperCase();
  if (upper.includes("RECH")) return OVERRIDE_FIELDS.RECH;
  if (upper.includes("VM0050")) return OVERRIDE_FIELDS.VM0050;
  if (upper.includes("TPDDTEC")) return OVERRIDE_FIELDS.TPDDTEC;
  return OVERRIDE_FIELDS.default;
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
  const [showOverrides, setShowOverrides] = useState(true);

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
    setResult(null);
    try {
      const r = await fetch(`/api/projects/${projectId}/er-scenarios/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ overrides }),
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e) {
      toast({ title: "Simulation failed", description: String(e), variant: "destructive" });
    } finally {
      setRunning(false);
    }
  }

  async function saveScenario() {
    if (!result || !scenarioName.trim()) {
      toast({ title: "Enter a scenario name first", variant: "destructive" });
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
      toast({ title: `Scenario "${scenarioName}" saved` });
      setScenarioName("");
      // Don't clear result or overrides — user may want to tweak and run again
    } catch (e) {
      toast({ title: "Save failed", description: String(e), variant: "destructive" });
    } finally {
      setSaving(false);
    }
  }

  async function deleteScenario(scenarioId: number) {
    try {
      await fetch(`/api/projects/${projectId}/er-scenarios/${scenarioId}`, { method: "DELETE" });
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "er-scenarios"] });
      toast({ title: "Scenario deleted" });
    } catch (e) {
      toast({ title: "Error", description: String(e), variant: "destructive" });
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

  function resetScenario() {
    setResult(null);
    setOverrides({});
    setScenarioName("");
  }

  const chartData = result
    ? (result.year_by_year ?? result.years ?? []).map((y) => ({
        year: y.calendar_year,
        baseline: Math.round(y.baseline_emissions),
        net_er: Math.round(y.net_er),
      }))
    : [];

  const overrideFields = getOverrideFields(project.methodology);
  const activeOverrideCount = Object.keys(overrides).length;

  if (!isMethodologySupported(project.methodology)) {
    return (
      <div className="py-12 text-center text-sm text-muted-foreground border border-dashed border-border rounded-lg">
        ER simulation is not yet available for methodology: <strong>{project.methodology}</strong>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-green-500/10 flex items-center justify-center">
          <TrendingUp className="w-4 h-4 text-green-400" />
        </div>
        <h2 className="text-base font-semibold">ER Simulator</h2>
        <span className="text-xs text-muted-foreground px-2 py-0.5 bg-muted rounded">
          {project.methodology}
        </span>
        <div className="ml-auto flex gap-1">
          {(["simulator", "scenarios"] as const).map((t) => (
            <button
              key={t}
              data-testid={`er-tab-${t}`}
              onClick={() => setActiveTab(t)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors capitalize ${
                activeTab === t ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground"
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

      {/* ── SIMULATOR TAB ── */}
      {activeTab === "simulator" && (
        <div className="space-y-4">

          {/* Workflow guidance */}
          <div className="px-4 py-3 bg-card border border-border/50 rounded-lg text-xs text-muted-foreground leading-relaxed">
            <strong className="text-foreground">How to compare multiple scenarios:</strong> adjust the parameters below, run the simulation, name it, and save it. Then reset and run again with different values. Switch to the <strong className="text-foreground">Scenarios</strong> tab to compare all saved results side by side.
          </div>

          {/* Parameter overrides panel */}
          <div className="border border-border/50 rounded-lg overflow-hidden">
            <button
              className="w-full flex items-center justify-between px-4 py-3 bg-card text-left hover:bg-accent/10"
              onClick={() => setShowOverrides(!showOverrides)}
            >
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Parameter Overrides
                </span>
                {activeOverrideCount > 0 && (
                  <span className="bg-primary/20 text-primary text-[10px] font-bold px-1.5 rounded-full">
                    {activeOverrideCount} active
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {activeOverrideCount > 0 && (
                  <button
                    className="text-xs text-muted-foreground hover:text-foreground px-2 py-0.5 rounded hover:bg-accent"
                    onClick={(e) => { e.stopPropagation(); setOverrides({}); }}
                  >
                    Clear all
                  </button>
                )}
                {showOverrides ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
              </div>
            </button>

            {showOverrides && (
              <div className="px-4 py-3 border-t border-border/50 bg-background">
                <p className="text-xs text-muted-foreground mb-3">
                  Leave blank to use the project's saved parameter values. Fill in to test a different assumption.
                </p>
                <div className="grid grid-cols-2 gap-3">
                  {overrideFields.map(({ key, label, step, unit }) => (
                    <div key={key} className="space-y-1">
                      <Label className="text-xs text-muted-foreground">
                        {label}{unit ? <span className="ml-1 opacity-60">({unit})</span> : null}
                      </Label>
                      <div className="relative">
                        <Input
                          type="number"
                          step={step}
                          placeholder="Project value"
                          value={overrides[key] ?? ""}
                          onChange={(e) => {
                            const v = e.target.value;
                            setOverrides((o) => {
                              const next = { ...o };
                              if (v === "") delete next[key]; else next[key] = parseFloat(v);
                              return next;
                            });
                          }}
                          className={`bg-input border-border h-8 text-sm pr-7 ${overrides[key] != null ? "border-primary/50 bg-primary/5" : ""}`}
                          data-testid={`input-override-${key}`}
                        />
                        {overrides[key] != null && (
                          <button
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                            onClick={() => setOverrides((o) => { const n = { ...o }; delete n[key]; return n; })}
                          >
                            <RotateCcw className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Run / Reset buttons */}
          <div className="flex gap-2">
            <Button
              data-testid="button-run-simulation"
              onClick={runSimulation}
              disabled={running}
              className="gap-2 flex-1"
            >
              {running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              {running ? "Calculating..." : result ? "Re-run Simulation" : "Run Simulation"}
            </Button>
            {result && (
              <Button
                data-testid="button-reset-scenario"
                variant="outline"
                onClick={resetScenario}
                className="gap-1.5 text-muted-foreground"
              >
                <RotateCcw className="w-4 h-4" />
                New Scenario
              </Button>
            )}
          </div>

          {/* Results */}
          {result && (
            <div className="space-y-4">
              {/* Summary cards */}
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

              {/* Chart */}
              {chartData.length > 0 && (
                <div className="bg-card border border-border/50 rounded-lg p-4">
                  <p className="text-xs font-medium text-muted-foreground mb-3 uppercase tracking-wider">Year-by-Year ER (tCO₂e)</p>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="year" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                      <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
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

              {/* Year table */}
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

              {/* Save scenario */}
              <div className="p-3 bg-card border border-primary/20 rounded-lg space-y-2">
                <p className="text-xs text-muted-foreground">
                  Save this result as a named scenario, then click <strong className="text-foreground">New Scenario</strong> to test different assumptions.
                </p>
                <div className="flex items-center gap-2">
                  <Input
                    placeholder='e.g. "Base Case", "Conservative −20%", "Optimistic"'
                    value={scenarioName}
                    onChange={(e) => setScenarioName(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && saveScenario()}
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
                    {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-4 h-4" />}
                    {saving ? "Saving..." : "Save Scenario"}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── SCENARIOS TAB ── */}
      {activeTab === "scenarios" && (
        <div className="space-y-3">
          {loadingScenarios ? (
            <div className="space-y-2">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}</div>
          ) : !scenarios?.length ? (
            <div className="py-12 text-center text-sm text-muted-foreground border border-dashed border-border rounded-lg">
              No saved scenarios yet.<br />
              <span className="text-xs">Run a simulation in the Simulator tab and save it with a name.</span>
            </div>
          ) : (
            <>
              {/* Comparison table */}
              {scenarios.length > 1 && (
                <div className="border border-border rounded-lg overflow-hidden">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-card border-b border-border text-muted-foreground uppercase tracking-wider">
                        <th className="text-left px-4 py-2">Scenario</th>
                        <th className="text-right px-4 py-2">Total ER</th>
                        <th className="text-right px-4 py-2">Avg Annual</th>
                        <th className="text-right px-4 py-2">Years</th>
                        <th className="text-center px-4 py-2">Drafting</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scenarios.map((s) => {
                        const best = scenarios.reduce((a, b) =>
                          (a.summary?.total_er ?? 0) > (b.summary?.total_er ?? 0) ? a : b
                        );
                        const isBest = s.id === best.id;
                        return (
                          <tr key={s.id} className={`border-b border-border/40 ${s.is_selected ? "bg-primary/5" : "hover:bg-accent/10"}`}>
                            <td className="px-4 py-2">
                              <div className="flex items-center gap-2">
                                {s.is_selected && <Star className="w-3 h-3 text-primary shrink-0" />}
                                <span className="font-medium">{s.scenario_name}</span>
                                {isBest && <span className="text-[9px] bg-green-500/15 text-green-400 px-1.5 rounded font-bold">HIGHEST</span>}
                              </div>
                            </td>
                            <td className="px-4 py-2 text-right font-bold text-primary">{fmt(s.summary?.total_er)}</td>
                            <td className="px-4 py-2 text-right">{fmt(s.summary?.average_annual_er)}</td>
                            <td className="px-4 py-2 text-right">{s.summary?.crediting_years ?? "—"}</td>
                            <td className="px-4 py-2 text-center">
                              {s.is_selected
                                ? <span className="text-primary text-xs font-medium">Selected</span>
                                : <button
                                    data-testid={`button-select-scenario-${s.id}`}
                                    onClick={() => selectScenario(s.id)}
                                    className="text-xs text-muted-foreground hover:text-foreground underline"
                                  >
                                    Use
                                  </button>
                              }
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Scenario cards */}
              {scenarios.map((s) => (
                <div
                  key={s.id}
                  data-testid={`scenario-card-${s.id}`}
                  className={`p-4 bg-card border rounded-lg ${s.is_selected ? "border-primary/40" : "border-border/50"}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-sm">{s.scenario_name}</span>
                        {s.is_selected && (
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-primary/10 text-primary rounded text-xs font-medium">
                            <Star className="w-3 h-3" /> Selected for Drafting
                          </span>
                        )}
                        {s.purpose && <span className="text-xs text-muted-foreground">{s.purpose}</span>}
                      </div>
                      {s.summary && (
                        <div className="text-xs text-muted-foreground mt-1.5 flex gap-4">
                          <span>Total: <strong className="text-foreground">{fmt(s.summary.total_er)} tCO₂e</strong></span>
                          <span>Avg: <strong className="text-foreground">{fmt(s.summary.average_annual_er)}/yr</strong></span>
                          <span>{s.summary.crediting_years} yrs</span>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {!s.is_selected && (
                        <Button
                          data-testid={`button-select-scenario-${s.id}`}
                          size="sm"
                          variant="outline"
                          onClick={() => selectScenario(s.id)}
                          className="text-xs h-7 gap-1"
                        >
                          <Star className="w-3 h-3" />
                          Use for Drafting
                        </Button>
                      )}
                      <Button
                        data-testid={`button-delete-scenario-${s.id}`}
                        size="sm"
                        variant="ghost"
                        onClick={() => deleteScenario(s.id)}
                        className="h-7 w-7 p-0 text-muted-foreground hover:text-red-400"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}
