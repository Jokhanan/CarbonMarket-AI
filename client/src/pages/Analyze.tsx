import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { Upload, FileSearch, RefreshCw, AlertCircle, AlertTriangle, Info, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { uploadDocx, analyzeSelected, type AnalyzeResult, type Finding } from "@/lib/api";

const STANDARDS = ["GoldStandard", "VCS", "CDM"];
const DOC_TYPES = ["PDD", "MonitoringReport", "ValidationReport", "VerificationReport"];
const VERSIONS: Record<string, string[]> = {
  PDD: ["PDD_v1_0", "PDD_v2_0"],
  MonitoringReport: ["MR_v1_0"],
  ValidationReport: ["ValReport_v1_0"],
  VerificationReport: ["VerReport_v1_0"],
};

const LEVEL_CONFIG = {
  ERROR: { icon: AlertCircle, color: "text-red-400", bg: "bg-red-500/10 border-red-500/20" },
  WARNING: { icon: AlertTriangle, color: "text-yellow-400", bg: "bg-yellow-500/10 border-yellow-500/20" },
  INFO: { icon: Info, color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
} as const;

function FindingRow({ f }: { f: Finding }) {
  const cfg = LEVEL_CONFIG[f.level] ?? LEVEL_CONFIG.INFO;
  const Icon = cfg.icon;
  return (
    <div className={`flex items-start gap-3 px-4 py-3 rounded-md border ${cfg.bg}`} data-testid={`finding-${f.level}-${f.code}`}>
      <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${cfg.color}`} />
      <div className="min-w-0">
        <span className={`text-xs font-semibold ${cfg.color}`}>[{f.level}]</span>
        {f.code && <span className="ml-2 text-xs text-muted-foreground font-mono">{f.code}</span>}
        {f.section && <span className="ml-2 text-xs text-muted-foreground">§{f.section}</span>}
        <p className="text-sm mt-0.5 text-foreground">{f.message}</p>
      </div>
    </div>
  );
}

export default function Analyze() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [standard, setStandard] = useState("GoldStandard");
  const [docType, setDocType] = useState("PDD");
  const [version, setVersion] = useState("PDD_v1_0");
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [uploadedPath, setUploadedPath] = useState<string | null>(null);

  const analyzeMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile) throw new Error("Aucun fichier selectionne");
      const { file_path } = await uploadDocx(selectedFile);
      setUploadedPath(file_path);
      return analyzeSelected({ file_path, standard, doc_type: docType, version });
    },
    onSuccess: (data) => setResult(data),
  });

  const errors = result?.findings?.filter((f) => f.level === "ERROR").length ?? 0;
  const warnings = result?.findings?.filter((f) => f.level === "WARNING").length ?? 0;
  const infos = result?.findings?.filter((f) => f.level === "INFO").length ?? 0;

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center gap-3">
        <FileSearch className="w-6 h-6 text-primary" />
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Analyse Compliance</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Verification de conformite des documents carbone</p>
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
                <SelectTrigger data-testid="select-standard" className="bg-input border-border h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STANDARDS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground font-medium">Type de document</Label>
              <Select value={docType} onValueChange={(v) => { setDocType(v); setVersion(VERSIONS[v]?.[0] ?? ""); }}>
                <SelectTrigger data-testid="select-doc-type" className="bg-input border-border h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DOC_TYPES.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground font-medium">Version</Label>
              <Select value={version} onValueChange={setVersion}>
                <SelectTrigger data-testid="select-version" className="bg-input border-border h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(VERSIONS[docType] ?? ["v1_0"]).map((v) => (
                    <SelectItem key={v} value={v}>{v}</SelectItem>
                  ))}
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
                data-testid="input-file-analyze"
                onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
              />
              <button
                data-testid="button-choose-file"
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
              data-testid="button-analyze"
              onClick={() => analyzeMutation.mutate()}
              disabled={!selectedFile || analyzeMutation.isPending}
              className="w-full gap-2"
            >
              {analyzeMutation.isPending
                ? <><RefreshCw className="w-4 h-4 animate-spin" /> Analyse en cours...</>
                : <><FileSearch className="w-4 h-4" /> Lancer l'analyse</>
              }
            </Button>

            {analyzeMutation.isError && (
              <p className="text-xs text-destructive">{String(analyzeMutation.error)}</p>
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          {!result && !analyzeMutation.isPending && (
            <div className="flex flex-col items-center justify-center h-64 text-center text-muted-foreground border border-dashed border-border rounded-lg">
              <FileSearch className="w-10 h-10 mb-3 opacity-30" />
              <p className="text-sm">Selectionnez un fichier .docx et lancez l'analyse.</p>
            </div>
          )}

          {analyzeMutation.isPending && (
            <div className="flex flex-col items-center justify-center h-64 gap-4 text-muted-foreground">
              <RefreshCw className="w-6 h-6 animate-spin text-primary" />
              <p className="text-sm">Analyse en cours...</p>
            </div>
          )}

          {result && (
            <>
              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: "Score", value: `${Math.round((result.score ?? 0) * 100)}%`, icon: CheckCircle2, color: "text-primary" },
                  { label: "Erreurs", value: errors, icon: AlertCircle, color: "text-red-400" },
                  { label: "Avertissements", value: warnings, icon: AlertTriangle, color: "text-yellow-400" },
                  { label: "Infos", value: infos, icon: Info, color: "text-blue-400" },
                ].map(({ label, value, icon: Icon, color }) => (
                  <Card key={label} className="bg-card border-card-border">
                    <CardContent className="pt-4 pb-4 flex items-center justify-between">
                      <div>
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">{label}</p>
                        <p className="text-2xl font-bold mt-1" data-testid={`text-${label.toLowerCase()}`}>{value}</p>
                      </div>
                      <Icon className={`w-7 h-7 ${color} opacity-70`} />
                    </CardContent>
                  </Card>
                ))}
              </div>

              {typeof result.score === "number" && (
                <div className="space-y-1.5">
                  <p className="text-xs text-muted-foreground">Score de conformite</p>
                  <Progress value={(result.score ?? 0) * 100} className="h-2" />
                </div>
              )}

              <Card className="bg-card border-card-border">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold">
                    Findings ({result.findings?.length ?? 0})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {result.findings?.length ? (
                    result.findings.map((f, i) => <FindingRow key={i} f={f} />)
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-6">Aucun finding.</p>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
