import { useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { FileText, Upload, Trash2, RefreshCw, Brain, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { uploadProjectDocument, type ProjectDocument } from "@/lib/api";

const DOC_TYPES = [
  { value: "pdd", label: "PDD" },
  { value: "monitoring_report", label: "Monitoring Report" },
  { value: "validation_report", label: "Validation Report" },
  { value: "verification_report", label: "Verification Report" },
  { value: "methodology", label: "Methodology" },
  { value: "guidance", label: "Guidance" },
  { value: "other", label: "Other" },
];

const STATUS_COLORS: Record<string, string> = {
  ingested: "text-green-400",
  processing: "text-yellow-400",
  pending: "text-muted-foreground",
  failed: "text-red-400",
};

export default function DocumentsTab({ projectId }: { projectId: number }) {
  const { toast } = useToast();
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [docType, setDocType] = useState("pdd");
  const [uploading, setUploading] = useState(false);
  const [extractingId, setExtractingId] = useState<number | null>(null);

  const { data: docs, isLoading } = useQuery<ProjectDocument[]>({
    queryKey: ["/api/projects", projectId, "documents"],
    queryFn: async () => {
      const r = await fetch(`/api/projects/${projectId}/documents`);
      if (!r.ok) throw new Error("Failed");
      const d = await r.json();
      return Array.isArray(d) ? d : (d.documents ?? []);
    },
    refetchInterval: (q) => {
      const docs = q.state.data ?? [];
      return docs.some((d: ProjectDocument) => d.ingestion_status === "processing") ? 4000 : false;
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => apiRequest("DELETE", `/api/projects/${projectId}/documents/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "documents"] });
      toast({ title: "Document deleted" });
    },
  });

  const toggleAIMut = useMutation({
    mutationFn: ({ id, use }: { id: number; use: boolean }) =>
      apiRequest("PATCH", `/api/projects/${projectId}/documents/${id}/ai-context`, { use_as_ai_context: use }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "documents"] }),
  });

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await uploadProjectDocument(projectId, file, docType);
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "documents"] });
      toast({ title: "Document uploaded" });
    } catch (err) {
      toast({ title: "Upload failed", description: String(err), variant: "destructive" });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function extractIntelligence(docId: number) {
    setExtractingId(docId);
    try {
      const r = await fetch(`/api/projects/${projectId}/documents/${docId}/extract-intelligence`, {
        method: "POST",
      });
      if (!r.ok) throw new Error(await r.text());
      toast({ title: "Intelligence extracted", description: "Parameters updated from document" });
      qc.invalidateQueries({ queryKey: ["/api/projects", projectId, "parameters"] });
    } catch (err) {
      toast({ title: "Extraction failed", description: String(err), variant: "destructive" });
    } finally {
      setExtractingId(null);
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
          <FileText className="w-4 h-4 text-blue-400" />
        </div>
        <h2 className="text-base font-semibold">Documents</h2>
        <span className="ml-auto text-xs text-muted-foreground">{docs?.length ?? 0} documents</span>
      </div>

      <div className="flex items-end gap-3 p-4 bg-card border border-border/50 rounded-lg">
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Document type</Label>
          <Select value={docType} onValueChange={setDocType}>
            <SelectTrigger data-testid="select-upload-doc-type" className="bg-input border-border h-8 text-sm w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DOC_TYPES.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <input ref={fileRef} type="file" accept=".pdf,.docx,.doc,.xlsx,.csv,.txt" className="hidden" onChange={handleUpload} />
        <Button
          data-testid="button-upload-doc"
          disabled={uploading}
          onClick={() => fileRef.current?.click()}
          variant="outline"
          className="gap-2 h-8"
        >
          {uploading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
          {uploading ? "Uploading..." : "Upload Document"}
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
        </div>
      ) : !docs?.length ? (
        <div className="py-12 text-center text-sm text-muted-foreground border border-dashed border-border rounded-lg">
          No documents yet. Upload a PDF or DOCX to get started.
        </div>
      ) : (
        <div className="border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-card text-xs text-muted-foreground uppercase tracking-wider">
                <th className="text-left px-4 py-2.5">File</th>
                <th className="text-left px-4 py-2.5">Type</th>
                <th className="text-left px-4 py-2.5">Status</th>
                <th className="text-left px-4 py-2.5">AI Context</th>
                <th className="text-left px-4 py-2.5">Date</th>
                <th className="px-4 py-2.5 w-24" />
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id} data-testid={`row-doc-${d.id}`} className="border-b border-border/40 hover:bg-accent/20">
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
                      <span className="truncate max-w-[220px] font-medium text-xs">{d.original_filename || d.filename}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-xs text-muted-foreground">{d.doc_type || "—"}</td>
                  <td className="px-4 py-2.5">
                    <span className={`text-xs font-medium ${STATUS_COLORS[d.ingestion_status ?? "pending"] ?? "text-muted-foreground"}`}>
                      {d.ingestion_status ?? "pending"}
                      {d.ingestion_status === "processing" && <RefreshCw className="inline w-3 h-3 ml-1 animate-spin" />}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <button
                      data-testid={`button-toggle-ai-${d.id}`}
                      onClick={() => toggleAIMut.mutate({ id: d.id, use: !d.use_as_ai_context })}
                      title={d.use_as_ai_context ? "Remove from AI context" : "Add to AI context"}
                      className={`transition-colors ${d.use_as_ai_context ? "text-primary" : "text-muted-foreground hover:text-foreground"}`}
                    >
                      {d.use_as_ai_context ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                    </button>
                  </td>
                  <td className="px-4 py-2.5 text-xs text-muted-foreground">
                    {d.created_at ? new Date(d.created_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2 justify-end">
                      <button
                        data-testid={`button-extract-${d.id}`}
                        onClick={() => extractIntelligence(d.id)}
                        disabled={extractingId === d.id || d.ingestion_status !== "ingested"}
                        title="Extract intelligence to parameters"
                        className="text-muted-foreground hover:text-primary transition-colors disabled:opacity-40"
                      >
                        {extractingId === d.id
                          ? <RefreshCw className="w-4 h-4 animate-spin" />
                          : <Brain className="w-4 h-4" />}
                      </button>
                      <button
                        data-testid={`button-delete-doc-${d.id}`}
                        onClick={() => deleteMut.mutate(d.id)}
                        className="text-muted-foreground hover:text-destructive transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
