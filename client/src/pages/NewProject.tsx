import { useState } from "react";
import { useLocation } from "wouter";
import { ArrowLeft, ArrowRight, Check, RefreshCw, Leaf } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { STANDARD_OPTIONS, METHODOLOGY_GROUPS } from "@/lib/api";

const DOC_TYPE_OPTIONS = [
  { value: "PDD",    label: "PDD",    desc: "Project Design Document — standalone project" },
  { value: "PoA-DD", label: "PoA-DD", desc: "Programme of Activities Design Document" },
  { value: "MR",     label: "MR",     desc: "Monitoring Report (linked to an existing project)" },
  { value: "VPA-DD", label: "VPA-DD", desc: "VPA Design Document (part of a PoA)" },
];

const STEPS = ["Project Type", "Methodology", "Location & Details"];

export default function NewProject() {
  const [, navigate] = useLocation();
  const { toast } = useToast();
  const [step, setStep] = useState(0);
  const [creating, setCreating] = useState(false);

  const [form, setForm] = useState({
    name: "",
    standard: "GoldStandard",
    doc_type: "PDD",
    methodology: "",
    country: "",
    description: "",
    crediting_period_years: 5,
    crediting_period_start: new Date().getFullYear(),
  });

  const set = (k: string, v: string | number) => setForm((f) => ({ ...f, [k]: v }));

  function canNext(): boolean {
    if (step === 0) return !!form.doc_type && !!form.standard;
    if (step === 1) return !!form.methodology;
    if (step === 2) return !!form.name.trim() && !!form.country.trim();
    return false;
  }

  async function create() {
    setCreating(true);
    try {
      const r = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!r.ok) throw new Error(await r.text());
      const project = await r.json();

      // Initialize parameters immediately
      await fetch(`/api/projects/${project.id}/parameters/initialize`, { method: "POST" }).catch(() => {});

      toast({ title: "Project created", description: form.name });
      navigate(`/projects/${project.id}`);
    } catch (e) {
      toast({ title: "Creation failed", description: String(e), variant: "destructive" });
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => step > 0 ? setStep(step - 1) : navigate("/projects")}
          className="gap-1.5 text-muted-foreground h-8 px-2"
        >
          <ArrowLeft className="w-4 h-4" />
          {step === 0 ? "Cancel" : "Back"}
        </Button>
        <div className="h-4 w-px bg-border" />
        <h1 className="text-lg font-semibold">New Project</h1>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-0 mb-8">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center">
            <div className="flex items-center gap-2">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-colors ${
                i < step
                  ? "bg-primary border-primary text-white"
                  : i === step
                  ? "border-primary text-primary"
                  : "border-border text-muted-foreground"
              }`}>
                {i < step ? <Check className="w-3.5 h-3.5" /> : i + 1}
              </div>
              <span className={`text-xs font-medium ${i === step ? "text-foreground" : "text-muted-foreground"}`}>
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`h-px w-12 mx-3 ${i < step ? "bg-primary" : "bg-border"}`} />
            )}
          </div>
        ))}
      </div>

      {/* Step 0 — Project Type */}
      {step === 0 && (
        <div className="space-y-5">
          <div>
            <h2 className="text-base font-semibold mb-1">Select project type</h2>
            <p className="text-sm text-muted-foreground">What kind of document are you developing?</p>
          </div>

          <div className="space-y-2">
            {DOC_TYPE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                data-testid={`doc-type-${opt.value}`}
                onClick={() => set("doc_type", opt.value)}
                className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                  form.doc_type === opt.value
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-border/80 bg-card"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded flex items-center justify-center font-bold text-xs shrink-0 ${
                    form.doc_type === opt.value ? "bg-primary text-white" : "bg-muted text-muted-foreground"
                  }`}>
                    {opt.label}
                  </div>
                  <div>
                    <div className="font-semibold text-sm">{opt.label}</div>
                    <div className="text-xs text-muted-foreground mt-0.5">{opt.desc}</div>
                  </div>
                  {form.doc_type === opt.value && (
                    <Check className="w-4 h-4 text-primary ml-auto shrink-0" />
                  )}
                </div>
              </button>
            ))}
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Registry / Standard</Label>
            <div className="grid grid-cols-3 gap-2">
              {STANDARD_OPTIONS.map((s) => (
                <button
                  key={s}
                  data-testid={`standard-${s}`}
                  onClick={() => set("standard", s)}
                  className={`py-2 px-3 rounded-lg border text-sm font-medium transition-all ${
                    form.standard === s
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border bg-card text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Step 1 — Methodology */}
      {step === 1 && (
        <div className="space-y-5">
          <div>
            <h2 className="text-base font-semibold mb-1">Select methodology</h2>
            <p className="text-sm text-muted-foreground">Choose the carbon accounting methodology for your project.</p>
          </div>

          {Object.entries(METHODOLOGY_GROUPS).map(([group, methodologies]) => (
            <div key={group}>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">{group}</p>
              <div className="grid grid-cols-2 gap-2">
                {methodologies.map((m) => (
                  <button
                    key={m}
                    data-testid={`methodology-${m}`}
                    onClick={() => set("methodology", m)}
                    className={`p-3 rounded-lg border text-left text-sm font-medium transition-all ${
                      form.methodology === m
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-border bg-card text-muted-foreground hover:text-foreground hover:border-border/80"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      {m}
                      {form.methodology === m && <Check className="w-4 h-4 shrink-0" />}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ))}

          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Or enter methodology code manually</Label>
            <Input
              value={form.methodology}
              onChange={(e) => set("methodology", e.target.value)}
              placeholder="e.g. VM0050, TPDDTEC, ACM0002"
              className="bg-input border-border"
              data-testid="input-methodology-manual"
            />
          </div>
        </div>
      )}

      {/* Step 2 — Location & Details */}
      {step === 2 && (
        <div className="space-y-4">
          <div>
            <h2 className="text-base font-semibold mb-1">Project details</h2>
            <p className="text-sm text-muted-foreground">Name your project and add location information.</p>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Project Name *</Label>
            <Input
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="e.g. Ghana Clean Cookstoves Programme Phase 1"
              className="bg-input border-border"
              autoFocus
              data-testid="input-project-name"
            />
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Country *</Label>
            <Input
              value={form.country}
              onChange={(e) => set("country", e.target.value)}
              placeholder="e.g. Ghana, Kenya, India"
              className="bg-input border-border"
              data-testid="input-country"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Crediting Period (years)</Label>
              <Input
                type="number" min={1} max={30}
                value={form.crediting_period_years}
                onChange={(e) => set("crediting_period_years", parseInt(e.target.value) || 5)}
                className="bg-input border-border"
                data-testid="input-crediting-years"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Start Year</Label>
              <Input
                type="number" min={2000} max={2050}
                value={form.crediting_period_start}
                onChange={(e) => set("crediting_period_start", parseInt(e.target.value) || 2024)}
                className="bg-input border-border"
                data-testid="input-start-year"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Description (optional)</Label>
            <Textarea
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
              placeholder="Brief description of the project scope and objectives..."
              rows={3}
              className="bg-input border-border resize-none text-sm"
              data-testid="textarea-description"
            />
          </div>

          <div className="p-3 bg-primary/5 border border-primary/15 rounded-lg text-xs text-muted-foreground">
            <div className="flex items-start gap-2">
              <Leaf className="w-4 h-4 text-primary shrink-0 mt-0.5" />
              <div>
                <strong className="text-foreground">{form.standard} · {form.methodology} · {form.doc_type}</strong>
                <br />Parameters will be auto-initialized from methodology defaults after creation.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between mt-8 pt-6 border-t border-border/50">
        {step === 0 ? (
          <div />
        ) : (
          <Button variant="outline" onClick={() => setStep(step - 1)} className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
        )}

        {step < STEPS.length - 1 ? (
          <Button
            data-testid="button-next-step"
            onClick={() => setStep(step + 1)}
            disabled={!canNext()}
            className="gap-2"
          >
            Next
            <ArrowRight className="w-4 h-4" />
          </Button>
        ) : (
          <Button
            data-testid="button-create-project"
            onClick={create}
            disabled={creating || !canNext()}
            className="gap-2"
          >
            {creating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
            {creating ? "Creating..." : "Create Project"}
          </Button>
        )}
      </div>
    </div>
  );
}
