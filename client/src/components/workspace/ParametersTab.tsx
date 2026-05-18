import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, CheckCircle, AlertCircle, Sliders, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import type { Parameter, ParameterSummary } from "@/lib/api";

const SOURCE_COLORS: Record<string, string> = {
  measured: "text-green-400 bg-green-400/10",
  confirmed: "text-blue-400 bg-blue-400/10",
  default: "text-yellow-400 bg-yellow-400/10",
  user_override: "text-primary bg-primary/10",
  extracted: "text-purple-400 bg-purple-400/10",
};

function ParamRow({
  param,
  projectId,
  onUpdated,
}: {
  param: Parameter;
  projectId: number;
  onUpdated: () => void;
}) {
  const { toast } = useToast();
  const [editing, setEditing] = useState(false);
  const [val, setVal] = useState(String(param.value ?? ""));

  async function save() {
    try {
      const r = await fetch(`/api/projects/${projectId}/parameters/${param.param_key}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value: isNaN(Number(val)) ? val : Number(val) }),
      });
      if (!r.ok) throw new Error(await r.text());
      setEditing(false);
      onUpdated();
    } catch (e) {
      toast({ title: "Save failed", description: String(e), variant: "destructive" });
    }
  }

  async function confirm() {
    try {
      await fetch(`/api/projects/${projectId}/parameters/${param.param_key}/confirm`, {
        method: "POST",
      });
      onUpdated();
    } catch (e) {
      toast({ title: "Confirm failed", description: String(e), variant: "destructive" });
    }
  }

  const src = param.source_type ?? "default";
  const srcColor = SOURCE_COLORS[src] ?? "text-muted-foreground bg-muted";

  return (
    <tr className="border-b border-border/40 hover:bg-accent/10 group">
      <td className="px-4 py-2.5">
        <div>
          <span className="font-mono text-xs font-medium">{param.param_key}</span>
          {param.param_name && param.param_name !== param.param_key && (
            <div className="text-xs text-muted-foreground mt-0.5 truncate max-w-[200px]">{param.param_name}</div>
          )}
        </div>
      </td>
      <td className="px-4 py-2.5">
        {editing ? (
          <div className="flex items-center gap-2">
            <Input
              value={val}
              onChange={(e) => setVal(e.target.value)}
              className="h-7 text-xs bg-input border-border w-32"
              autoFocus
              onKeyDown={(e) => { if (e.key === "Enter") save(); if (e.key === "Escape") setEditing(false); }}
            />
            <Button size="sm" onClick={save} className="h-7 px-2 text-xs">Save</Button>
            <Button size="sm" variant="ghost" onClick={() => setEditing(false)} className="h-7 px-2 text-xs">Cancel</Button>
          </div>
        ) : (
          <button
            data-testid={`param-value-${param.param_key}`}
            onClick={() => { setVal(String(param.value ?? "")); setEditing(true); }}
            className="text-sm font-medium hover:text-primary transition-colors text-left"
          >
            {param.value != null ? String(param.value) : <span className="text-muted-foreground italic">not set</span>}
          </button>
        )}
      </td>
      <td className="px-4 py-2.5 text-xs text-muted-foreground">{param.unit || "—"}</td>
      <td className="px-4 py-2.5">
        <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${srcColor}`}>
          {src}
        </span>
      </td>
      <td className="px-4 py-2.5">
        <div className="flex items-center gap-2">
          {param.confirmed ? (
            <span data-testid={`param-confirmed-${param.param_key}`} className="text-green-400">
              <CheckCircle className="w-4 h-4" />
            </span>
          ) : (
            <button
              data-testid={`button-confirm-param-${param.param_key}`}
              onClick={confirm}
              title="Confirm this value"
              className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-green-400"
            >
              <Check className="w-4 h-4" />
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}

export default function ParametersTab({ projectId }: { projectId: number }) {
  const { toast } = useToast();
  const qc = useQueryClient();
  const [initializing, setInitializing] = useState(false);
  const [validating, setValidating] = useState(false);
  const [groupFilter, setGroupFilter] = useState("all");

  const { data: params, isLoading, refetch } = useQuery<Parameter[]>({
    queryKey: ["/api/projects", projectId, "parameters"],
    queryFn: async () => {
      const r = await fetch(`/api/projects/${projectId}/parameters`);
      if (!r.ok) throw new Error("Failed");
      return r.json();
    },
  });

  const { data: summary } = useQuery<ParameterSummary>({
    queryKey: ["/api/projects", projectId, "parameters", "summary"],
    queryFn: async () => {
      const r = await fetch(`/api/projects/${projectId}/parameters/summary`);
      if (!r.ok) throw new Error("Failed");
      return r.json();
    },
  });

  async function initialize() {
    setInitializing(true);
    try {
      const r = await fetch(`/api/projects/${projectId}/parameters/initialize`, { method: "POST" });
      if (!r.ok) throw new Error(await r.text());
      await qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "parameters"] });
      toast({ title: "Parameters initialized" });
    } catch (e) {
      toast({ title: "Init failed", description: String(e), variant: "destructive" });
    } finally {
      setInitializing(false);
    }
  }

  async function validate() {
    setValidating(true);
    try {
      const r = await fetch(`/api/projects/${projectId}/parameters/validate`, { method: "POST" });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      const issues = data.issues ?? data.errors ?? [];
      if (issues.length === 0) {
        toast({ title: "All parameters valid" });
      } else {
        toast({ title: `${issues.length} validation issues`, description: issues.slice(0, 3).join("; "), variant: "destructive" });
      }
    } catch (e) {
      toast({ title: "Validation failed", description: String(e), variant: "destructive" });
    } finally {
      setValidating(false);
    }
  }

  const groups = params ? [...new Set(params.map((p) => p.group ?? p.section ?? "General"))] : [];
  const filtered = params
    ? groupFilter === "all"
      ? params
      : params.filter((p) => (p.group ?? p.section ?? "General") === groupFilter)
    : [];

  const pending = params?.filter((p) => p.value == null).length ?? 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-amber-500/10 flex items-center justify-center">
          <Sliders className="w-4 h-4 text-amber-400" />
        </div>
        <h2 className="text-base font-semibold">Parameters</h2>
        <div className="ml-auto flex items-center gap-2">
          <Button
            data-testid="button-init-params"
            size="sm"
            variant="outline"
            onClick={initialize}
            disabled={initializing}
            className="gap-1.5 h-7 text-xs"
          >
            {initializing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            Initialize
          </Button>
          <Button
            data-testid="button-validate-params"
            size="sm"
            variant="outline"
            onClick={validate}
            disabled={validating}
            className="gap-1.5 h-7 text-xs"
          >
            {validating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
            Validate
          </Button>
        </div>
      </div>

      {summary && (
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: "Total", value: summary.total, color: "text-foreground" },
            { label: "Confirmed", value: summary.confirmed, color: "text-green-400" },
            { label: "Pending", value: summary.pending ?? pending, color: "text-yellow-400" },
            { label: "Coverage", value: `${summary.coverage_pct ?? 0}%`, color: "text-primary" },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-card border border-border/50 rounded-lg px-4 py-3">
              <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">{label}</div>
              <div className={`text-xl font-bold ${color}`}>{value}</div>
            </div>
          ))}
        </div>
      )}

      {pending > 0 && (
        <div className="flex items-center gap-2 px-3 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-xs text-yellow-400">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {pending} parameter{pending > 1 ? "s" : ""} still need values. Click any value to edit.
        </div>
      )}

      {groups.length > 1 && (
        <div className="flex items-center gap-1.5 flex-wrap">
          {["all", ...groups].map((g) => (
            <button
              key={g}
              data-testid={`filter-group-${g}`}
              onClick={() => setGroupFilter(g)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                groupFilter === g
                  ? "bg-primary text-primary-foreground"
                  : "bg-card border border-border text-muted-foreground hover:text-foreground"
              }`}
            >
              {g}
            </button>
          ))}
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">{[...Array(8)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
      ) : !filtered.length ? (
        <div className="py-12 text-center text-sm text-muted-foreground border border-dashed border-border rounded-lg">
          No parameters yet. Click "Initialize" to load defaults for this methodology.
        </div>
      ) : (
        <div className="border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-card text-xs text-muted-foreground uppercase tracking-wider">
                <th className="text-left px-4 py-2.5">Parameter</th>
                <th className="text-left px-4 py-2.5">Value</th>
                <th className="text-left px-4 py-2.5">Unit</th>
                <th className="text-left px-4 py-2.5">Source</th>
                <th className="text-left px-4 py-2.5">Confirmed</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <ParamRow
                  key={p.param_key}
                  param={p}
                  projectId={projectId}
                  onUpdated={() => {
                    qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "parameters"] });
                    qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "parameters", "summary"] });
                  }}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
