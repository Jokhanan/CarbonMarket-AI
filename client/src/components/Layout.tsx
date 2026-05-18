import { Link, useLocation } from "wouter";
import {
  LayoutDashboard,
  Calculator,
  FolderOpen,
  FileSearch,
  Sparkles,
  Leaf,
  Plus,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/calculator", label: "ER Calculator", icon: Calculator },
  { href: "/projects", label: "Projects", icon: FolderOpen },
  { href: "/analyze", label: "Analyze", icon: FileSearch },
  { href: "/review", label: "AI Review", icon: Sparkles },
] as const;

export default function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <aside className="w-56 shrink-0 flex flex-col bg-sidebar border-r border-sidebar-border">
        <div className="flex items-center gap-2 px-5 py-5 border-b border-sidebar-border">
          <Leaf className="w-5 h-5 text-primary" strokeWidth={2} />
          <span className="text-base font-semibold tracking-tight text-foreground">
            Carbon<span className="text-primary">GPT</span>
          </span>
        </div>

        <div className="px-3 pt-3 pb-1">
          <Link href="/projects/new">
            <button
              data-testid="nav-new-project"
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Project
            </button>
          </Link>
        </div>

        <nav className="flex-1 px-3 py-2 space-y-0.5">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? location === "/" : location.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                data-testid={`nav-${label.toLowerCase().replace(/\s+/g, "-")}`}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  active
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent"
                )}
              >
                <Icon className="w-4 h-4 shrink-0" />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="px-5 py-4 border-t border-sidebar-border">
          <p className="text-xs text-muted-foreground">Carbon OS v2.0</p>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
