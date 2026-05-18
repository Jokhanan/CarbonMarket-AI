import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { PenLine, Wand2, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import type { Project } from "@/lib/api";

interface Section {
  section_id: string;
  section_title: string;
  content?: string;
  status?: "empty" | "drafted" | "revision";
  word_count?: number;
}

const STATUS_COLORS: Record<string, string> = {
  drafted: "bg-green-500/10 text-green-400 border-green-500/20",
  revision: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  empty: "bg-muted text-muted-foreground border-border",
};

export default function WriteDraftTab({ project }: { project: Project }) {
  const { toast } = useToast();
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [writing, setWriting] = useState<string | null>(null);
  const [writingAll, setWritingAll] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  const projectId = project.id;
  const docType = project.doc_type?.toUpperCase() ?? "PDD";

  const SECTIONS: Section[] = docType.includes("PDD") ? [
    { section_id: "A1", section_title: "A.1 — Project Title and Description" },
    { section_id: "A2", section_title: "A.2 — Project Activity" },
    { section_id: "A3", section_title: "A.3 — Project Boundaries" },
    { section_id: "B1", section_title: "B.1 — Baseline Scenario" },
    { section_id: "B2", section_title: "B.2 — Additionality" },
    { section_id: "B3", section_title: "B.3 — Emission Reduction Methodology" },
    { section_id: "C1", section_title: "C.1 — Monitoring Parameters" },
    { section_id: "C2", section_title: "C.2 — Monitoring Plan" },
    { section_id: "D1", section_title: "D.1 — Stakeholder Consultation" },
    { section_id: "E1", section_title: "E.1 — Environmental Impact" },
  ] : [
    { section_id: "1", section_title: "Section 1 — Project Description" },
    { section_id: "2", section_title: "Section 2 — Monitoring Results" },
    { section_id: "3", section_title: "Section 3 — ER Calculation" },
    { section_id: "4", section_title: "Section 4 — Quality Assurance" },
  ];

  async function draftSection(sectionId: string, sectionTitle: string) {
    setWriting(sectionId);
    try {
      const r = await fetch(`/api/projects/${projectId}/write`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ section_id: sectionId, section_title: sectionTitle }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      const content = data.content ?? data.draft ?? data.text ?? JSON.stringify(data);
      setDrafts((d) => ({ ...d, [sectionId]: content }));
      setExpanded(sectionId);
    } catch (e) {
      toast({ title: "Draft failed", description: String(e), variant: "destructive" });
    } finally {
      setWriting(null);
    }
  }

  async function draftAll() {
    setWritingAll(true);
    try {
      const r = await fetch(`/api/projects/${projectId}/write-all`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      const sections = data.sections ?? data.drafts ?? [];
      const newDrafts: Record<string, string> = {};
      for (const s of sections) {
        newDrafts[s.section_id ?? s.id] = s.content ?? s.draft ?? "";
      }
      setDrafts((d) => ({ ...d, ...newDrafts }));
      toast({ title: `${Object.keys(newDrafts).length} sections drafted` });
    } catch (e) {
      toast({ title: "Draft all failed", description: String(e), variant: "destructive" });
    } finally {
      setWritingAll(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-purple-500/10 flex items-center justify-center">
          <PenLine className="w-4 h-4 text-purple-400" />
        </div>
        <h2 className="text-base font-semibold">Write / Draft</h2>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {Object.keys(drafts).length}/{SECTIONS.length} sections drafted
          </span>
          <Button
            data-testid="button-draft-all"
            size="sm"
            onClick={draftAll}
            disabled={writingAll}
            className="gap-1.5 h-7 text-xs"
          >
            {writingAll ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Wand2 className="w-3.5 h-3.5" />}
            {writingAll ? "Drafting all..." : "Draft All"}
          </Button>
        </div>
      </div>

      <div className="bg-primary/5 border border-primary/15 rounded-lg px-3 py-2.5 text-xs text-muted-foreground">
        AI will use your project parameters, ER scenario, and uploaded documents as context for each section.
      </div>

      <div className="space-y-2">
        {SECTIONS.map((sec) => {
          const hasDraft = !!drafts[sec.section_id];
          const isExpanded = expanded === sec.section_id;
          const isWriting = writing === sec.section_id;

          return (
            <div
              key={sec.section_id}
              data-testid={`section-card-${sec.section_id}`}
              className={`border rounded-lg overflow-hidden ${hasDraft ? "border-primary/30" : "border-border/50"}`}
            >
              <div className="flex items-center justify-between px-4 py-3 bg-card">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs text-muted-foreground w-8">{sec.section_id}</span>
                  <span className="text-sm font-medium">{sec.section_title.split(" — ")[1] ?? sec.section_title}</span>
                  {hasDraft && (
                    <span className={`inline-flex px-1.5 py-0.5 rounded text-xs font-medium border ${STATUS_COLORS.drafted}`}>
                      drafted
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    data-testid={`button-draft-${sec.section_id}`}
                    size="sm"
                    variant={hasDraft ? "outline" : "default"}
                    onClick={() => draftSection(sec.section_id, sec.section_title)}
                    disabled={isWriting || writingAll}
                    className="gap-1.5 h-7 text-xs"
                  >
                    {isWriting
                      ? <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      : <Wand2 className="w-3.5 h-3.5" />}
                    {isWriting ? "Writing..." : hasDraft ? "Redraft" : "Draft"}
                  </Button>
                  {hasDraft && (
                    <button
                      data-testid={`button-expand-${sec.section_id}`}
                      onClick={() => setExpanded(isExpanded ? null : sec.section_id)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  )}
                </div>
              </div>
              {isExpanded && hasDraft && (
                <div className="border-t border-border/50 p-4 bg-background">
                  <Textarea
                    value={drafts[sec.section_id]}
                    onChange={(e) => setDrafts((d) => ({ ...d, [sec.section_id]: e.target.value }))}
                    rows={10}
                    className="bg-input border-border text-sm resize-none w-full font-mono leading-relaxed"
                    data-testid={`textarea-draft-${sec.section_id}`}
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    {drafts[sec.section_id].split(/\s+/).filter(Boolean).length} words
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
