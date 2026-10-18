import React from 'react';
import { X, FileCode, Copy, Check } from 'lucide-react';
import type { Finding } from '../types';
import { SeverityBadge } from './SeverityBadge';

interface Props {
  finding: Finding | null;
  onClose: () => void;
}

export const EvidenceViewerModal: React.FC<Props> = ({ finding, onClose }) => {
  const [copied, setCopied] = React.useState(false);

  if (!finding) return null;

  const evidence = finding.evidences?.[0];

  const handleCopy = () => {
    if (evidence?.code_snippet) {
      navigator.clipboard.writeText(evidence.code_snippet);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div 
        className="w-full max-w-3xl glass-panel rounded-2xl border border-slate-700/60 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-3">
            <SeverityBadge severity={finding.severity} size="sm" />
            <span className="font-mono text-xs text-slate-400">{finding.finding_id}</span>
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/50">
              {finding.owasp_id || 'GenAI Risk'}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          <div>
            <h3 className="text-lg font-bold text-white mb-1.5">{finding.title}</h3>
            <p className="text-sm text-slate-300 leading-relaxed">{finding.description}</p>
          </div>

          {/* Evidence Location Header */}
          {evidence ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono text-slate-400 bg-slate-950/80 px-4 py-2 rounded-t-lg border-t border-x border-slate-800">
                <div className="flex items-center gap-2 text-cyan-400">
                  <FileCode className="w-4 h-4" />
                  <span>{evidence.file_path}</span>
                  {evidence.line_start && (
                    <span className="text-slate-500">
                      :L{evidence.line_start}{evidence.line_end ? `-L${evidence.line_end}` : ''}
                    </span>
                  )}
                </div>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 text-slate-400 hover:text-cyan-300 transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>

              {/* Code Snippet Box */}
              <div className="bg-slate-950 p-4 rounded-b-lg border-b border-x border-slate-800 font-mono text-xs text-slate-200 overflow-x-auto leading-relaxed selection:bg-cyan-900">
                <pre>
                  <code>{evidence.code_snippet || '// No snippet available'}</code>
                </pre>
              </div>

              {evidence.context_note && (
                <div className="text-xs text-slate-400 italic mt-1">
                  Context: {evidence.context_note}
                </div>
              )}
            </div>
          ) : (
            <div className="p-4 rounded-lg bg-slate-900 text-slate-400 text-xs">
              No code snippet captured for this finding.
            </div>
          )}

          {/* Remediation Section */}
          {finding.remediation && (
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400 font-mono">
                Recommended Remediation
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed">{finding.remediation}</p>
              {finding.remediation_snippet && (
                <div className="mt-2 bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-xs text-emerald-300 overflow-x-auto">
                  <pre>
                    <code>{finding.remediation_snippet}</code>
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/40 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
