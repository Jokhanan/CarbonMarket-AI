import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Save, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { STANDARD_OPTIONS, ALL_METHODOLOGIES, type Project } from "@/lib/api";

const DOC_TYPES = ["PDD", "PoA-DD", "MR", "VPA-DD", "ValVer"];
const STATUS_OPTIONS = ["draft", "active", "review", "registered", "archived"];

export default function SetupTab({ project }: { project: Project }) {
  const { toast } = useToast();
  const qc = useQueryClient();
  const [form, setForm] = useState({
    name: project.name ?? "",
    standard: project.standard ?? "",
    methodology: project.methodology ?? "",
    country: project.country ?? "",
    doc_type: project.doc_type ?? "",
    status: project.status ?? "draft",
    description: project.description ?? "",
    crediting_period_years: project.crediting_period_years ?? 5,
    crediting_period_start: project.crediting_period_start ?? new Date().getFullYear(),
  });

  const saveMutation = useMutation({
    mutationFn: () => apiRequest("PATCH", `/api/projects/${project.id}`, form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["/api/projects", project.id] });
      toast({ title: "Project saved" });
    },
    onError: (e) => toast({ title: "Save failed", description: String(e), variant: "destructive" }),
  });

  const set = (k: string, v: string | number) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center">
          <Settings className="w-4 h-4 text-primary" />
        </div>
        <h2 className="text-base font-semibold">Project Settings</h2>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2 space-y-1.5">
          <Label className="text-xs text-muted-foreground">Project Name</Label>
          <Input
            data-testid="input-project-name"
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            className="bg-input border-border"
          />
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Standard</Label>
          <Select value={form.standard} onValueChange={(v) => set("standard", v)}>
            <SelectTrigger data-testid="select-standard" className="bg-input border-border">
              <SelectValue placeholder="Select standard" />
            </SelectTrigger>
            <SelectContent>
              {STANDARD_OPTIONS.map((s) => (
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Document Type</Label>
          <Select value={form.doc_type} onValueChange={(v) => set("doc_type", v)}>
            <SelectTrigger data-testid="select-doc-type" className="bg-input border-border">
              <SelectValue placeholder="Select type" />
            </SelectTrigger>
            <SelectContent>
              {DOC_TYPES.map((d) => (
                <SelectItem key={d} value={d}>{d}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Methodology</Label>
          <Select value={form.methodology} onValueChange={(v) => set("methodology", v)}>
            <SelectTrigger data-testid="select-methodology" className="bg-input border-border">
              <SelectValue placeholder="Select methodology" />
            </SelectTrigger>
            <SelectContent>
              {ALL_METHODOLOGIES.map((m) => (
                <SelectItem key={m} value={m}>{m}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Country</Label>
          <Input
            data-testid="input-country"
            value={form.country}
            onChange={(e) => set("country", e.target.value)}
            placeholder="e.g. Ghana"
            className="bg-input border-border"
          />
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Status</Label>
          <Select value={form.status} onValueChange={(v) => set("status", v)}>
            <SelectTrigger data-testid="select-status" className="bg-input border-border">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {STATUS_OPTIONS.map((s) => (
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Crediting Years</Label>
            <Input
              type="number"
              min={1} max={30}
              data-testid="input-crediting-years"
              value={form.crediting_period_years}
              onChange={(e) => set("crediting_period_years", parseInt(e.target.value) || 5)}
              className="bg-input border-border"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Start Year</Label>
            <Input
              type="number"
              min={2000} max={2050}
              data-testid="input-start-year"
              value={form.crediting_period_start}
              onChange={(e) => set("crediting_period_start", parseInt(e.target.value) || 2024)}
              className="bg-input border-border"
            />
          </div>
        </div>

        <div className="col-span-2 space-y-1.5">
          <Label className="text-xs text-muted-foreground">Description</Label>
          <Textarea
            data-testid="textarea-description"
            value={form.description}
            onChange={(e) => set("description", e.target.value)}
            rows={3}
            className="bg-input border-border resize-none text-sm"
          />
        </div>
      </div>

      <div className="pt-2">
        <Button
          data-testid="button-save-setup"
          onClick={() => saveMutation.mutate()}
          disabled={saveMutation.isPending}
          className="gap-2"
        >
          <Save className="w-4 h-4" />
          {saveMutation.isPending ? "Saving..." : "Save Changes"}
        </Button>
      </div>
    </div>
  );
}
