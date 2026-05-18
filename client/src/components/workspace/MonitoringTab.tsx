import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Activity, Plus, RefreshCw, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import type { MonitoringPeriod } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  planned: "text-muted-foreground",
  in_progress: "text-yellow-400",
  complete: "text-green-400",
  submitted: "text-blue-400",
};

export default function MonitoringTab({ projectId }: { projectId: number }) {
  const { toast } = useToast();
  const qc = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [newPeriod, setNewPeriod] = useState({ period_start: "", period_end: "", notes: "" });
  const [adding, setAdding] = useState(false);

  const { data: periods, isLoading } = useQuery<MonitoringPeriod[]>({
    queryKey: ["/api/projects", projectId, "monitoring-periods"],
    queryFn: async () => {
      const r = await fetch(`/api/projects/${projectId}/monitoring-periods`);
      if (!r.ok) throw new Error("Failed");
      return r.json();
    },
  });

  const { data: tasks, isLoading: loadingTasks } = useQuery<any[]>({
    queryKey: ["/api/projects", projectId, "monitoring-tasks"],
    queryFn: async () => {
      const r = await fetch(`/api/projects/${projectId}/monitoring-tasks`);
      if (!r.ok) throw new Error("Failed");
      return r.json();
    },
  });

  async function addPeriod() {
    if (!newPeriod.period_start || !newPeriod.period_end) {
      toast({ title: "Start and end date required", variant: "destructive" });
      return;
    }
    setAdding(true);
    try {
      const r = await fetch(`/api/projects/${projectId}/monitoring-periods`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...newPeriod, period_number: (periods?.length ?? 0) + 1 }),
      });
      if (!r.ok) throw new Error(await r.text());
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "monitoring-periods"] });
      setNewPeriod({ period_start: "", period_end: "", notes: "" });
      setShowAddForm(false);
      toast({ title: "Monitoring period added" });
    } catch (e) {
      toast({ title: "Failed", description: String(e), variant: "destructive" });
    } finally {
      setAdding(false);
    }
  }

  async function generateMR(periodId: number) {
    toast({ title: "Generating MR...", description: "A new Monitoring Report project will be created." });
    try {
      const r = await fetch(`/api/projects/${projectId}/monitoring-periods/${periodId}/generate-mr`, {
        method: "POST",
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      toast({ title: "MR project created", description: `Project ID: ${data.mr_project_id}` });
    } catch (e) {
      toast({ title: "MR generation failed", description: String(e), variant: "destructive" });
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-teal-500/10 flex items-center justify-center">
          <Activity className="w-4 h-4 text-teal-400" />
        </div>
        <h2 className="text-base font-semibold">Monitoring</h2>
        <Button
          data-testid="button-add-period"
          size="sm"
          variant="outline"
          onClick={() => setShowAddForm(!showAddForm)}
          className="ml-auto gap-1.5 h-7 text-xs"
        >
          <Plus className="w-3.5 h-3.5" />
          Add Period
        </Button>
      </div>

      {showAddForm && (
        <div className="p-4 bg-card border border-primary/20 rounded-lg space-y-3">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">New Monitoring Period</p>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Start Date</Label>
              <Input
                type="date"
                value={newPeriod.period_start}
                onChange={(e) => setNewPeriod((p) => ({ ...p, period_start: e.target.value }))}
                className="bg-input border-border h-8 text-sm"
                data-testid="input-period-start"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">End Date</Label>
              <Input
                type="date"
                value={newPeriod.period_end}
                onChange={(e) => setNewPeriod((p) => ({ ...p, period_end: e.target.value }))}
                className="bg-input border-border h-8 text-sm"
                data-testid="input-period-end"
              />
            </div>
          </div>
          <Input
            placeholder="Notes (optional)"
            value={newPeriod.notes}
            onChange={(e) => setNewPeriod((p) => ({ ...p, notes: e.target.value }))}
            className="bg-input border-border h-8 text-sm"
          />
          <div className="flex gap-2">
            <Button
              data-testid="button-save-period"
              size="sm"
              onClick={addPeriod}
              disabled={adding}
              className="gap-1.5"
            >
              {adding ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : null}
              {adding ? "Saving..." : "Save Period"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setShowAddForm(false)}>Cancel</Button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">{[...Array(2)].map((_, i) => <Skeleton key={i} className="h-20 w-full" />)}</div>
      ) : !periods?.length ? (
        <div className="py-12 text-center text-sm text-muted-foreground border border-dashed border-border rounded-lg">
          No monitoring periods defined. Add the first one above.
        </div>
      ) : (
        <div className="space-y-3">
          {periods.map((p) => (
            <div key={p.id} data-testid={`period-card-${p.id}`} className="p-4 bg-card border border-border/50 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <div>
                    <div className="text-sm font-medium">Period {p.period_number}</div>
                    <div className="text-xs text-muted-foreground mt-0.5">
                      {new Date(p.period_start).toLocaleDateString()} – {new Date(p.period_end).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-medium ${STATUS_COLORS[p.status] ?? "text-muted-foreground"}`}>
                    {p.status}
                  </span>
                  <Button
                    data-testid={`button-gen-mr-${p.id}`}
                    size="sm"
                    variant="outline"
                    onClick={() => generateMR(p.id)}
                    className="text-xs h-7 gap-1.5"
                  >
                    Generate MR
                  </Button>
                </div>
              </div>
              {p.notes && <p className="text-xs text-muted-foreground mt-2">{p.notes}</p>}
            </div>
          ))}
        </div>
      )}

      {tasks && tasks.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Monitoring Tasks</p>
          {tasks.map((t: any, i: number) => (
            <div key={t.id ?? i} className="flex items-center justify-between px-3 py-2 bg-card border border-border/40 rounded text-sm">
              <span>{t.task_name ?? t.title ?? t.description}</span>
              <span className="text-xs text-muted-foreground">{t.frequency ?? t.status ?? ""}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
