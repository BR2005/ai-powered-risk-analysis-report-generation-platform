import React, { useEffect, useState } from 'react';
import { ShieldCheck, Server, AlertCircle } from 'lucide-react';
import { checkHealth } from '../api/client';
import type { HealthStatus } from '../types';

export const Navbar: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkHealth()
      .then((data) => setHealth(data))
      .catch(() => setHealth(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-30 px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <ShieldCheck className="w-5 h-5 text-slate-950" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-base tracking-tight text-white font-sans">Lucifer</span>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/50">
              GenAI Security
            </span>
          </div>
          <p className="text-[10px] text-slate-400 hidden sm:block">
            OWASP GenAI • NIST AI RMF • MITRE ATLAS • ISO 42001 • EU AI Act
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Active AI Model Badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950/40 border border-cyan-800/60 text-xs font-mono text-cyan-300">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          <span>Model: Gemma 4</span>
        </div>

        {/* API Health Status Pill */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono">
          <Server className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-400 hidden md:inline">API:</span>
          {loading ? (
            <span className="text-slate-500">Checking...</span>
          ) : health ? (
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              v{health.version}
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-rose-400">
              <AlertCircle className="w-3 h-3" />
              Offline
            </span>
          )}
        </div>
      </div>
    </header>
  );
};
