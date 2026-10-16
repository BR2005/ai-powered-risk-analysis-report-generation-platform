import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Download, 
  FileCode, 
  Layers, 
  ShieldAlert, 
  Wrench, 
  CheckCircle2, 
  FileText, 
  ExternalLink,
  Code
} from 'lucide-react';
import { getAssessment, getReportPdfUrl } from '../api/client';
import type { AssessmentDetail, Finding } from '../types';
import { SeverityBadge } from '../components/SeverityBadge';
import { ControlStatusBadge } from '../components/ControlStatusBadge';
import { RiskScoreGauge } from '../components/RiskScoreGauge';
import { PipelineTimeline } from '../components/PipelineTimeline';
import { EvidenceViewerModal } from '../components/EvidenceViewerModal';

export const AssessmentDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'findings' | 'compliance' | 'remediation' | 'architecture'>('findings');
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);

  useEffect(() => {
    if (id) {
      getAssessment(id)
        .then(setAssessment)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-mono text-slate-400">Loading Assessment Artifacts...</p>
        </div>
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="p-12 text-center space-y-4">
        <h2 className="text-lg font-bold text-white">Assessment Not Found</h2>
        <p className="text-sm text-slate-400">The requested assessment ID does not exist.</p>
        <Link to="/" className="text-cyan-400 hover:underline text-sm font-medium">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const recon = assessment.recon_summary || {};
  const findings = assessment.findings || [];
  const controlMappings = assessment.control_mappings || [];

  return (
    <div className="space-y-6 animate-fadeIn pb-16">
      {/* Back button & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/assessments"
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl font-bold text-white">{assessment.project_name}</h1>
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                {assessment.id.slice(0, 8)}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Completed on {new Date(assessment.created_at).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Download Buttons */}
        <div className="flex items-center gap-2.5">
          <a
            href={getReportPdfUrl(assessment.id)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-xs font-semibold shadow-sm transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Export Audit PDF</span>
          </a>
          <Link
            to={`/reports?assessment_id=${assessment.id}`}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 text-xs font-semibold transition-all"
          >
            <FileText className="w-4 h-4" />
            <span>JSON Report</span>
          </Link>
        </div>
      </div>

      {/* Pipeline Status Banner */}
      <div className="glass-panel rounded-2xl p-4 border border-slate-800">
        <PipelineTimeline currentStatus={assessment.status} />
      </div>

      {/* Executive Summary Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Score Card */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex flex-col items-center justify-center text-center">
          <span className="text-xs uppercase font-mono tracking-wider font-semibold text-slate-400 mb-3">
            Authoritative Risk Score
          </span>
          <RiskScoreGauge score={assessment.overall_risk_score} level={assessment.risk_level} size={150} />
          <div className="mt-3 flex items-center gap-2">
            <SeverityBadge severity={assessment.risk_level} size="sm" />
            <span className="text-xs text-slate-400">Deterministic calculation</span>
          </div>
        </div>

        {/* Severity Metrics Breakdown */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Vulnerabilities by Severity
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Static AST & signature detections</p>
          </div>

          <div className="grid grid-cols-2 gap-3 my-3">
            <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-900/40">
              <span className="text-xs text-rose-400 font-mono uppercase font-semibold">Critical</span>
              <div className="text-2xl font-bold font-mono text-rose-300">
                {assessment.severity_breakdown?.CRITICAL || 0}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-orange-950/20 border border-orange-900/40">
              <span className="text-xs text-orange-400 font-mono uppercase font-semibold">High</span>
              <div className="text-2xl font-bold font-mono text-orange-300">
                {assessment.severity_breakdown?.HIGH || 0}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-900/40">
              <span className="text-xs text-amber-400 font-mono uppercase font-semibold">Medium</span>
              <div className="text-2xl font-bold font-mono text-amber-300">
                {assessment.severity_breakdown?.MEDIUM || 0}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-blue-950/20 border border-blue-900/40">
              <span className="text-xs text-blue-400 font-mono uppercase font-semibold">Low</span>
              <div className="text-2xl font-bold font-mono text-blue-300">
                {assessment.severity_breakdown?.LOW || 0}
              </div>
            </div>
          </div>

          <div className="text-xs text-slate-400">
            Total of <b className="text-white">{assessment.findings_count} findings</b> identified.
          </div>
        </div>

        {/* Compliance Posture Card */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Compliance Coverage
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Across target security frameworks</p>
          </div>

          <div className="my-2">
            <div className="flex items-baseline justify-between mb-1.5">
              <span className="text-3xl font-extrabold text-emerald-400 font-mono">
                {assessment.compliance_score.toFixed(1)}%
              </span>
              <span className="text-xs text-slate-400">
                {assessment.target_frameworks.length} Frameworks Active
              </span>
            </div>
            {/* Progress bar */}
            <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden border border-slate-800">
              <div
                className="bg-gradient-to-r from-emerald-500 to-cyan-500 h-full rounded-full transition-all duration-1000"
                style={{ width: `${assessment.compliance_score}%` }}
              />
            </div>
          </div>

          <div className="space-y-1 text-xs text-slate-400">
            <div className="flex items-center justify-between">
              <span>Missing Controls with Evidence:</span>
              <span className="text-rose-400 font-bold font-mono">
                {assessment.compliance_breakdown?.MISSING_WITH_EVIDENCE || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Partially Implemented:</span>
              <span className="text-amber-400 font-bold font-mono">
                {assessment.compliance_breakdown?.PARTIALLY_IMPLEMENTED || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Controls with Verified Evidence:</span>
              <span className="text-emerald-400 font-bold font-mono">
                {assessment.compliance_breakdown?.IMPLEMENTED_WITH_EVIDENCE || 0}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-slate-800 flex items-center gap-6">
        <button
          onClick={() => setActiveTab('findings')}
          className={`pb-3 text-sm font-semibold transition-all flex items-center gap-2 border-b-2 cursor-pointer ${
            activeTab === 'findings'
              ? 'border-cyan-400 text-cyan-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Security Findings ({findings.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('compliance')}
          className={`pb-3 text-sm font-semibold transition-all flex items-center gap-2 border-b-2 cursor-pointer ${
            activeTab === 'compliance'
              ? 'border-cyan-400 text-cyan-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Framework Matrix ({controlMappings.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('remediation')}
          className={`pb-3 text-sm font-semibold transition-all flex items-center gap-2 border-b-2 cursor-pointer ${
            activeTab === 'remediation'
              ? 'border-cyan-400 text-cyan-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Wrench className="w-4 h-4" />
          <span>Remediation Roadmap</span>
        </button>

        <button
          onClick={() => setActiveTab('architecture')}
          className={`pb-3 text-sm font-semibold transition-all flex items-center gap-2 border-b-2 cursor-pointer ${
            activeTab === 'architecture'
              ? 'border-cyan-400 text-cyan-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Code className="w-4 h-4" />
          <span>Recon & Boundaries</span>
        </button>
      </div>

      {/* Tab 1: Findings List */}
      {activeTab === 'findings' && (
        <div className="space-y-4">
          {findings.length === 0 ? (
            <div className="glass-panel rounded-2xl p-12 text-center text-slate-400 border border-slate-800">
              <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
              <h3 className="text-base font-bold text-white">No Security Vulnerabilities Detected</h3>
              <p className="text-xs text-slate-500 mt-1">
                Static scans did not trigger any detectable GenAI insecure patterns in evaluated files.
              </p>
            </div>
          ) : (
            findings.map((f) => (
              <div
                key={f.id}
                className="glass-panel glass-panel-hover rounded-2xl p-5 border border-slate-800 space-y-3 cursor-pointer"
                onClick={() => setSelectedFinding(f)}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <SeverityBadge severity={f.severity} size="sm" />
                    <span className="font-mono text-xs text-slate-400">{f.finding_id}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/40 font-mono">
                      {f.owasp_id || f.category}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-slate-400 font-semibold">
                    CVSS Score: {f.numerical_score} / 10.0
                  </span>
                </div>

                <div>
                  <h3 className="text-base font-bold text-white">{f.title}</h3>
                  <p className="text-xs text-slate-300 mt-1 line-clamp-2 leading-relaxed">
                    {f.description}
                  </p>
                </div>

                {f.evidences?.[0] && (
                  <div className="flex items-center justify-between text-xs font-mono text-slate-400 bg-slate-950/70 px-3 py-2 rounded-lg border border-slate-800">
                    <div className="flex items-center gap-2 truncate text-cyan-400">
                      <FileCode className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate">{f.evidences[0].file_path}</span>
                      {f.evidences[0].line_start && (
                        <span className="text-slate-500">:L{f.evidences[0].line_start}</span>
                      )}
                    </div>
                    <span className="text-[11px] text-cyan-400 font-medium hover:underline shrink-0">
                      Inspect Evidence →
                    </span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab 2: Compliance Matrix */}
      {activeTab === 'compliance' && (
        <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/50 text-xs font-mono uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-6 py-3 font-semibold">Framework</th>
                  <th className="px-6 py-3 font-semibold">Control ID</th>
                  <th className="px-6 py-3 font-semibold">Title</th>
                  <th className="px-6 py-3 font-semibold">Status</th>
                  <th className="px-6 py-3 font-semibold">Mapping Evidence & Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {controlMappings.map((cm) => (
                  <tr key={cm.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="px-6 py-3.5 font-mono text-xs font-bold text-cyan-400">
                      {cm.framework_id}
                    </td>
                    <td className="px-6 py-3.5 font-mono text-xs text-white">
                      {cm.control_id}
                      {cm.is_conceptual && (
                        <span className="block text-[10px] text-slate-500 font-sans">Conceptual</span>
                      )}
                    </td>
                    <td className="px-6 py-3.5 text-xs text-slate-200 max-w-xs">
                      <div className="font-semibold">{cm.control_title}</div>
                      {cm.control_category && (
                        <span className="text-[10px] text-slate-500">{cm.control_category}</span>
                      )}
                    </td>
                    <td className="px-6 py-3.5">
                      <ControlStatusBadge status={cm.status} size="sm" />
                    </td>
                    <td className="px-6 py-3.5 text-xs text-slate-300 max-w-md">
                      <p className="leading-relaxed">{cm.evidence_summary || cm.rationale}</p>
                      {cm.source_url && (
                        <a
                          href={cm.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] text-cyan-400 hover:underline mt-1"
                        >
                          <span>Official Reference</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Remediation Roadmap */}
      {activeTab === 'remediation' && (
        <div className="space-y-4">
          {findings.map((f, idx) => (
            <div key={f.id} className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60 flex items-center justify-center font-mono text-xs font-bold">
                    {idx + 1}
                  </span>
                  <h3 className="text-sm font-bold text-white">{f.title}</h3>
                </div>
                <SeverityBadge severity={f.severity} size="sm" />
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {f.remediation || 'Apply defensive guardrails and validate all untrusted inputs.'}
              </p>

              {f.remediation_snippet && (
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-emerald-400 overflow-x-auto leading-relaxed">
                  <pre>
                    <code>{f.remediation_snippet}</code>
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Tab 4: Architecture & Trust Boundaries */}
      {activeTab === 'architecture' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400 font-mono">
              Identified Components
            </h3>
            <ul className="space-y-2">
              {(recon.components || ['Core LLM Pipeline']).map((c: string, i: number) => (
                <li key={i} className="flex items-center gap-2 text-xs text-slate-300 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-rose-400 font-mono">
              Trust Boundaries & Attack Surfaces
            </h3>
            <ul className="space-y-2">
              {(recon.trust_boundaries || ['Untrusted User Input Boundary']).map((b: string, i: number) => (
                <li key={i} className="flex items-center gap-2 text-xs text-slate-300 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                  <span>{b}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Code Evidence Viewer Modal */}
      <EvidenceViewerModal finding={selectedFinding} onClose={() => setSelectedFinding(null)} />
    </div>
  );
};
