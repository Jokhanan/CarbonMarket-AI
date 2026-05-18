export interface Project {
  id: number;
  name: string;
  standard: string;
  doc_type: string;
  methodology: string;
  country: string;
  description: string;
  status: string;
  doc_count: number;
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
  created_at: string;
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

export interface AIReviewResult {
  task_id?: string;
  status: string;
  sections?: AIReviewSection[];
  results?: AIReviewSection[];
  error?: string;
}

export async function uploadDocx(file: File): Promise<{ file_path: string; filename: string }> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch("/api/upload-document", { method: "POST", body: fd });
  if (!res.ok) throw new Error(`Upload failed: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function calculate(req: CalcRequest): Promise<CalcResult> {
  const res = await fetch("/api/v1/calculate", {
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

export const METHODOLOGY_LABELS = {
  RECH: "GS RECH v5",
  TPDDTEC: "TPDDTEC v4",
  VM0050: "VM0050 v1",
  MECD: "GS MECD v2",
} as const;

export type Methodology = keyof typeof METHODOLOGY_LABELS;
export const METHODOLOGIES: Methodology[] = ["RECH", "TPDDTEC", "VM0050", "MECD"];
