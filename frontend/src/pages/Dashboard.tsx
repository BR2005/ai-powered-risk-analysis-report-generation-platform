import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldAlert, 
  Layers, 
  FileCheck, 
  ArrowUpRight, 
  PlusCircle, 
  Activity, 
  CheckCircle2, 
  AlertOctagon 
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  Cell, 
  PieChart, 
  Pie 
} from 'recharts';
import { listAssessments } from '../api/client';
import type { AssessmentSummary } from '../types';
import { SeverityBadge } from '../components/SeverityBadge';

export const Dashboard: React.FC = () => {
  const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listAssessments()
      .then(setAssessments)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  // Aggregated metrics
  const totalAssessments = assessments.length;
  const criticalCount = assessments.reduce((acc, a) => acc + (a.severity_breakdown?.CRITICAL || 0), 0);
  const highCount = assessments.reduce((acc, a) => acc + (a.severity_breakdown?.HIGH || 0), 0);
  const mediumCount = assessments.reduce((acc, a) => acc + (a.severity_breakdown?.MEDIUM || 0), 0);
  const lowCount = assessments.reduce((acc, a) => acc + (a.severity_breakdown?.LOW || 0), 0);
  const totalFindings = criticalCount + highCount + mediumCount + lowCount;

  const avgCompliance = totalAssessments > 0
    ? (assessments.reduce((acc, a) => acc + (a.compliance_score || 0), 0) / totalAssessments).toFixed(1)
    : '0.0';

  // Severity Distribution for Chart
  const severityChartData = [
    { name: 'Critical', count: criticalCount, color: '#f43f5e' },
    { name: 'High', count: highCount, color: '#fb923c' },
    { name: 'Medium', count: mediumCount, color: '#fbbf24' },
    { name: 'Low', count: lowCount, color: '#60a5fa' },
  ];

  // Compliance Posture Data
  const implementedCount = assessments.reduce((acc, a) => acc + (a.compliance_breakdown?.IMPLEMENTED_WITH_EVIDENCE || 0), 0);
  const missingCount = assessments.reduce((acc, a) => acc + (a.compliance_breakdown?.MISSING_WITH_EVIDENCE || 0), 0);
  const partialCount = assessments.reduce((acc, a) => acc + (a.compliance_breakdown?.PARTIALLY_IMPLEMENTED || 0), 0);
  const notEvidencedCount = assessments.reduce((acc, a) => acc + (a.compliance_breakdown?.NOT_EVIDENCED || 0), 0);

  const compliancePieData = [
    { name: 'Implemented', value: implementedCount || 1, color: '#10b981' },
    { name: 'Missing', value: missingCount || 1, color: '#ef4444' },
    { name: 'Partial', value: partialCount || 1, color: '#f59e0b' },
    { name: 'Not Evidenced', value: notEvidencedCount || 1, color: '#64748b' },
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            Security & Compliance Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time telemetry across assessed GenAI models, RAG pipelines, and agent frameworks.
          </p>
        </div>
        <Link
          to="/new-assessment"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-semibold text-sm shadow-lg shadow-cyan-500/20 transition-all cursor-pointer"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Assessment</span>
        </Link>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Assessments */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-mono tracking-wider font-semibold">Total Audited</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white font-mono">{totalAssessments}</span>
            <span className="text-xs text-slate-400">Applications</span>
          </div>
        </div>

        {/* Critical & High Findings */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-mono tracking-wider font-semibold">Critical Vulnerabilities</span>
            <AlertOctagon className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-rose-400 font-mono">{criticalCount}</span>
            <span className="text-xs text-slate-400 font-mono">({highCount} High)</span>
          </div>
        </div>

        {/* Total Findings */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-mono tracking-wider font-semibold">Total Findings</span>
            <ShieldAlert className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-amber-300 font-mono">{totalFindings}</span>
            <span className="text-xs text-slate-400">across codebase</span>
          </div>
        </div>

        {/* Avg Compliance Score */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-mono tracking-wider font-semibold">Avg Compliance</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-emerald-400 font-mono">{avgCompliance}%</span>
            <span className="text-xs text-slate-400">Across 6 Frameworks</span>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Breakdown Bar Chart */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white">Vulnerability Severity Distribution</h2>
              <p className="text-xs text-slate-400">Aggregated findings classified by severity level</p>
            </div>
            <ShieldAlert className="w-4 h-4 text-slate-500" />
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={severityChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {severityChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Compliance Posture Pie Chart */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white">Compliance Control Implementation</h2>
              <p className="text-xs text-slate-400">Status classification across evaluated controls</p>
            </div>
            <Layers className="w-4 h-4 text-slate-500" />
          </div>
          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={compliancePieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {compliancePieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs mt-2">
            <div className="flex items-center justify-center gap-1.5 text-emerald-400">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <span>Implemented</span>
            </div>
            <div className="flex items-center justify-center gap-1.5 text-rose-400">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
              <span>Missing</span>
            </div>
            <div className="flex items-center justify-center gap-1.5 text-amber-400">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
              <span>Partial</span>
            </div>
            <div className="flex items-center justify-center gap-1.5 text-slate-400">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-500" />
              <span>Not Evidenced</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Assessments Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white">Recent Security Assessments</h2>
            <p className="text-xs text-slate-400">Latest evaluated projects and risk scores</p>
          </div>
          <Link
            to="/assessments"
            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-500 text-sm">Loading assessment records...</div>
        ) : assessments.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <FileCheck className="w-10 h-10 text-slate-600 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-300">No assessments executed yet</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Start by uploading your GenAI application source code archive or entering an architecture description.
            </p>
            <Link
              to="/new-assessment"
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-xs font-semibold"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Run First Assessment</span>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/50 text-xs font-mono uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-6 py-3 font-semibold">Project Name</th>
                  <th className="px-6 py-3 font-semibold">Risk Level</th>
                  <th className="px-6 py-3 font-semibold">Risk Score</th>
                  <th className="px-6 py-3 font-semibold">Compliance</th>
                  <th className="px-6 py-3 font-semibold">Findings</th>
                  <th className="px-6 py-3 font-semibold">Date</th>
                  <th className="px-6 py-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {assessments.slice(0, 5).map((a) => (
                  <tr key={a.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="px-6 py-3.5 font-medium text-white">
                      <Link to={`/assessments/${a.id}`} className="hover:text-cyan-400 transition-colors">
                        {a.project_name}
                      </Link>
                      {a.description && (
                        <p className="text-xs text-slate-400 truncate max-w-xs font-normal">
                          {a.description}
                        </p>
                      )}
                    </td>
                    <td className="px-6 py-3.5">
                      <SeverityBadge severity={a.risk_level} size="sm" />
                    </td>
                    <td className="px-6 py-3.5 font-mono text-xs font-bold text-slate-200">
                      {a.overall_risk_score.toFixed(1)} / 100
                    </td>
                    <td className="px-6 py-3.5 font-mono text-xs text-emerald-400 font-semibold">
                      {a.compliance_score.toFixed(1)}%
                    </td>
                    <td className="px-6 py-3.5 font-mono text-xs text-slate-300">
                      {a.findings_count}
                    </td>
                    <td className="px-6 py-3.5 text-xs text-slate-400">
                      {new Date(a.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <Link
                        to={`/assessments/${a.id}`}
                        className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 font-medium"
                      >
                        <span>Details</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
