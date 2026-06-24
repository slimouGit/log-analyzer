export type Severity = "low" | "medium" | "high" | "critical";

export type IncidentType =
  | "application_error"
  | "database_error"
  | "network_error"
  | "configuration_error"
  | "performance_issue"
  | "security_related"
  | "unknown";

export interface LogInput {
  title: string;
  raw_log: string;
  language: string;
  source: string;
}

export interface LogAnalysis {
  incident_type: IncidentType;
  severity: Severity;
  affected_component: string;
  short_summary: string;
  probable_root_cause: string;
  important_log_lines: string[];
  recommended_debug_steps: string[];
  possible_fix_direction: string;
  test_cases: string[];
  confidence: number;
}

export interface LogAnalysisResponse {
  analysis_id: number;
  analysis: LogAnalysis;
}

export interface StoredLogAnalysis {
  id: number;
  title: string;
  raw_log: string;
  language: string;
  source: string;
  analysis: LogAnalysis;
  created_at: string;
}
