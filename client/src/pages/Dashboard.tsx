import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import { FolderOpen, FileText, Activity, Plus, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { Project } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  active: "bg-primary/15 text-primary border-primary/20",
  draft: "bg-secondary text-muted-foreground border-border",
  registered: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  archived: "bg-orange-500/15 text-orange-400 border-orange-500/20",
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      data-testid={`badge-status-${status}`}
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${STATUS_COLORS[status] ?? "bg-secondary text-muted-foreground border-border"}`}
    >
      {status}
    </span>
  );
}

export default function Dashboard() {
  const { data: projects, isLoading } = useQuery<Project[]>({
    queryKey: ["/api/projects"],
  });

  const total = projects?.length ?? 0;
  const active = projects?.filter((p) => p.status === "active").length ?? 0;
  const drafts = projects?.filter((p) => p.status === "draft").length ?? 0;
  const totalDocs = projects?.reduce((s, p) => s + (p.doc_count ?? 0), 0) ?? 0;

  const metrics = [
    { label: "Total projets", value: total, icon: FolderOpen, color: "text-primary" },
    { label: "Actifs", value: active, icon: Activity, color: "text-green-400" },
    { label: "Brouillons", value: drafts, icon: FileText, color: "text-yellow-400" },
    { label: "Documents", value: totalDocs, icon: FileText, color: "text-blue-400" },
  ];

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">Vue d'ensemble de votre portefeuille carbone</p>
        </div>
        <Link href="/projects/new">
          <Button data-testid="button-new-project" className="gap-2">
            <Plus className="w-4 h-4" />
            New Project
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {metrics.map(({ label, value, icon: Icon, color }) => (
          <Card key={label} data-testid={`card-metric-${label}`} className="bg-card border-card-border">
            <CardContent className="pt-5 pb-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">{label}</p>
                  {isLoading ? (
                    <Skeleton className="h-8 w-12 mt-1" />
                  ) : (
                    <p className="text-3xl font-bold mt-1">{value}</p>
                  )}
                </div>
                <Icon className={`w-8 h-8 ${color} opacity-70`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="bg-card border-card-border">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold">Projets recents</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="px-6 py-4 space-y-3">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : !projects?.length ? (
            <div className="px-6 py-12 text-center text-muted-foreground text-sm">
              Aucun projet. Commencez par en creer un.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Nom</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Standard</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Methodologie</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Pays</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Statut</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Docs</th>
                  <th className="px-6 py-3" />
                </tr>
              </thead>
              <tbody>
                {projects.slice(0, 15).map((p) => (
                  <tr
                    key={p.id}
                    data-testid={`row-project-${p.id}`}
                    className="border-b border-border/50 hover:bg-accent/40 transition-colors"
                  >
                    <td className="px-6 py-3 font-medium max-w-[200px] truncate">{p.name}</td>
                    <td className="px-6 py-3 text-muted-foreground">{p.standard}</td>
                    <td className="px-6 py-3 text-muted-foreground">{p.methodology || "—"}</td>
                    <td className="px-6 py-3 text-muted-foreground">{p.country || "—"}</td>
                    <td className="px-6 py-3"><StatusBadge status={p.status} /></td>
                    <td className="px-6 py-3 text-muted-foreground">{p.doc_count ?? 0}</td>
                    <td className="px-6 py-3">
                      <Link
                        href={`/projects/${p.id}`}
                        className="text-primary hover:text-primary/80 flex items-center gap-1 text-xs"
                      >
                        Voir <ArrowRight className="w-3 h-3" />
                      </Link>
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
