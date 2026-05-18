import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { Sparkles, Upload, RefreshCw, AlertTriangle, Info, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { uploadDocx, startAIReview, pollAIReview, type AIReviewResult, type AIReviewSection } from "@/lib/api";

const STANDARDS = ["GoldStandard", "VCS", "CDM"];
const DOC_TYPES = ["PDD", "MonitoringReport", "ValidationReport", "VerificationReport"];

const LEVEL_COLORS: Record<string, string> = {
  CAR: "bg-red-500/15 text-red-400 border-red-500/20",
  CL: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
  FAR: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  OK: "bg-primary/15 text-primary border-primary/20",
  INFO: "bg-secondary text-muted-foreground border-border",
};

function SectionCard({ section }: { section: AIReviewSection }) {
  const hasIssues = section.findings?.some((f) => ["CAR", "CL", "FAR"].includes(f.level?.toUpperCase() ?? ""));
  return (
    <Card className="bg-card border-card-border" data-testid={`section-${section.section?.replace(/\s+/g, "-").toLowerCase()}`}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold">{section.section}</CardTitle>
          {!hasIssues && (
            <span className="flex items-center gap-1 text-xs text-primary">
              <CheckCircle2 className="w-3.5 h-3.5" /> Conforme
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {section.findings?.map((f, i) => {
          const lvl = (f.level ?? "INFO").toUpperCase();
          const colorClass = LEVEL_COLORS[lvl] ?? LEVEL_COLORS.INFO;
          return (
            <div key={i} className={`flex items-start gap-2 px-3 py-2 rounded border ${colorClass}`}>
              <span className="text-xs font-bold shrink-0 mt-0.5">[{lvl}]</span>
              <p className="text-sm">{f.message}</p>
            </div>
          );
        })}
        {(!section.findings || section.findings.length === 0) && (
          <p className="text-xs text-muted-foreground">Aucun finding pour cette section.</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function AIReview() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [standard, setStandard] = useState("GoldStandard");
  const [docType, setDocType] = useState("PDD");
  const [result, setResult] = useState<AIReviewResult | null>(null);
  const [polling, setPolling] = useState(false);
  const { toast } = useToast();

  const reviewMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile) throw new Error("Aucun fichier selectionne");
      const { file_path } = await uploadDocx(selectedFile);
      const { task_id } = await startAIReview({ standard, doc_type: docType, file_path, user_doc_path: file_path });
      return task_id;
    },
    onSuccess: async (taskId) => {
      setPolling(true);
      let attempts = 0;
      const MAX = 60;
      const interval = setInterval(async () => {
        attempts++;
        try {
          const data = await pollAIReview(taskId);
          if (data.status === "completed" || data.results || data.sections) {
            clearInterval(interval);
            setPolling(false);
            setResult(data);
          } else if (data.status === "error" || data.error) {
            clearInterval(interval);
            setPolling(false);
            toast({ title: "Erreur AI Review", description: data.error, variant: "destructive" });
          } else if (attempts >= MAX) {
            clearInterval(interval);
            setPolling(false);
            toast({ title: "Timeout", description: "La review n'a pas abouti dans le temps imparti.", variant: "destructive" });
          }
        } catch {
          clearInterval(interval);
          setPolling(false);
        }
      }, 3000);
    },
    onError: (err) => {
      toast({ title: "Erreur", description: String(err), variant: "destructive" });
    },
  });

  const sections = result?.sections ?? result?.results ?? [];
  const carCount = sections.reduce((acc, s) => acc + (s.findings?.filter((f) => f.level?.toUpperCase() === "CAR").length ?? 0), 0);
  const clCount = sections.reduce((acc, s) => acc + (s.findings?.filter((f) => f.level?.toUpperCase() === "CL").length ?? 0), 0);
  const farCount = sections.reduce((acc, s) => acc + (s.findings?.filter((f) => f.level?.toUpperCase() === "FAR").length ?? 0), 0);

  const isRunning = reviewMutation.isPending || polling;

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center gap-3">
        <Sparkles className="w-6 h-6 text-primary" />
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">AI Review</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Revue IA section par section (CAR / CL / FAR)</p>
        </div>
      </div>

      <div className="grid grid-cols-[340px_1fr] gap-6 items-start">
        <Card className="bg-card border-card-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground font-medium">Standard</Label>
              <Select value={standard} onValueChange={setStandard}>
                <SelectTrigger data-testid="select-standard-review" className="bg-input border-border h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STANDARDS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground font-medium">Type de document</Label>
              <Select value={docType} onValueChange={setDocType}>
                <SelectTrigger data-testid="select-doctype-review" className="bg-input border-border h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DOC_TYPES.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div className="border-t border-border pt-3 space-y-2">
              <Label className="text-xs text-muted-foreground font-medium">Fichier .docx</Label>
              <input
                ref={fileRef}
                type="file"
                accept=".docx"
                className="hidden"
                data-testid="input-file-review"
                onChange={(e) => { setSelectedFile(e.target.files?.[0] ?? null); setResult(null); }}
              />
              <button
                data-testid="button-choose-file-review"
                onClick={() => fileRef.current?.click()}
                className="w-full flex flex-col items-center gap-2 py-5 rounded-md border border-dashed border-border hover:border-primary/50 transition-colors text-muted-foreground hover:text-foreground cursor-pointer"
              >
                <Upload className="w-6 h-6" />
                <span className="text-xs">
                  {selectedFile ? selectedFile.name : "Cliquez pour selectionner"}
                </span>
              </button>
            </div>

            <Button
              data-testid="button-start-review"
              onClick={() => reviewMutation.mutate()}
              disabled={!selectedFile || isRunning}
              className="w-full gap-2"
            >
              {isRunning
                ? <><RefreshCw className="w-4 h-4 animate-spin" /> {polling ? "Analyse en cours..." : "Lancement..."}</>
                : <><Sparkles className="w-4 h-4" /> Lancer l'AI Review</>
              }
            </Button>

            {polling && (
              <p className="text-xs text-muted-foreground text-center">
                Polling toutes les 3s — peut prendre 1-2 minutes
              </p>
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          {!result && !isRunning && (
            <div className="flex flex-col items-center justify-center h-64 text-center text-muted-foreground border border-dashed border-border rounded-lg">
              <Sparkles className="w-10 h-10 mb-3 opacity-30" />
              <p className="text-sm">Selectionnez un fichier .docx et lancez la revue IA.</p>
              <p className="text-xs mt-1">La review analyse le document section par section.</p>
            </div>
          )}

          {isRunning && (
            <div className="flex flex-col items-center justify-center h-64 gap-4 text-muted-foreground">
              <RefreshCw className="w-8 h-8 animate-spin text-primary" />
              <div className="text-center">
                <p className="text-sm font-medium">AI Review en cours</p>
                <p className="text-xs mt-1">Analyse du document par le LLM...</p>
              </div>
            </div>
          )}

          {result && (
            <>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: "CAR", value: carCount, color: "text-red-400" },
                  { label: "CL", value: clCount, color: "text-yellow-400" },
                  { label: "FAR", value: farCount, color: "text-blue-400" },
                ].map(({ label, value, color }) => (
                  <Card key={label} className="bg-card border-card-border">
                    <CardContent className="pt-4 pb-4">
                      <p className={`text-xs font-semibold uppercase ${color}`}>{label}</p>
                      <p className="text-3xl font-bold mt-1" data-testid={`text-${label.toLowerCase()}-count`}>{value}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="space-y-3">
                {sections.map((s, i) => <SectionCard key={i} section={s} />)}
                {!sections.length && (
                  <Card className="bg-card border-card-border">
                    <CardContent className="py-8 text-center text-sm text-muted-foreground">
                      Aucune section retournee.
                    </CardContent>
                  </Card>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
