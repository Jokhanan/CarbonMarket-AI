import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import Calculator from "@/pages/Calculator";
import Projects from "@/pages/Projects";
import Project from "@/pages/Project";
import NewProject from "@/pages/NewProject";
import Analyze from "@/pages/Analyze";
import AIReview from "@/pages/AIReview";
import NotFound from "@/pages/not-found";
import Copilot from "@/components/Copilot";

function Router() {
  return (
    <Layout>
      <Switch>
        <Route path="/" component={Dashboard} />
        <Route path="/calculator" component={Calculator} />
        <Route path="/projects" component={Projects} />
        <Route path="/projects/new" component={NewProject} />
        <Route path="/projects/:id" component={Project} />
        <Route path="/analyze" component={Analyze} />
        <Route path="/review" component={AIReview} />
        <Route component={NotFound} />
      </Switch>
      <Copilot />
    </Layout>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}
