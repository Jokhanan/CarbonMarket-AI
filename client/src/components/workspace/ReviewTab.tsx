import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, RefreshCw, CheckCircle, AlertTriangle, XCircle, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import type { ProjectDocument, Project } from "@/lib/api";

interface ReviewSection {
  section_id: string;
  section_title: string;
  completeness_score: number;
  issues: string[];
  suggested_fixes: string[];
  questions_for_user: string[];
}

interface ReviewResult {
  overall_score: number;
  overall_risk: string;
  top_issues: string[];
  top_actions: string[];
  per_section_reviews: ReviewSection[];
  compliance_alerts: Array<{ severity: string; title: string; description: string }>;
}

const SCORE_COLOR = (s: number) =>
  s >= 80 ? "text-green-400" : s >= 50 ? "text-yellow-400" : "text-red-400";

const RISK_COLORS: Record<string, string> = {
  LOW: "text-green-400 bg-green-400/10 border-green-400/20",
  MEDIUM: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20",
  HIGH: "text-red-400 bg-red-400/10 border-red-400/20",
};

export default function ReviewTab({ project }: { project: Project }) {
  const { toast } = useToast();
  const projectId = project.id;
  const [result, setResult] = useState<ReviewResult | null>(null);
  const [running, setRunning] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [expanded, setExpanded] = useState<string | null>(null);

  const { data: docs } = useQuery<ProjectDocument[]>({
    queryKey: ["/api/projects", projectId, "documents"],
    queryFn: async () => {
      const r = await fetch(`/api/projects/${projectId}/documents`);
      if (!r.ok) throw new Error("Failed");
      const d = await r.json();
      return Array.isArray(d) ? d : (d.documents ?? []);
    },
  });

  async function runReview() {
    setRunning(true);
    try {
      const url = selectedDocId
        ? `/api/projects/${projectId}/review/${selectedDocId}`
        : `/api/projects/${projectId}/review-draft`;
      const r = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setResult(data);
    } catch (e) {
      toast({ title: "Review failed", description: String(e), variant: "destructive" });
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
          <Search className="w-4 h-4 text-blue-400" />
        </div>
        <h2 className="text-base font-semibold">AI Review</h2>
      </div>

      <div className="flex items-end gap-3 p-4 bg-card border border-border/50 rounded-lg">
        <div className="space-y-1.5 flex-1">
          <Label className="text-xs text-muted-foreground">Document to review (optional)</Label>
          <Select value={selectedDocId} onValueChange={setSelectedDocId}>
            <SelectTrigger className="bg-input border-border h-8 text-sm">
              <SelectValue placeholder="Review AI draft (no document selected)" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Review AI draft</SelectItem>
              {(docs ?? []).map((d) => (
                <SelectItem key={d.id} value={String(d.id)}>
                  {d.original_filename || d.filename}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button
          data-testid="button-run-review"
          onClick={runReview}
          disabled={running}
          className="gap-2 shrink-0"
        >
          {running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          {running ? "Reviewing..." : "Run Review"}
        </Button>
      </div>

      {result && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-card border border-border/50 rounded-lg p-4 text-center">
              <div className={`text-3xl font-bold ${SCORE_COLOR(result.overall_score)}`}>
                {result.overall_score}/100
              </div>
              <div className="text-xs text-muted-foreground mt-1">Overall Score</div>
            </div>
            <div className="bg-card border border-border/50 rounded-lg p-4 text-center">
              <div className={`text-lg font-bold inline-flex items-center px-3 py-1 rounded border ${RISK_COLORS[result.overall_risk] ?? "text-muted-foreground"}`}>
                {result.overall_risk ?? "—"}
              </div>
              <div className="text-xs text-muted-foreground mt-2">Risk Level</div>
            </div>
          </div>

          {result.top_issues?.length > 0 && (
            <div className="p-4 bg-red-500/5 border border-red-500/15 rounded-lg">
              <p className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-2">Top Issues</p>
              <ul className="space-y-1">
                {result.top_issues.map((issue, i) => (
                  <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                    <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.top_actions?.length > 0 && (
            <div className="p-4 bg-primary/5 border border-primary/15 rounded-lg">
              <p className="text-xs font-semibold text-primary uppercase tracking-wider mb-2">Priority Actions</p>
              <ul className="space-y-1">
                {result.top_actions.map((action, i) => (
                  <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.per_section_reviews?.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Section Reviews</p>
              {result.per_section_reviews.map((sec) => {
                const isOpen = expanded === sec.section_id;
                const label = sec.completeness_score >= 80 ? "PASS" : sec.completeness_score >= 50 ? "REVIEW" : "FAIL";
                return (
                  <div key={sec.section_id} className="border border-border/50 rounded-lg overflow-hidden">
                    <button
                      data-testid={`review-section-${sec.section_id}`}
                      className="w-full flex items-center justify-between px-4 py-3 bg-card hover:bg-accent/20 transition-colors text-left"
                      onClick={() => setExpanded(isOpen ? null : sec.section_id)}
                    >
                      <div className="flex items-center gap-3">
                        <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${SCORE_COLOR(sec.completeness_score)}`}>
                          [{label}]
                        </span>
                        <span className="text-sm font-medium">{sec.section_id}: {sec.section_title}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-bold ${SCORE_COLOR(sec.completeness_score)}`}>
                          {sec.completeness_score}/100
                        </span>
                        {isOpen ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
                      </div>
                    </button>
                    {isOpen && (
                      <div className="px-4 py-3 border-t border-border/50 space-y-3 bg-background">
                        {sec.issues?.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-red-400 mb-1.5">Issues</p>
                            {sec.issues.map((iss, i) => <p key={i} className="text-xs text-muted-foreground">• {iss}</p>)}
                          </div>
                        )}
                        {sec.suggested_fixes?.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-primary mb-1.5">Suggested Fixes</p>
                            {sec.suggested_fixes.map((fix, i) => <p key={i} className="text-xs text-muted-foreground">• {fix}</p>)}
                          </div>
                        )}
                        {sec.questions_for_user?.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-yellow-400 mb-1.5">Questions</p>
                            {sec.questions_for_user.map((q, i) => <p key={i} className="text-xs text-muted-foreground">• {q}</p>)}
                          </div>
                        )}
                        {!sec.issues?.length && !sec.suggested_fixes?.length && !sec.questions_for_user?.length && (
                          <p className="text-xs text-muted-foreground">No issues found for this section.</p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
