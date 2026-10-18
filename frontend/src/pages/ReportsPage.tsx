import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { 
  FileText, 
  Download, 
  ExternalLink, 
  Copy, 
  Check, 
  ArrowRight
} from 'lucide-react';
import { listAssessments, getReportJson, downloadReportPdf } from '../api/client';
import type { AssessmentSummary } from '../types';
import { SeverityBadge } from '../components/SeverityBadge';

export const ReportsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const urlAssessmentId = searchParams.get('assessment_id');

  const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [jsonReport, setJsonReport] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    listAssessments()
      .then((data) => {
        setAssessments(data);
        const targetId = urlAssessmentId || (data.length > 0 ? data[0].id : null);
        setSelectedId(targetId);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [urlAssessmentId]);

  useEffect(() => {
    if (selectedId) {
      getReportJson(selectedId)
        .then(setJsonReport)
        .catch(console.error);
    }
  }, [selectedId]);

  const handleCopyJson = () => {
    if (jsonReport) {
      navigator.clipboard.writeText(JSON.stringify(jsonReport, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const selectedAssessment = assessments.find((a) => a.id === selectedId);

  return (
    <div className="space-y-6 animate-fadeIn pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          Assessment Reports & Audit Exports
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Download verifiable, structured audit reports in JSON and executive PDF formats.
        </p>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500 font-mono text-sm">
          Loading Audit Reports...
        </div>
      ) : assessments.length === 0 ? (
        <div className="glass-panel rounded-2xl p-12 text-center text-slate-400 border border-slate-800">
          <FileText className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <h3 className="text-base font-bold text-white">No Reports Generated Yet</h3>
          <p className="text-xs text-slate-500 mt-1">
            Run an assessment to generate your first audit report.
          </p>
          <Link
            to="/new-assessment"
            className="inline-flex items-center gap-1.5 px-4 py-2 mt-4 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 text-xs font-semibold"
          >
            <span>Create Assessment</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Assessment Selector Sidebar */}
          <div className="space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-bold">
              Select Assessment
            </h3>
            <div className="space-y-2">
              {assessments.map((a) => {
                const isSelected = a.id === selectedId;
                return (
                  <button
                    key={a.id}
                    onClick={() => setSelectedId(a.id)}
                    className={`w-full p-4 rounded-xl border text-left transition-all cursor-pointer ${
                      isSelected
                        ? 'border-cyan-500/70 bg-cyan-950/20 text-white shadow-sm'
                        : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-white truncate max-w-[180px]">
                        {a.project_name}
                      </span>
                      <SeverityBadge severity={a.risk_level} size="sm" />
                    </div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                      <span>Score: {a.overall_risk_score.toFixed(1)}/100</span>
                      <span>{new Date(a.created_at).toLocaleDateString()}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Report Preview Panel */}
          <div className="lg:col-span-2 space-y-4">
            {selectedAssessment && (
              <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-5">
                {/* Header with Export Buttons */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
                  <div>
                    <h2 className="text-lg font-bold text-white">{selectedAssessment.project_name}</h2>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">
                      Assessment ID: {selectedAssessment.id}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => downloadReportPdf(selectedAssessment.id).catch(() => window.alert('Could not download the PDF report.'))}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 text-xs font-bold shadow-sm transition-all"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download PDF</span>
                    </button>
                    <button
                      onClick={handleCopyJson}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 hover:border-slate-600 text-slate-300 text-xs font-semibold transition-colors cursor-pointer"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? 'Copied' : 'Copy JSON'}</span>
                    </button>
                  </div>
                </div>

                {/* Report Metadata Pills */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                  <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                    <span className="text-[10px] uppercase font-mono text-slate-400">Risk Score</span>
                    <div className="text-xl font-bold font-mono text-white mt-1">
                      {selectedAssessment.overall_risk_score.toFixed(1)}
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                    <span className="text-[10px] uppercase font-mono text-slate-400">Compliance</span>
                    <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                      {selectedAssessment.compliance_score.toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                    <span className="text-[10px] uppercase font-mono text-slate-400">Findings</span>
                    <div className="text-xl font-bold font-mono text-amber-400 mt-1">
                      {selectedAssessment.findings_count}
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                    <span className="text-[10px] uppercase font-mono text-slate-400">Status</span>
                    <div className="text-sm font-bold font-mono text-cyan-400 mt-2">
                      {selectedAssessment.status}
                    </div>
                  </div>
                </div>

                {/* JSON Report Viewer */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-slate-400">
                    <span>Structured Audit JSON Output</span>
                    <Link
                      to={`/assessments/${selectedAssessment.id}`}
                      className="text-cyan-400 hover:underline flex items-center gap-1"
                    >
                      <span>Interactive View</span>
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 max-h-[420px] overflow-y-auto leading-relaxed selection:bg-cyan-900">
                    <pre>
                      <code>
                        {jsonReport
                          ? JSON.stringify(jsonReport, null, 2)
                          : '// Loading structured report JSON...'}
                      </code>
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
