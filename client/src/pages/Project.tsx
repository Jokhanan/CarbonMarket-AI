import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRoute, Link } from "wouter";
import { ArrowLeft, Upload, FileText, Trash2, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { uploadProjectDocument, type Project, type ProjectDocument } from "@/lib/api";
import { apiRequest } from "@/lib/queryClient";

const DOC_TYPES = [
  { value: "pdd", label: "PDD" },
  { value: "monitoring_report", label: "Monitoring Report" },
  { value: "validation_report", label: "Rapport de validation" },
  { value: "verification_report", label: "Rapport de verification" },
  { value: "other", label: "Autre" },
];

export default function ProjectPage() {
  const [, params] = useRoute("/projects/:id");
  const projectId = parseInt(params?.id ?? "0");
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [docType, setDocType] = useState("pdd");
  const [uploading, setUploading] = useState(false);

  const { data: project, isLoading: loadingProject } = useQuery<Project>({
    queryKey: ["/api/projects", projectId],
    queryFn: async () => {
      const res = await fetch(`/api/projects/${projectId}`);
      if (!res.ok) throw new Error("Project not found");
      return res.json();
    },
    enabled: !!projectId,
  });

  const { data: docs, isLoading: loadingDocs } = useQuery<ProjectDocument[]>({
    queryKey: ["/api/projects", projectId, "documents"],
    queryFn: async () => {
      const res = await fetch(`/api/projects/${projectId}/documents`);
      if (!res.ok) throw new Error("Failed to load documents");
      const data = await res.json();
      return Array.isArray(data) ? data : (data.documents ?? []);
    },
    enabled: !!projectId,
  });

  const deleteMutation = useMutation({
    mutationFn: (docId: number) =>
      apiRequest("DELETE", `/api/projects/${projectId}/documents/${docId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/projects", projectId, "documents"] });
      toast({ title: "Document supprime" });
    },
  });

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await uploadProjectDocument(projectId, file, docType);
      queryClient.invalidateQueries({ queryKey: ["/api/projects", projectId, "documents"] });
      toast({ title: "Document uploade avec succes" });
    } catch (err) {
      toast({ title: "Erreur upload", description: String(err), variant: "destructive" });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  const STATUS_COLORS: Record<string, string> = {
    active: "bg-primary/15 text-primary border-primary/20",
    draft: "bg-secondary text-muted-foreground border-border",
    registered: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/projects">
          <a className="text-muted-foreground hover:text-foreground">
            <ArrowLeft className="w-5 h-5" />
          </a>
        </Link>
        {loadingProject ? (
          <Skeleton className="h-8 w-64" />
        ) : (
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{project?.name}</h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              {project?.standard} · {project?.methodology || "—"} · {project?.country || "—"}
            </p>
          </div>
        )}
        {project && (
          <span className={`ml-auto inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium border ${STATUS_COLORS[project.status] ?? "bg-secondary text-muted-foreground border-border"}`}>
            {project.status}
          </span>
        )}
      </div>

      {project && (
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Standard", value: project.standard },
            { label: "Methodologie", value: project.methodology || "—" },
            { label: "Pays", value: project.country || "—" },
            { label: "Type", value: project.doc_type || "—" },
          ].map(({ label, value }) => (
            <Card key={label} className="bg-card border-card-border">
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wider">{label}</p>
                <p className="text-sm font-semibold mt-1">{value}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {project?.description && (
        <Card className="bg-card border-card-border">
          <CardContent className="pt-4 pb-4 text-sm text-muted-foreground">{project.description}</CardContent>
        </Card>
      )}

      <Card className="bg-card border-card-border">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold">Upload un document</CardTitle>
        </CardHeader>
        <CardContent className="flex items-end gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Type de document</Label>
            <Select value={docType} onValueChange={setDocType}>
              <SelectTrigger data-testid="select-doc-type" className="bg-input border-border h-8 text-sm w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DOC_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.doc,.xlsx,.csv,.txt"
            className="hidden"
            data-testid="input-file-upload"
            onChange={handleUpload}
          />
          <Button
            data-testid="button-upload-doc"
            disabled={uploading}
            onClick={() => fileRef.current?.click()}
            variant="outline"
            className="gap-2 h-8"
          >
            {uploading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            {uploading ? "Upload..." : "Choisir fichier"}
          </Button>
        </CardContent>
      </Card>

      <Card className="bg-card border-card-border">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold">
            Documents ({loadingDocs ? "..." : docs?.length ?? 0})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loadingDocs ? (
            <div className="px-6 py-4 space-y-2">
              {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : !docs?.length ? (
            <div className="px-6 py-8 text-center text-sm text-muted-foreground">
              Aucun document. Uploadez un fichier ci-dessus.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-xs text-muted-foreground uppercase">
                  <th className="text-left px-4 py-2">Nom</th>
                  <th className="text-left px-4 py-2">Type</th>
                  <th className="text-left px-4 py-2">Date</th>
                  <th className="px-4 py-2 w-10" />
                </tr>
              </thead>
              <tbody>
                {docs.map((d) => (
                  <tr key={d.id} data-testid={`row-doc-${d.id}`} className="border-b border-border/50 hover:bg-accent/30">
                    <td className="px-4 py-2 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
                      <span className="truncate max-w-[300px]">{d.original_filename || d.filename}</span>
                    </td>
                    <td className="px-4 py-2 text-muted-foreground">{d.doc_type || "—"}</td>
                    <td className="px-4 py-2 text-muted-foreground text-xs">
                      {d.created_at ? new Date(d.created_at).toLocaleDateString("fr-FR") : "—"}
                    </td>
                    <td className="px-4 py-2">
                      <button
                        data-testid={`button-delete-doc-${d.id}`}
                        onClick={() => deleteMutation.mutate(d.id)}
                        className="text-muted-foreground hover:text-destructive transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
