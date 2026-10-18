import React, { useEffect, useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { getFrameworks } from '../api/client';
import type { Framework } from '../types';

export const ComplianceMatrixPage: React.FC = () => {
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [activeFwId, setActiveFwId] = useState<string>('OWASP-GENAI');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getFrameworks()
      .then((data) => {
        setFrameworks(data.frameworks || []);
        if (data.frameworks?.length > 0) {
          setActiveFwId(data.frameworks[0].id);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const activeFramework = frameworks.find((fw) => fw.id === activeFwId);

  return (
    <div className="space-y-6 animate-fadeIn pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          GenAI Compliance Knowledge Base & Crosswalk Matrix
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Explore official security controls, technical verification guidance, and crosswalk mapping rationales.
        </p>
      </div>

      {/* Framework Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {frameworks.map((fw) => {
          const isActive = fw.id === activeFwId;
          return (
            <button
              key={fw.id}
              onClick={() => setActiveFwId(fw.id)}
              className={`px-4 py-2.5 rounded-xl text-xs font-mono font-bold tracking-wider shrink-0 transition-all cursor-pointer ${
                isActive
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/60 shadow-sm'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              <span>{fw.id}</span>
              <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-400">
                {fw.controls_count}
              </span>
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500 font-mono text-sm">
          Loading Framework Catalogs...
        </div>
      ) : activeFramework ? (
        <div className="space-y-6">
          {/* Active Framework Header Card */}
          <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <span className="text-xs font-mono text-cyan-400 font-bold uppercase tracking-widest">
                  {activeFramework.category}
                </span>
                <h2 className="text-xl font-bold text-white mt-0.5">{activeFramework.name}</h2>
              </div>
              <a
                href={activeFramework.source_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:border-cyan-500 text-cyan-400 text-xs font-semibold self-start sm:self-auto transition-colors"
              >
                <span>Official Publication</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>

            <p className="text-xs text-slate-400 italic">
              Publisher: {activeFramework.publisher} • Version: {activeFramework.version}
            </p>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 leading-relaxed">
              <b className="text-slate-300">Disclaimer: </b>
              {activeFramework.disclaimer}
            </div>
          </div>

          {/* Controls List */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 font-mono">
              Control Catalog ({activeFramework.controls.length} Controls)
            </h3>

            <div className="grid grid-cols-1 gap-4">
              {activeFramework.controls.map((ctrl) => (
                <div
                  key={ctrl.control_id}
                  className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <span className="px-2.5 py-1 rounded-md bg-cyan-950 text-cyan-400 border border-cyan-800/50 font-mono text-xs font-bold">
                        {ctrl.control_id}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 font-mono">
                        {ctrl.category}
                      </span>
                    </div>

                    {ctrl.reference_url && (
                      <a
                        href={ctrl.reference_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-slate-400 hover:text-cyan-400 flex items-center gap-1 font-mono transition-colors"
                      >
                        <span>Reference</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>

                  <div>
                    <h4 className="text-base font-bold text-white">{ctrl.title}</h4>
                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">{ctrl.description}</p>
                  </div>

                  {ctrl.verification_guidance && (
                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs font-mono space-y-1">
                      <div className="text-cyan-400 font-bold uppercase tracking-wider text-[10px]">
                        Verification & Evidence Guidance
                      </div>
                      <p className="text-slate-400 font-sans leading-relaxed">
                        {ctrl.verification_guidance}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
