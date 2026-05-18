import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import { FolderOpen, ArrowRight, Plus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { Project } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  active: "bg-primary/15 text-primary border-primary/20",
  draft: "bg-secondary text-muted-foreground border-border",
  registered: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  archived: "bg-orange-500/15 text-orange-400 border-orange-500/20",
};

export default function Projects() {
  const { data: projects, isLoading } = useQuery<Project[]>({
    queryKey: ["/api/projects"],
  });

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FolderOpen className="w-6 h-6 text-primary" />
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Projets</h1>
            <p className="text-sm text-muted-foreground mt-0.5">{projects?.length ?? 0} projets</p>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}
        </div>
      ) : !projects?.length ? (
        <Card className="bg-card border-card-border">
          <CardContent className="py-16 text-center text-muted-foreground text-sm">
            Aucun projet. Utilisez le formulaire Streamlit ou l'API pour creer des projets.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {projects.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`}>
              <a
                data-testid={`card-project-${p.id}`}
                className="flex items-center justify-between px-5 py-4 bg-card border border-card-border rounded-lg hover:border-primary/30 hover:bg-accent/30 transition-all cursor-pointer"
              >
                <div className="flex items-center gap-4 min-w-0">
                  <FolderOpen className="w-5 h-5 text-muted-foreground shrink-0" />
                  <div className="min-w-0">
                    <p className="font-medium text-sm truncate">{p.name}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {p.standard} · {p.methodology || "—"} · {p.country || "—"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4 shrink-0">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${STATUS_COLORS[p.status] ?? "bg-secondary text-muted-foreground border-border"}`}>
                    {p.status}
                  </span>
                  <span className="text-xs text-muted-foreground">{p.doc_count ?? 0} docs</span>
                  <ArrowRight className="w-4 h-4 text-muted-foreground" />
                </div>
              </a>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
