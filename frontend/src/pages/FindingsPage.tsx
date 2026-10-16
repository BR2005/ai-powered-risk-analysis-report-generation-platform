import React, { useEffect, useState } from 'react';
import { 
  Search, 
  FileCode, 
  CheckCircle2 
} from 'lucide-react';
import { getFindings } from '../api/client';
import type { Finding } from '../types';
import { SeverityBadge } from '../components/SeverityBadge';
import { EvidenceViewerModal } from '../components/EvidenceViewerModal';

export const FindingsPage: React.FC = () => {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);

  useEffect(() => {
    getFindings()
      .then(setFindings)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const categories = Array.from(new Set(findings.map((f) => f.category)));

  const filteredFindings = findings.filter((f) => {
    const matchesSearch =
      f.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.finding_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (f.evidences?.[0]?.file_path || '').toLowerCase().includes(searchTerm.toLowerCase());

    const matchesSeverity =
      selectedSeverity === 'ALL' || f.severity.toUpperCase() === selectedSeverity;

    const matchesCategory =
      selectedCategory === 'ALL' || f.category === selectedCategory;

    return matchesSearch && matchesSeverity && matchesCategory;
  });

  return (
    <div className="space-y-6 animate-fadeIn pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          Security Vulnerabilities Explorer
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Search, filter, and inspect verified evidence across all evaluated application assessments.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel rounded-2xl p-4 border border-slate-800 flex flex-col md:flex-row gap-4">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search by title, description, rule, or file path..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-500 text-xs focus:outline-none focus:border-cyan-500 transition-colors"
          />
        </div>

        {/* Severity Filter */}
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs font-mono text-slate-400">Severity:</span>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-xs focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
            <option value="INFORMATIONAL">Informational</option>
          </select>
        </div>

        {/* Category Filter */}
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs font-mono text-slate-400">Category:</span>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-xs focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Findings List */}
      {loading ? (
        <div className="p-12 text-center text-slate-500 text-sm font-mono">
          Loading Security Findings...
        </div>
      ) : filteredFindings.length === 0 ? (
        <div className="glass-panel rounded-2xl p-12 text-center text-slate-400 border border-slate-800">
          <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
          <h3 className="text-base font-bold text-white">No Matching Vulnerabilities</h3>
          <p className="text-xs text-slate-500 mt-1">
            Try adjusting your search query or severity filters.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredFindings.map((f) => (
            <div
              key={f.id}
              onClick={() => setSelectedFinding(f)}
              className="glass-panel glass-panel-hover rounded-2xl p-5 border border-slate-800 space-y-3 cursor-pointer"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <SeverityBadge severity={f.severity} size="sm" />
                  <span className="font-mono text-xs text-slate-400">{f.finding_id}</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/40 font-mono">
                    {f.owasp_id || f.category}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                  <span>Score: <b className="text-white">{f.numerical_score}</b></span>
                  <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
                    {f.validation_status}
                  </span>
                </div>
              </div>

              <div>
                <h3 className="text-base font-bold text-white">{f.title}</h3>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                  {f.description}
                </p>
              </div>

              {f.evidences?.[0] && (
                <div className="flex items-center justify-between text-xs font-mono text-slate-400 bg-slate-950/70 px-3.5 py-2 rounded-lg border border-slate-800">
                  <div className="flex items-center gap-2 truncate text-cyan-400">
                    <FileCode className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{f.evidences[0].file_path}</span>
                    {f.evidences[0].line_start && (
                      <span className="text-slate-500">:L{f.evidences[0].line_start}</span>
                    )}
                  </div>
                  <span className="text-[11px] text-cyan-400 hover:underline shrink-0">
                    View Redacted Snippet →
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Evidence Viewer Modal */}
      <EvidenceViewerModal finding={selectedFinding} onClose={() => setSelectedFinding(null)} />
    </div>
  );
};
