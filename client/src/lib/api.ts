export interface Project {
  id: number;
  name: string;
  standard: string;
  doc_type: string;
  methodology: string;
  country: string;
  description: string;
  status: string;
  doc_count?: number;
  crediting_period_years?: number;
  crediting_period_start?: number;
  methodology_settings?: Record<string, unknown>;
  project_intake?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ProjectDocument {
  id: number;
  project_id: number;
  filename: string;
  original_filename: string;
  doc_type: string;
  file_path: string;
  use_as_ai_context: boolean;
  ingestion_status?: string;
  created_at: string;
}

export interface Parameter {
  id: number;
  param_key: string;
  param_name: string;
  value: number | string | null;
  unit?: string;
  source_type: string;
  tier?: string;
  confirmed: boolean;
  description?: string;
  section?: string;
  group?: string;
}

export interface ParameterSummary {
  total: number;
  confirmed: number;
  pending: number;
  defaulted: number;
  coverage_pct: number;
}

export interface ERScenario {
  id: number;
  project_id: number;
  scenario_name: string;
  purpose?: string;
  is_selected: boolean;
  summary?: {
    total_er: number;
    average_annual_er: number;
    crediting_years: number;
    deployment_mode?: string;
  };
  created_at: string;
}

export interface ERYear {
  year_number: number;
  calendar_year: number;
  net_er: number;
  gross_er?: number;
  baseline_emissions: number;
  project_emissions: number;
  leakage?: number;
  active_devices?: number;
}

export interface ERResult {
  summary: {
    total_er: number;
    average_annual_er: number;
    crediting_years: number;
    deployment_mode?: string;
  };
  years: ERYear[];
  year_by_year?: ERYear[];
  warnings?: string[];
  calculation_steps?: Record<string, unknown>[];
  parameters_used?: Record<string, unknown>;
}

export interface AuditResult {
  overall_score: number;
  risk_level: string;
  summary: string;
  counts: { critical: number; high: number; medium: number; low: number };
  findings: Array<{
    type: string;
    title: string;
    severity: string;
    description: string;
    category: string;
  }>;
  parameter_issues: Array<{ param_key: string; message: string; status: string }>;
  evidence_gaps: Array<{ param_name: string; param_key: string; source_type: string }>;
  recommendations: string[];
}

export interface Lifecycle {
  current_stage: string;
  stages: Array<{
    key: string;
    name: string;
    status: string;
    tasks_total: number;
    tasks_completed: number;
  }>;
}

export interface LifecycleTask {
  id: number;
  title: string;
  stage: string;
  status: string;
  priority: string;
  due_date?: string;
  notes?: string;
}

export interface MonitoringPeriod {
  id: number;
  project_id: number;
  period_number: number;
  period_start: string;
  period_end: string;
  status: string;
  notes?: string;
}

export interface Issuance {
  id: number;
  project_id: number;
  vintage_year: number;
  credits_issued: number;
  status: string;
  registry_serial?: string;
  issuance_date?: string;
}

export interface CalcYear {
  year_number: number;
  calendar_year: number;
  net_er: number;
  gross_er?: number;
  baseline_emissions: number;
  project_emissions: number;
  leakage?: number;
  active_devices?: number;
  adoption_rate?: number;
}

export interface CalcSummary {
  total_er: number;
  average_annual_er: number;
  crediting_years: number;
  deployment_mode?: string;
  total_leakage?: number;
}

export interface CalcResult {
  summary: CalcSummary;
  years: CalcYear[];
  year_by_year?: CalcYear[];
  warnings: string[];
  calculation_steps?: Record<string, unknown>[];
  parameters_used?: Record<string, unknown>;
  methodology?: string;
}

export interface CalcRequest {
  methodology: string;
  params: Record<string, unknown>;
  crediting_years: number;
  start_year: number;
}

export interface AIReviewResult {
  task_id?: string;
  status: string;
  sections?: Array<{ section: string; findings: { level: string; message: string }[]; score?: number }>;
  error?: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  action?: string;
  navigate_to?: string;
}

export interface MethodologyInfo {
  code: string;
  name: string;
  standard: string;
  category?: string;
  description?: string;
}

export interface AnalyzeRequest {
  file_path: string;
  standard: string;
  doc_type: string;
  version?: string;
}

export interface Finding {
  level: "ERROR" | "WARNING" | "INFO";
  code: string;
  message: string;
  section?: string;
}

export interface AnalyzeResult {
  score: number;
  findings: Finding[];
  summary?: string;
}

export interface AIReviewRequest {
  standard: string;
  doc_type: string;
  file_path: string;
  user_doc_path?: string;
  version?: string;
}

export interface AIReviewSection {
  section: string;
  findings: { level: string; message: string }[];
  score?: number;
}

export const METHODOLOGY_LABELS: Record<string, string> = {
  RECH: "GS RECH v5",
  TPDDTEC: "TPDDTEC v4",
  VM0050: "VM0050 v1",
  MECD: "GS MECD v2",
  "ACM0002": "ACM0002",
  "AMS-I.D.": "AMS-I.D.",
  "GS-MECD": "GS-MECD",
};

export type Methodology = string;
export const METHODOLOGIES: Methodology[] = ["RECH", "TPDDTEC", "VM0050", "MECD"];

export async function uploadDocx(file: File): Promise<{ file_path: string; filename: string }> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch("/api/upload-document", { method: "POST", body: fd });
  if (!res.ok) throw new Error(`Upload failed: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function calculate(req: CalcRequest): Promise<CalcResult> {
  const res = await fetch("/api/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Calculation failed: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function analyzeSelected(req: AnalyzeRequest): Promise<AnalyzeResult> {
  const res = await fetch("/api/analyze-selected", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Analysis failed: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function startAIReview(req: AIReviewRequest): Promise<{ task_id: string }> {
  const res = await fetch("/api/ai-review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`AI Review start failed: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function pollAIReview(taskId: string): Promise<AIReviewResult> {
  const res = await fetch(`/api/ai-review/${taskId}`);
  if (!res.ok) throw new Error(`Poll failed: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function uploadProjectDocument(
  projectId: number,
  file: File,
  docType: string
): Promise<{ id: number; message: string }> {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("doc_type", docType);
  const res = await fetch(`/api/projects/${projectId}/documents`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(`Upload failed: ${res.status} ${await res.text()}`);
  return res.json();
}

export const STANDARD_OPTIONS = ["GoldStandard", "Verra", "CDM", "ART-TREES", "GCC"];

export const METHODOLOGY_GROUPS: Record<string, string[]> = {
  "Clean Cooking": ["TPDDTEC", "VM0050", "GS-MECD", "AMS-I.E."],
  "Renewable Energy": ["ACM0002", "AMS-I.D.", "VM0042"],
  "Other": ["GS RECH v5"],
};

export const ALL_METHODOLOGIES = Object.values(METHODOLOGY_GROUPS).flat();
