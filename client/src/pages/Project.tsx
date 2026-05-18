import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRoute, Link } from "wouter";
import {
  ArrowLeft, Settings, FileText, Sliders, TrendingUp,
  PenLine, Search, ShieldCheck, MessageSquare, Clock,
  Activity, Download,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import type { Project } from "@/lib/api";
import SetupTab from "@/components/workspace/SetupTab";
import DocumentsTab from "@/components/workspace/DocumentsTab";
import ParametersTab from "@/components/workspace/ParametersTab";
import ERSimulatorTab from "@/components/workspace/ERSimulatorTab";
import WriteDraftTab from "@/components/workspace/WriteDraftTab";
import ReviewTab from "@/components/workspace/ReviewTab";
import AuditTab from "@/components/workspace/AuditTab";
import FindingsTab from "@/components/workspace/FindingsTab";
import LifecycleTab from "@/components/workspace/LifecycleTab";
import MonitoringTab from "@/components/workspace/MonitoringTab";
import ExportTab from "@/components/workspace/ExportTab";

const TABS = [
  { id: "setup",      label: "Setup",       icon: Settings },
  { id: "documents",  label: "Documents",   icon: FileText },
  { id: "parameters", label: "Parameters",  icon: Sliders },
  { id: "er",         label: "ER Simulator",icon: TrendingUp },
  { id: "write",      label: "Write",       icon: PenLine },
  { id: "review",     label: "Review",      icon: Search },
  { id: "audit",      label: "Audit",       icon: ShieldCheck },
  { id: "findings",   label: "Findings",    icon: MessageSquare },
  { id: "lifecycle",  label: "Lifecycle",   icon: Clock },
  { id: "monitoring", label: "Monitoring",  icon: Activity },
  { id: "export",     label: "Export",      icon: Download },
] as const;

type TabId = typeof TABS[number]["id"];

const STANDARD_BADGE: Record<string, string> = {
  GoldStandard: "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20",
  Verra: "bg-blue-500/10 text-blue-400 border border-blue-500/20",
  CDM: "bg-purple-500/10 text-purple-400 border border-purple-500/20",
};

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-500/10 text-green-400 border-green-500/20",
  draft: "bg-secondary text-muted-foreground border-border",
  registered: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  archived: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  review: "bg-purple-500/10 text-purple-400 border-purple-500/20",
};

export default function ProjectPage() {
  const [, params] = useRoute("/projects/:id");
  const projectId = parseInt(params?.id ?? "0");
  const [activeTab, setActiveTab] = useState<TabId>("setup");

  const { data: project, isLoading } = useQuery<Project>({
    queryKey: ["/api/projects", projectId],
    queryFn: async () => {
      const r = await fetch(`/api/projects/${projectId}`);
      if (!r.ok) throw new Error("Project not found");
      return r.json();
    },
    enabled: !!projectId,
  });

  if (isLoading) {
    return (
      <div className="p-8 space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Project not found.{" "}
        <Link href="/projects" className="text-primary hover:underline">Back to projects</Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-0 h-full">
      {/* ── Breadcrumb ── */}
      <div className="flex items-center gap-2 px-6 pt-5 pb-3 text-xs text-muted-foreground border-b border-border/50">
        <Link href="/projects" className="hover:text-foreground flex items-center gap-1 transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" />
          Projects
        </Link>
        <span>/</span>
        <span className="text-foreground font-medium truncate max-w-[200px]">{project.name}</span>
      </div>

      {/* ── Project Header ── */}
      <div className="px-6 py-4 border-b border-border/50 bg-card/30">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1.5">
              {project.standard && (
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${STANDARD_BADGE[project.standard] ?? "bg-secondary text-muted-foreground border border-border"}`}>
                  {project.standard}
                </span>
              )}
              {project.doc_type && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary/10 text-primary border border-primary/20">
                  {project.doc_type}
                </span>
              )}
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${STATUS_COLORS[project.status] ?? "bg-secondary text-muted-foreground border-border"}`}>
                {project.status}
              </span>
            </div>
            <h1 className="text-xl font-bold tracking-tight truncate">{project.name}</h1>
            <div className="flex items-center gap-1.5 mt-1 text-xs text-muted-foreground flex-wrap">
              {project.methodology && <span>{project.methodology}</span>}
              {project.methodology && project.country && <span>·</span>}
              {project.country && <span>{project.country}</span>}
              {project.crediting_period_years && (
                <>
                  <span>·</span>
                  <span>{project.crediting_period_years} yr crediting period</span>
                </>
              )}
            </div>
          </div>
          {project.crediting_period_start && (
            <div className="shrink-0 text-right">
              <div className="text-lg font-bold text-primary">{project.crediting_period_start}</div>
              <div className="text-xs text-muted-foreground">Start Year</div>
            </div>
          )}
        </div>
      </div>

      {/* ── Tab Bar ── */}
      <div className="border-b border-border/50 overflow-x-auto shrink-0">
        <div className="flex px-2 min-w-max">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                data-testid={`tab-${tab.id}`}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-3 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
                  active
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Tab Content ── */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === "setup"      && <SetupTab project={project} />}
        {activeTab === "documents"  && <DocumentsTab projectId={projectId} />}
        {activeTab === "parameters" && <ParametersTab projectId={projectId} />}
        {activeTab === "er"         && <ERSimulatorTab project={project} />}
        {activeTab === "write"      && <WriteDraftTab project={project} />}
        {activeTab === "review"     && <ReviewTab project={project} />}
        {activeTab === "audit"      && <AuditTab projectId={projectId} />}
        {activeTab === "findings"   && <FindingsTab projectId={projectId} />}
        {activeTab === "lifecycle"  && <LifecycleTab projectId={projectId} />}
        {activeTab === "monitoring" && <MonitoringTab projectId={projectId} />}
        {activeTab === "export"     && <ExportTab project={project} />}
      </div>
    </div>
  );
}
