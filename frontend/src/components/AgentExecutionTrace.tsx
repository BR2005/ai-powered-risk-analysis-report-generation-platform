import React, { useState } from 'react';
import {
  Bot,
  Sparkles,
  Radar,
  ShieldAlert,
  FileCheck2,
  Scale,
  Layers,
  Wrench,
  FileText,
  CheckCircle2,
  Clock,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  Cpu
} from 'lucide-react';
import type { AgentExecutionRecord } from '../types';

interface Props {
  executionLog?: AgentExecutionRecord[];
  supervisorIterations?: number;
}

const AGENT_META: Record<string, { label: string; icon: React.ElementType; color: string; bg: string }> = {
  recon: {
    label: 'Reconnaissance Agent',
    icon: Radar,
    color: 'text-indigo-400 border-indigo-500/30',
    bg: 'bg-indigo-950/20'
  },
  security: {
    label: 'Security Analysis Agent',
    icon: ShieldAlert,
    color: 'text-rose-400 border-rose-500/30',
    bg: 'bg-rose-950/20'
  },
  evidence: {
    label: 'Evidence Verification Agent',
    icon: FileCheck2,
    color: 'text-amber-400 border-amber-500/30',
    bg: 'bg-amber-950/20'
  },
  risk: {
    label: 'Risk Assessment Agent',
    icon: Scale,
    color: 'text-purple-400 border-purple-500/30',
    bg: 'bg-purple-950/20'
  },
  compliance: {
    label: 'Compliance Mapping Agent',
    icon: Layers,
    color: 'text-cyan-400 border-cyan-500/30',
    bg: 'bg-cyan-950/20'
  },
  remediation: {
    label: 'Remediation Roadmap Agent',
    icon: Wrench,
    color: 'text-emerald-400 border-emerald-500/30',
    bg: 'bg-emerald-950/20'
  },
  report: {
    label: 'Report Generation Agent',
    icon: FileText,
    color: 'text-blue-400 border-blue-500/30',
    bg: 'bg-blue-950/20'
  },
  FINISH: {
    label: 'Supervisor Termination',
    icon: CheckCircle2,
    color: 'text-emerald-400 border-emerald-500/30',
    bg: 'bg-emerald-950/30'
  }
};

export const AgentExecutionTrace: React.FC<Props> = ({ executionLog = [], supervisorIterations = 0 }) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!executionLog || executionLog.length === 0) {
    return (
      <div className="glass-panel rounded-2xl p-8 text-center text-slate-400 border border-slate-800">
        <Bot className="w-10 h-10 text-cyan-400 mx-auto mb-3 animate-pulse" />
        <h3 className="text-sm font-bold text-white uppercase font-mono tracking-wider">
          Awaiting Multi-Agent Trace
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Gemma 4 autonomous supervision logs will populate as agents execute.
        </p>
      </div>
    );
  }

  const extraLoopsCount = executionLog.filter(
    (r) => r.supervisor_decision?.needs_extra_security_check
  ).length;

  const totalDuration = executionLog.reduce((acc, r) => acc + (r.duration_seconds || 0), 0);

  const isGemma4Sourced = executionLog.some(
    (r) => r.supervisor_decision?.source === 'gemma4'
  );

  return (
    <div className="space-y-6">
      {/* Supervisor Header Banner */}
      <div className="glass-panel rounded-2xl p-5 border border-cyan-500/30 bg-gradient-to-r from-slate-900/90 via-cyan-950/20 to-slate-900/90 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-inner">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  Gemma 4 Autonomous Multi-Agent Supervision
                </h3>
                <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                  <Sparkles className="w-3 h-3 text-cyan-400" />
                  {isGemma4Sourced ? 'Gemma 4 Directed' : 'Priority Queue Guardrail'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Dynamic conditional routing with bounded investigation loops based on live evidence verification.
              </p>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="flex items-center gap-4 border-t md:border-t-0 md:border-l border-slate-800 pt-3 md:pt-0 md:pl-5 text-xs font-mono">
            <div>
              <span className="text-slate-400 text-[10px] uppercase block">Iterations</span>
              <span className="text-sm font-bold text-cyan-400">
                {supervisorIterations || executionLog.length} / 8 Max
              </span>
            </div>
            <div>
              <span className="text-slate-400 text-[10px] uppercase block">Feedback Loops</span>
              <span className={`text-sm font-bold ${extraLoopsCount > 0 ? 'text-amber-400' : 'text-slate-300'}`}>
                {extraLoopsCount} {extraLoopsCount === 1 ? 'Loop' : 'Loops'}
              </span>
            </div>
            <div>
              <span className="text-slate-400 text-[10px] uppercase block">Runtime</span>
              <span className="text-sm font-bold text-slate-200">
                {totalDuration.toFixed(2)}s
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Step by step Execution Flow */}
      <div className="space-y-3">
        <h4 className="text-xs font-mono uppercase tracking-wider font-bold text-slate-400 px-1">
          Autonomous Collaboration Trace ({executionLog.length} steps)
        </h4>

        <div className="relative pl-6 space-y-4 before:content-[''] before:absolute before:left-2.5 before:top-4 before:bottom-4 before:w-0.5 before:bg-slate-800">
          {executionLog.map((record, idx) => {
            const meta = AGENT_META[record.agent_name] || {
              label: record.agent_name,
              icon: Cpu,
              color: 'text-slate-400 border-slate-700',
              bg: 'bg-slate-900/40'
            };
            const Icon = meta.icon;
            const decision = record.supervisor_decision || {};
            const isFinish = record.agent_name === 'FINISH';
            const isExpanded = expandedIndex === idx;

            return (
              <div
                key={idx}
                className={`relative glass-panel rounded-xl border transition-all ${
                  isFinish
                    ? 'border-emerald-500/40 bg-emerald-950/10'
                    : decision.needs_extra_security_check
                      ? 'border-amber-500/40 bg-amber-950/10'
                      : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                {/* Node icon along left timeline */}
                <div
                  className={`absolute -left-[31px] top-4 w-5 h-5 rounded-full border flex items-center justify-center bg-slate-950 text-[10px] font-mono font-bold ${
                    isFinish
                      ? 'border-emerald-500 text-emerald-400 ring-4 ring-emerald-950/60'
                      : decision.needs_extra_security_check
                        ? 'border-amber-400 text-amber-300 ring-4 ring-amber-950/60'
                        : 'border-cyan-500 text-cyan-300 ring-4 ring-cyan-950/60'
                  }`}
                >
                  {idx + 1}
                </div>

                <div className="p-4 space-y-3">
                  {/* Top Bar: Supervisor Decision & Badges */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                        Step {idx + 1} • Iteration {decision.iteration || idx + 1}
                      </span>

                      <div className="flex items-center gap-1.5 text-xs font-semibold text-white">
                        <Icon className={`w-4 h-4 ${meta.color.split(' ')[0]}`} />
                        <span>{meta.label}</span>
                      </div>

                      {decision.needs_extra_security_check && (
                        <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                          <RotateCcw className="w-3 h-3 animate-spin" />
                          Feedback Loop Active
                        </span>
                      )}

                      {decision.source === 'gemma4' && (
                        <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                          Gemma 4 Routing
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {record.duration_seconds.toFixed(2)}s
                      </span>
                      <button
                        onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                        className="text-slate-400 hover:text-white p-1"
                        aria-label="Toggle details"
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Gemma 4's Supervisor Reasoning Bubble */}
                  <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800/80 text-xs text-slate-300 flex items-start gap-2.5">
                    <Sparkles className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <div className="text-[10px] uppercase font-mono font-semibold text-cyan-400">
                        Gemma 4 Supervisor Routing Rationale
                      </div>
                      <p className="italic text-slate-200">
                        "{decision.reason || 'Model routing decision based on assessment state.'}"
                      </p>
                    </div>
                  </div>

                  {/* Agent Output Summary */}
                  <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-slate-400 font-semibold text-[11px]">Execution Result:</span>
                      <span className="text-slate-300">{record.output_summary}</span>
                    </div>
                  </div>

                  {/* Expanded Detail View */}
                  {isExpanded && (
                    <div className="pt-3 border-t border-slate-800/80 text-xs font-mono space-y-2 text-slate-400 animate-fadeIn">
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <span className="text-slate-400 block text-[10px]">Started At</span>
                          <span className="text-slate-300">{new Date(record.started_at).toLocaleTimeString()}</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Completed At</span>
                          <span className="text-slate-300">{new Date(record.completed_at).toLocaleTimeString()}</span>
                        </div>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">Routing Source</span>
                        <span className="text-cyan-400">{decision.source || 'default'}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
