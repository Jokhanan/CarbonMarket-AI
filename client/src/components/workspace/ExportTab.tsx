import { useState } from "react";
import { Download, FileText, RefreshCw, Table } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import type { Project } from "@/lib/api";

export default function ExportTab({ project }: { project: Project }) {
  const { toast } = useToast();
  const [format, setFormat] = useState<"docx" | "xlsx">("docx");
  const [exporting, setExporting] = useState(false);

  async function exportDoc() {
    setExporting(true);
    try {
      const docType = project.doc_type?.toLowerCase() ?? "pdd";
      const url =
        format === "xlsx"
          ? `/api/projects/${project.id}/export-calculation`
          : `/api/projects/${project.id}/generate-template`;
      const body =
        format === "xlsx"
          ? { doc_type: docType }
          : { doc_type: docType, include_calculations: true };
      const r = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(await r.text());

      const contentType = r.headers.get("Content-Type") ?? "";
      if (contentType.includes("application/json")) {
        const data = await r.json();
        const url = data.download_url ?? data.file_url ?? data.url;
        if (url) {
          const a = document.createElement("a");
          a.href = url;
          a.download = `${project.name}_export.${format}`;
          a.click();
          toast({ title: "Export ready" });
        } else {
          toast({ title: "Export complete", description: JSON.stringify(data).slice(0, 100) });
        }
      } else {
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${project.name}_export.${format}`;
        a.click();
        URL.revokeObjectURL(url);
        toast({ title: "Download started" });
      }
    } catch (e) {
      toast({ title: "Export failed", description: String(e), variant: "destructive" });
    } finally {
      setExporting(false);
    }
  }

  const EXPORT_OPTIONS = [
    {
      format: "docx" as const,
      icon: FileText,
      label: "DOCX — Project Document",
      desc: "Full PDD/MR/PoA-DD with AI-drafted sections, tables, and formatted content.",
    },
    {
      format: "xlsx" as const,
      icon: Table,
      label: "Excel — ER Workbook",
      desc: "Fully traceable ER calculation workbook with live formulas and vintage table.",
    },
  ];

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-indigo-500/10 flex items-center justify-center">
          <Download className="w-4 h-4 text-indigo-400" />
        </div>
        <h2 className="text-base font-semibold">Export</h2>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {EXPORT_OPTIONS.map((opt) => (
          <button
            key={opt.format}
            data-testid={`export-option-${opt.format}`}
            onClick={() => setFormat(opt.format)}
            className={`p-4 rounded-lg border text-left transition-all ${
              format === opt.format
                ? "border-primary/50 bg-primary/5"
                : "border-border/50 bg-card hover:border-border hover:bg-accent/20"
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <opt.icon className={`w-5 h-5 ${format === opt.format ? "text-primary" : "text-muted-foreground"}`} />
              <span className="font-medium text-sm">{opt.label}</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">{opt.desc}</p>
          </button>
        ))}
      </div>

      <div className="p-4 bg-card border border-border/50 rounded-lg space-y-3">
        <p className="text-xs text-muted-foreground">
          The export will include all drafted sections, the selected ER scenario, confirmed parameters, and linked evidence. Make sure you have run the ER Simulator and drafted the key sections before exporting.
        </p>
        <Button
          data-testid="button-export"
          onClick={exportDoc}
          disabled={exporting}
          className="gap-2 w-full"
        >
          {exporting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
          {exporting ? "Generating export..." : `Export as ${format.toUpperCase()}`}
        </Button>
      </div>

      <div className="p-4 bg-yellow-500/5 border border-yellow-500/15 rounded-lg">
        <p className="text-xs font-semibold text-yellow-400 mb-1.5">Before exporting</p>
        <ul className="text-xs text-muted-foreground space-y-1">
          <li>• ER Simulator — run a scenario and save it</li>
          <li>• Write/Draft — draft key sections (A.1, B.1, B.2 at minimum)</li>
          <li>• Parameters — confirm critical values (fNRB, SFC, NCV)</li>
          <li>• Audit — score ≥ 60 recommended before submission</li>
        </ul>
      </div>
    </div>
  );
}
