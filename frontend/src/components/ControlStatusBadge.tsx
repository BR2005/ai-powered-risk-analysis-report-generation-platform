import React from 'react';
import type { ControlStatus } from '../types';
import { CheckCircle2, AlertCircle, XCircle, HelpCircle, MinusCircle } from 'lucide-react';

interface Props {
  status: ControlStatus | string;
  size?: 'sm' | 'md';
}

export const ControlStatusBadge: React.FC<Props> = ({ status, size = 'md' }) => {
  const st = status as ControlStatus;

  const config: Record<ControlStatus, { label: string; bg: string; text: string; border: string; icon: React.ReactNode }> = {
    IMPLEMENTED_WITH_EVIDENCE: {
      label: 'Implemented with Evidence',
      bg: 'bg-emerald-950/60',
      text: 'text-emerald-400',
      border: 'border-emerald-500/40',
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
    },
    PARTIALLY_IMPLEMENTED: {
      label: 'Partially Implemented',
      bg: 'bg-amber-950/60',
      text: 'text-amber-400',
      border: 'border-amber-500/40',
      icon: <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
    },
    MISSING_WITH_EVIDENCE: {
      label: 'Missing with Evidence',
      bg: 'bg-rose-950/60',
      text: 'text-rose-400',
      border: 'border-rose-500/40',
      icon: <XCircle className="w-3.5 h-3.5 text-rose-400" />
    },
    NOT_EVIDENCED: {
      label: 'Not Evidenced',
      bg: 'bg-slate-900/60',
      text: 'text-slate-400',
      border: 'border-slate-700/50',
      icon: <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
    },
    NOT_APPLICABLE: {
      label: 'Not Applicable',
      bg: 'bg-slate-950',
      text: 'text-slate-500',
      border: 'border-slate-800',
      icon: <MinusCircle className="w-3.5 h-3.5 text-slate-500" />
    }
  };

  const current = config[st] || config.NOT_EVIDENCED;
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${current.bg} ${current.text} ${current.border} ${sizeClasses}`}>
      {current.icon}
      <span>{current.label}</span>
    </span>
  );
};
