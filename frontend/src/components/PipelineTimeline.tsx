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
  Loader2 
} from 'lucide-react';

interface Props {
  currentStatus: 'PENDING' | 'SCANNING' | 'ANALYZING' | 'COMPLETED' | 'FAILED';
}

export const PipelineTimeline: React.FC<Props> = ({ currentStatus }) => {
  const stages = [
    { id: 1, name: 'Reconnaissance', icon: Radar, desc: 'Architecture & Trust Boundaries' },
    { id: 2, name: 'Security Analysis', icon: ShieldAlert, desc: 'AST & Static Rule Scans' },
    { id: 3, name: 'Evidence Validation', icon: FileCheck2, desc: 'Snippet Verification' },
    { id: 4, name: 'Risk Assessment', icon: Scale, desc: 'Deterministic Scoring' },
    { id: 5, name: 'Compliance Mapping', icon: Layers, desc: 'Crosswalk Alignment' },
    { id: 6, name: 'Remediation Engine', icon: Wrench, desc: 'Actionable Mitigations' },
    { id: 7, name: 'Report Generation', icon: FileText, desc: 'Audit Artifact Assembly' },
  ];

  const getStageState = (stageId: number) => {
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
    <div className="w-full py-4">
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {stages.map((stage) => {
          const state = getStageState(stage.id);
          const Icon = stage.icon;

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
              className={`p-3 rounded-xl border transition-all flex flex-col items-start justify-between min-h-[95px] ${cardBorder}`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[10px] uppercase font-mono tracking-wider font-semibold text-slate-400">
                  Agent 0{stage.id}
                </span>
                {state === 'completed' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                {state === 'active' && <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />}
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
