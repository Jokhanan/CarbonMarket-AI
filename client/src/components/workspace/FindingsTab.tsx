import { useState, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { MessageSquare, Upload, RefreshCw, ChevronDown, ChevronUp, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";

interface Finding {
  id: number;
  finding_type: string;
  title: string;
  description: string;
  status: string;
  response?: string;
  section_ref?: string;
  severity?: string;
}

const TYPE_COLORS: Record<string, string> = {
  CAR: "text-red-400 bg-red-400/10 border-red-400/20",
  CL: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20",
  FAR: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  CR: "text-purple-400 bg-purple-400/10 border-purple-400/20",
};

const STATUS_COLORS: Record<string, string> = {
  open: "text-red-400",
  in_progress: "text-yellow-400",
  resolved: "text-green-400",
  closed: "text-muted-foreground",
};

function FindingRow({ finding, projectId }: { finding: Finding; projectId: number }) {
  const { toast } = useToast();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [response, setResponse] = useState(finding.response ?? "");
  const [status, setStatus] = useState(finding.status ?? "open");
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);

  async function generateResponse() {
    setGenerating(true);
    try {
      const r = await fetch(`/api/projects/${projectId}/respond-to-finding`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ finding_id: finding.id, action: "generate" }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setResponse(data.response ?? data.draft ?? "");
    } catch (e) {
      toast({ title: "Generation failed", description: String(e), variant: "destructive" });
    } finally {
      setGenerating(false);
    }
  }

  async function saveResponse() {
    setSaving(true);
    try {
      await fetch(`/api/projects/${projectId}/respond-to-finding`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ finding_id: finding.id, response, status, action: "save" }),
      });
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "findings"] });
      toast({ title: "Response saved" });
    } catch (e) {
      toast({ title: "Save failed", description: String(e), variant: "destructive" });
    } finally {
      setSaving(false);
    }
  }

  const typeKey = (finding.finding_type ?? "").toUpperCase();
  const typeColor = TYPE_COLORS[typeKey] ?? "text-muted-foreground bg-muted border-border";

  return (
    <div className="border border-border/50 rounded-lg overflow-hidden">
      <button
        data-testid={`finding-row-${finding.id}`}
        className="w-full flex items-center justify-between px-4 py-3 bg-card hover:bg-accent/20 text-left"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className={`shrink-0 text-xs font-bold px-1.5 py-0.5 rounded border ${typeColor}`}>
            {typeKey || "OBS"}
          </span>
          <span className="text-sm font-medium truncate">{finding.title}</span>
          {finding.section_ref && (
            <span className="text-xs text-muted-foreground shrink-0">§{finding.section_ref}</span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-2">
          <span className={`text-xs font-medium ${STATUS_COLORS[finding.status] ?? ""}`}>{finding.status}</span>
          {open ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
        </div>
      </button>
      {open && (
        <div className="px-4 py-4 border-t border-border/50 bg-background space-y-3">
          <p className="text-sm text-muted-foreground">{finding.description}</p>
          <div className="flex items-center gap-2">
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="h-7 text-xs bg-input border-border w-36">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {["open", "in_progress", "resolved", "closed"].map((s) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              data-testid={`button-generate-response-${finding.id}`}
              size="sm"
              variant="outline"
              onClick={generateResponse}
              disabled={generating}
              className="gap-1.5 h-7 text-xs"
            >
              {generating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              {generating ? "Generating..." : "Draft AI Response"}
            </Button>
          </div>
          <Textarea
            value={response}
            onChange={(e) => setResponse(e.target.value)}
            placeholder="Type or generate a response to this finding..."
            rows={4}
            className="bg-input border-border text-sm resize-none"
            data-testid={`textarea-response-${finding.id}`}
          />
          <Button
            data-testid={`button-save-response-${finding.id}`}
            size="sm"
            onClick={saveResponse}
            disabled={saving || !response.trim()}
            className="gap-1.5"
          >
            {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : null}
            {saving ? "Saving..." : "Save Response"}
          </Button>
        </div>
      )}
    </div>
  );
}

export default function FindingsTab({ projectId }: { projectId: number }) {
  const { toast } = useToast();
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const { data: findings, isLoading } = useQuery<Finding[]>({
    queryKey: ["/api/projects", projectId, "findings"],
    queryFn: async () => {
      const r = await fetch(`/api/projects/${projectId}/audit-simulation/history`);
      if (!r.ok) throw new Error("Failed");
      const history = await r.json();
      if (!Array.isArray(history) || history.length === 0) return [];

      // Flatten findings from all audit runs, normalising field names.
      // Audit findings shape: { type, title, severity, description, category }
      // Our Finding interface:  { finding_type, title, status, description, ... }
      const findings: Finding[] = [];
      let uid = 1;
      for (const sim of history) {
        const raw = sim.findings ?? [];
        const parsed: any[] = typeof raw === "string" ? JSON.parse(raw) : raw;
        for (const f of parsed) {
          findings.push({
            id: f.id ?? uid++,
            finding_type: (f.finding_type ?? f.type ?? "OBS").toUpperCase(),
            title: f.title ?? f.message ?? "Untitled",
            description: f.description ?? "",
            status: f.status ?? "open",
            response: f.response,
            section_ref: f.section_ref ?? f.category,
            severity: f.severity,
          });
        }
      }
      return findings;
    },
  });

  async function uploadFindingsDoc(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const r = await fetch(`/api/projects/${projectId}/parse-findings-document`, {
        method: "POST",
        body: fd,
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      toast({ title: `${data.findings?.length ?? 0} findings extracted` });
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "findings"] });
    } catch (e) {
      toast({ title: "Upload failed", description: String(e), variant: "destructive" });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-pink-500/10 flex items-center justify-center">
          <MessageSquare className="w-4 h-4 text-pink-400" />
        </div>
        <h2 className="text-base font-semibold">Findings Response</h2>
        <div className="ml-auto flex items-center gap-2">
          <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden" onChange={uploadFindingsDoc} />
          <Button
            data-testid="button-upload-findings"
            size="sm"
            variant="outline"
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="gap-1.5 h-7 text-xs"
          >
            {uploading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
            Import Findings Doc
          </Button>
        </div>
      </div>

      <div className="p-4 bg-card border border-border/50 rounded-lg text-xs text-muted-foreground">
        Findings are sourced from audit simulations. Upload a validation/verification report to extract CAR/CL/FAR findings automatically, or respond to audit simulation findings below.
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}</div>
      ) : !findings?.length ? (
        <div className="py-12 text-center text-sm text-muted-foreground border border-dashed border-border rounded-lg">
          No findings yet. Run an Audit Simulation or import a validation report.
        </div>
      ) : (
        <div className="space-y-2">
          {findings.map((f, i) => (
            <FindingRow key={`${f.id}-${i}`} finding={f} projectId={projectId} />
          ))}
        </div>
      )}
    </div>
  );
}
