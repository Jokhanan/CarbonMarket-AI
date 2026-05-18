import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Clock, CheckCircle, Circle, RefreshCw, ChevronRight, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import type { Lifecycle, LifecycleTask, Issuance } from "@/lib/api";

const STAGE_LABELS: Record<string, string> = {
  feasibility: "Feasibility",
  design: "Design",
  validation: "Validation",
  registration: "Registration",
  monitoring: "Monitoring",
  verification: "Verification",
  issuance: "Issuance",
};

const PRIORITY_COLORS: Record<string, string> = {
  critical: "text-red-400",
  high: "text-orange-400",
  medium: "text-yellow-400",
  low: "text-muted-foreground",
};

const STATUS_COLORS_STAGE: Record<string, string> = {
  completed: "bg-green-500 border-green-500 text-white",
  active: "bg-primary border-primary text-white",
  upcoming: "bg-muted border-border text-muted-foreground",
};

export default function LifecycleTab({ projectId }: { projectId: number }) {
  const { toast } = useToast();
  const qc = useQueryClient();
  const [activeView, setActiveView] = useState<"tasks" | "stages" | "issuance">("tasks");
  const [newTask, setNewTask] = useState({ title: "", stage: "feasibility", priority: "medium" });
  const [addingTask, setAddingTask] = useState(false);
  const [advancing, setAdvancing] = useState(false);

  const { data: lifecycle, isLoading: loadingLifecycle } = useQuery<Lifecycle>({
    queryKey: ["/api/projects", projectId, "lifecycle"],
    queryFn: async () => {
      const r = await fetch(`/api/projects/${projectId}/lifecycle`);
      if (!r.ok) throw new Error("Failed");
      return r.json();
    },
  });

  const { data: tasks, isLoading: loadingTasks } = useQuery<LifecycleTask[]>({
    queryKey: ["/api/projects", projectId, "lifecycle-tasks"],
    queryFn: async () => {
      const r = await fetch(`/api/projects/${projectId}/lifecycle`);
      if (!r.ok) throw new Error("Failed");
      const data = await r.json();
      return data.tasks ?? [];
    },
  });

  const { data: issuances, isLoading: loadingIssuances } = useQuery<Issuance[]>({
    queryKey: ["/api/projects", projectId, "issuances"],
    queryFn: async () => {
      const r = await fetch(`/api/projects/${projectId}/issuances`);
      if (!r.ok) throw new Error("Failed");
      return r.json();
    },
    enabled: activeView === "issuance",
  });

  async function initLifecycle() {
    try {
      const r = await fetch(`/api/projects/${projectId}/lifecycle/initialize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!r.ok) throw new Error(await r.text());
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "lifecycle"] });
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "lifecycle-tasks"] });
      toast({ title: "Lifecycle initialized" });
    } catch (e) {
      toast({ title: "Failed", description: String(e), variant: "destructive" });
    }
  }

  async function advanceStage() {
    setAdvancing(true);
    try {
      const r = await fetch(`/api/projects/${projectId}/lifecycle/advance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!r.ok) throw new Error(await r.text());
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "lifecycle"] });
      toast({ title: "Stage advanced" });
    } catch (e) {
      toast({ title: "Failed", description: String(e), variant: "destructive" });
    } finally {
      setAdvancing(false);
    }
  }

  async function toggleTask(task: LifecycleTask) {
    const newStatus = task.status === "completed" ? "pending" : "completed";
    try {
      await fetch(`/api/projects/${projectId}/lifecycle`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: task.id, status: newStatus }),
      });
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "lifecycle-tasks"] });
    } catch (e) {
      toast({ title: "Update failed", description: String(e), variant: "destructive" });
    }
  }

  async function addTask() {
    if (!newTask.title.trim()) return;
    setAddingTask(true);
    try {
      await fetch(`/api/projects/${projectId}/lifecycle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newTask),
      });
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "lifecycle-tasks"] });
      setNewTask({ title: "", stage: lifecycle?.current_stage ?? "feasibility", priority: "medium" });
      toast({ title: "Task added" });
    } catch (e) {
      toast({ title: "Failed", description: String(e), variant: "destructive" });
    } finally {
      setAddingTask(false);
    }
  }

  const hasLifecycle = lifecycle?.stages && lifecycle.stages.some((s) => s.status !== "upcoming");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
          <Clock className="w-4 h-4 text-blue-400" />
        </div>
        <h2 className="text-base font-semibold">Lifecycle</h2>
        <div className="ml-auto flex gap-1">
          {(["tasks", "stages", "issuance"] as const).map((t) => (
            <button
              key={t}
              data-testid={`lifecycle-tab-${t}`}
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

      {!hasLifecycle && (
        <div className="p-4 bg-card border border-border/50 rounded-lg text-center space-y-3">
          <p className="text-sm text-muted-foreground">Project lifecycle not initialized yet.</p>
          <Button data-testid="button-init-lifecycle" onClick={initLifecycle} className="gap-2">
            <Clock className="w-4 h-4" />
            Initialize Lifecycle
          </Button>
        </div>
      )}

      {hasLifecycle && lifecycle && (
        <div className="flex items-center gap-0 overflow-x-auto py-1">
          {lifecycle.stages.map((stage, i) => (
            <div key={stage.key} className="flex items-center">
              <div className="flex flex-col items-center gap-1 px-2">
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold ${STATUS_COLORS_STAGE[stage.status]}`}>
                  {stage.status === "completed" ? "✓" : i + 1}
                </div>
                <span className={`text-[10px] font-medium whitespace-nowrap ${stage.status === "active" ? "text-primary" : stage.status === "completed" ? "text-green-400" : "text-muted-foreground"}`}>
                  {STAGE_LABELS[stage.key] ?? stage.name}
                </span>
                {stage.tasks_total > 0 && (
                  <span className="text-[9px] text-muted-foreground">{stage.tasks_completed}/{stage.tasks_total}</span>
                )}
              </div>
              {i < lifecycle.stages.length - 1 && (
                <div className={`h-px w-8 shrink-0 ${stage.status === "completed" ? "bg-green-500" : "bg-border"}`} />
              )}
            </div>
          ))}
        </div>
      )}

      {activeView === "tasks" && (
        <div className="space-y-3">
          {loadingTasks ? (
            <div className="space-y-2">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
          ) : !tasks?.length ? (
            <div className="py-8 text-center text-sm text-muted-foreground border border-dashed border-border rounded-lg">
              No tasks. Initialize lifecycle or add tasks manually.
            </div>
          ) : (
            <div className="space-y-1">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  data-testid={`task-row-${task.id}`}
                  className="flex items-center gap-3 px-3 py-2.5 bg-card border border-border/40 rounded-lg hover:bg-accent/10"
                >
                  <button onClick={() => toggleTask(task)} className="shrink-0">
                    {task.status === "completed"
                      ? <CheckCircle className="w-4 h-4 text-green-400" />
                      : <Circle className="w-4 h-4 text-muted-foreground" />}
                  </button>
                  <span className={`text-sm flex-1 ${task.status === "completed" ? "line-through text-muted-foreground" : ""}`}>
                    {task.title}
                  </span>
                  <span className="text-xs text-muted-foreground">{STAGE_LABELS[task.stage] ?? task.stage}</span>
                  <span className={`text-xs font-medium ${PRIORITY_COLORS[task.priority] ?? ""}`}>{task.priority}</span>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-end gap-2 pt-2">
            <div className="flex-1">
              <Input
                placeholder="New task title..."
                value={newTask.title}
                onChange={(e) => setNewTask((t) => ({ ...t, title: e.target.value }))}
                onKeyDown={(e) => e.key === "Enter" && addTask()}
                className="bg-input border-border h-8 text-sm"
                data-testid="input-new-task"
              />
            </div>
            <Select value={newTask.priority} onValueChange={(v) => setNewTask((t) => ({ ...t, priority: v }))}>
              <SelectTrigger className="h-8 text-xs bg-input border-border w-28">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {["low", "medium", "high", "critical"].map((p) => (
                  <SelectItem key={p} value={p}>{p}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              data-testid="button-add-task"
              size="sm"
              onClick={addTask}
              disabled={addingTask || !newTask.title.trim()}
              className="gap-1.5 h-8 shrink-0"
            >
              <Plus className="w-3.5 h-3.5" />
              Add
            </Button>
          </div>
        </div>
      )}

      {activeView === "stages" && hasLifecycle && (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">Current stage: <strong className="text-foreground">{STAGE_LABELS[lifecycle?.current_stage ?? ""] ?? lifecycle?.current_stage}</strong></p>
          <Button
            data-testid="button-advance-stage"
            onClick={advanceStage}
            disabled={advancing}
            variant="outline"
            className="gap-2"
          >
            {advancing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ChevronRight className="w-4 h-4" />}
            Advance to Next Stage
          </Button>
        </div>
      )}

      {activeView === "issuance" && (
        <div className="space-y-3">
          {loadingIssuances ? (
            <div className="space-y-2">{[...Array(2)].map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}</div>
          ) : !issuances?.length ? (
            <div className="py-12 text-center text-sm text-muted-foreground border border-dashed border-border rounded-lg">
              No issuance records yet.
            </div>
          ) : (
            issuances.map((iss) => (
              <div key={iss.id} className="p-4 bg-card border border-border/50 rounded-lg flex items-center justify-between">
                <div>
                  <div className="font-medium text-sm">Vintage {iss.vintage_year}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{iss.registry_serial ?? "No serial"}</div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-primary">{iss.credits_issued?.toLocaleString()} credits</div>
                  <div className="text-xs text-muted-foreground">{iss.status}</div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
