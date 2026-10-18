import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  ListOrdered, 
  Search, 
  PlusCircle, 
  ArrowUpRight, 
  Download 
} from 'lucide-react';
import { listAssessments, getReportPdfUrl } from '../api/client';
import type { AssessmentSummary } from '../types';
import { SeverityBadge } from '../components/SeverityBadge';

export const AssessmentsList: React.FC = () => {
  const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    listAssessments()
      .then(setAssessments)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filtered = assessments.filter(
    (a) =>
      a.project_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (a.description || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fadeIn pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Assessment History & Audit Logs
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Historical records of evaluated GenAI systems, risk trajectories, and compliance postures.
          </p>
        </div>
        <Link
          to="/new-assessment"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-semibold text-xs shadow-sm transition-all"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Assessment</span>
        </Link>
      </div>

      {/* Search Input */}
      <div className="glass-panel rounded-2xl p-4 border border-slate-800">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search by project name or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-500 text-xs focus:outline-none focus:border-cyan-500 transition-colors"
          />
        </div>
      </div>

      {/* Assessments Grid */}
      {loading ? (
        <div className="p-12 text-center text-slate-500 font-mono text-sm">
          Loading Assessments...
        </div>
      ) : filtered.length === 0 ? (
        <div className="glass-panel rounded-2xl p-12 text-center text-slate-400 border border-slate-800">
          <ListOrdered className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <h3 className="text-base font-bold text-white">No Assessments Found</h3>
          <p className="text-xs text-slate-500 mt-1">
            {searchTerm ? 'No projects match your search.' : 'Get started by running your first assessment.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((a) => (
            <div
              key={a.id}
              className="glass-panel glass-panel-hover rounded-2xl p-5 border border-slate-800 space-y-4 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <SeverityBadge severity={a.risk_level} size="sm" />
                  <span className="text-xs font-mono text-slate-400">
                    {new Date(a.created_at).toLocaleDateString()}
                  </span>
                </div>
                <Link
                  to={`/assessments/${a.id}`}
                  className="text-base font-bold text-white hover:text-cyan-400 transition-colors line-clamp-1"
                >
                  {a.project_name}
                </Link>
                {a.description && (
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                    {a.description}
                  </p>
                )}
              </div>

              {/* Stats Bar */}
              <div className="grid grid-cols-3 gap-2 py-2 px-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-center text-xs">
                <div>
                  <span className="text-[10px] text-slate-500 font-mono uppercase">Risk Score</span>
                  <div className="font-bold font-mono text-slate-200 mt-0.5">
                    {a.overall_risk_score.toFixed(1)}/100
                  </div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 font-mono uppercase">Compliance</span>
                  <div className="font-bold font-mono text-emerald-400 mt-0.5">
                    {a.compliance_score.toFixed(1)}%
                  </div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 font-mono uppercase">Findings</span>
                  <div className="font-bold font-mono text-amber-400 mt-0.5">
                    {a.findings_count}
                  </div>
                </div>
              </div>

              {/* Footer Links */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs font-medium">
                <a
                  href={getReportPdfUrl(a.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="text-slate-400 hover:text-cyan-400 flex items-center gap-1 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>PDF Audit</span>
                </a>

                <Link
                  to={`/assessments/${a.id}`}
                  className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-semibold transition-colors"
                >
                  <span>View Details</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
