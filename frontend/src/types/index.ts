export type SeverityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFORMATIONAL';

export type ControlStatus = 
  | 'IMPLEMENTED_WITH_EVIDENCE'
  | 'PARTIALLY_IMPLEMENTED'
  | 'MISSING_WITH_EVIDENCE'
  | 'NOT_EVIDENCED'
  | 'NOT_APPLICABLE';

export interface Evidence {
  id: string;
  file_path: string;
  line_start?: number;
  line_end?: number;
  code_snippet?: string;
  context_note?: string;
  is_redacted: boolean;
}

export interface Finding {
  id: string;
  assessment_id: string;
  finding_id: string;
  title: string;
  description: string;
  category: string;
  severity: SeverityLevel;
  numerical_score: number;
  confidence: string;
  validation_status: string;
  owasp_id?: string;
  remediation?: string;
  remediation_snippet?: string;
  created_at: string;
  evidences: Evidence[];
}

export interface ControlMapping {
  id: string;
  assessment_id: string;
  framework_id: string;
  control_id: string;
  control_title: string;
  control_category?: string;
  status: ControlStatus;
  evidence_summary?: string;
  rationale?: string;
  source_url?: string;
  is_conceptual: boolean;
}

export interface SupervisorDecision {
  next_agent: string;
  reason: string;
  needs_extra_security_check: boolean;
  source?: string;
  iteration?: number;
}

export interface AgentExecutionRecord {
  agent_name: string;
  started_at: string;
  completed_at: string;
  duration_seconds: number;
  supervisor_decision: SupervisorDecision;
  output_summary: string;
}

export interface AssessmentSummary {
  id: string;
  project_name: string;
  description?: string;
  status: 'PENDING' | 'SCANNING' | 'ANALYZING' | 'COMPLETED' | 'FAILED';
  overall_risk_score: number;
  risk_level: SeverityLevel;
  compliance_score: number;
  target_frameworks: string[];
  findings_count: number;
  severity_breakdown: Record<string, number>;
  compliance_breakdown: Record<string, number>;
  agent_execution_log?: AgentExecutionRecord[];
  supervisor_iterations?: number;
  created_at: string;
  completed_at?: string;
}

export interface AssessmentDetail extends AssessmentSummary {
  recon_summary: {
    components?: string[];
    models_detected?: string[];
    vector_stores?: string[];
    tools_detected?: string[];
    trust_boundaries?: string[];
    documented_controls?: string[];
    unverified_claims?: string[];
    narrative_overview?: string;
  };
  findings: Finding[];
  control_mappings: ControlMapping[];
}

export interface FrameworkControl {
  control_id: string;
  title: string;
  category: string;
  description: string;
  reference_url?: string;
  verification_guidance?: string;
  is_conceptual_mapping: boolean;
}

export interface Framework {
  id: string;
  name: string;
  version: string;
  publisher: string;
  category: string;
  controls_count: number;
  source_url: string;
  disclaimer: string;
  controls: FrameworkControl[];
}

export interface HealthStatus {
  status: string;
  version: string;
  timestamp: string;
  database: string;
  engine: string;
}
