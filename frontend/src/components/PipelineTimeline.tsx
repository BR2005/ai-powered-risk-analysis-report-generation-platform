import React from 'react';
import {
  Radar,
  ShieldAlert,
  FileCheck2,
  Scale,
  Layers,
  Wrench,
  FileText,
  CheckCircle2,
  Loader2,
  Bot,
  RotateCcw
} from 'lucide-react';
import type { AgentExecutionRecord } from '../types';

interface Props {
  currentStatus: 'PENDING' | 'SCANNING' | 'ANALYZING' | 'COMPLETED' | 'FAILED';
  agentExecutionLog?: AgentExecutionRecord[];
  supervisorIterations?: number;
}

export const PipelineTimeline: React.FC<Props> = ({
  currentStatus,
  agentExecutionLog = [],
  supervisorIterations
}) => {
  const stages = [
    { id: 1, key: 'recon', name: 'Reconnaissance', icon: Radar, desc: 'Architecture & Trust Boundaries' },
    { id: 2, key: 'security', name: 'Security Analysis', icon: ShieldAlert, desc: 'AST & Static Rule Scans' },
    { id: 3, key: 'evidence', name: 'Evidence Validation', icon: FileCheck2, desc: 'Snippet Verification' },
    { id: 4, key: 'risk', name: 'Risk Assessment', icon: Scale, desc: 'Deterministic Scoring' },
    { id: 5, key: 'compliance', name: 'Compliance Mapping', icon: Layers, desc: 'Crosswalk Alignment' },
    { id: 6, key: 'remediation', name: 'Remediation Engine', icon: Wrench, desc: 'Actionable Mitigations' },
    { id: 7, key: 'report', name: 'Report Generation', icon: FileText, desc: 'Audit Artifact Assembly' },
  ];

  // Count executions per agent
  const executionCounts = agentExecutionLog.reduce((acc, curr) => {
    acc[curr.agent_name] = (acc[curr.agent_name] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const getStageState = (stageKey: string, stageId: number) => {
    if (agentExecutionLog.length > 0) {
      const count = executionCounts[stageKey] || 0;
      if (count > 0) return 'completed';
      if (currentStatus === 'COMPLETED') return 'completed';
      return 'pending';
    }

    if (currentStatus === 'COMPLETED') return 'completed';
    if (currentStatus === 'FAILED') return stageId <= 2 ? 'completed' : 'failed';
    if (currentStatus === 'SCANNING') {
      return stageId === 2 ? 'active' : (stageId < 2 ? 'completed' : 'pending');
    }
    if (currentStatus === 'ANALYZING') {
      return stageId <= 3 ? 'completed' : (stageId === 4 ? 'active' : 'pending');
    }
    return 'pending';
  };

  return (
    <div className="w-full py-2 space-y-3">
      {/* Top micro bar for autonomous supervision */}
      {agentExecutionLog.length > 0 && (
        <div className="flex items-center justify-between text-xs font-mono px-1">
          <div className="flex items-center gap-2 text-cyan-400">
            <Bot className="w-3.5 h-3.5" />
            <span className="font-semibold">Gemma 4 Autonomous Supervision Active</span>
          </div>
          <span className="text-slate-400">
            {supervisorIterations || agentExecutionLog.length} Supervisor Routing Iterations
          </span>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {stages.map((stage) => {
          const state = getStageState(stage.key, stage.id);
          const Icon = stage.icon;
          const runCount = executionCounts[stage.key] || 0;

          let cardBorder = 'border-slate-800 bg-slate-900/40 text-slate-400';
          let iconColor = 'text-slate-500';

          if (state === 'completed') {
            cardBorder = 'border-emerald-500/30 bg-emerald-950/20 text-slate-200';
            iconColor = 'text-emerald-400';
          } else if (state === 'active') {
            cardBorder = 'border-cyan-500/60 bg-cyan-950/30 text-cyan-200 glow-cyan';
            iconColor = 'text-cyan-400';
          }

          return (
            <div
              key={stage.id}
              className={`p-3 rounded-xl border transition-all flex flex-col items-start justify-between min-h-[95px] relative ${cardBorder}`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[10px] uppercase font-mono tracking-wider font-semibold text-slate-400">
                  Agent 0{stage.id}
                </span>
                <div className="flex items-center gap-1">
                  {runCount > 1 && (
                    <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-0.5">
                      <RotateCcw className="w-2.5 h-2.5" />
                      x{runCount}
                    </span>
                  )}
                  {state === 'completed' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                  {state === 'active' && <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />}
                </div>
              </div>

              <div className="my-1.5 flex items-center gap-2">
                <Icon className={`w-4 h-4 ${iconColor}`} />
                <span className="text-xs font-semibold tracking-tight">{stage.name}</span>
              </div>

              <span className="text-[10px] text-slate-400 leading-tight">
                {stage.desc}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
