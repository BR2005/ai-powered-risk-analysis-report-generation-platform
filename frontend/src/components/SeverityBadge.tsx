import React from 'react';
import type { SeverityLevel } from '../types';
import { AlertOctagon, AlertTriangle, Info, CheckCircle } from 'lucide-react';

interface Props {
  severity: SeverityLevel | string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const SeverityBadge: React.FC<Props> = ({ severity, size = 'md', showIcon = true }) => {
  const sev = (severity || 'INFORMATIONAL').toUpperCase() as SeverityLevel;

  const config: Record<SeverityLevel, { bg: string; text: string; border: string; icon: React.ReactNode }> = {
    CRITICAL: {
      bg: 'bg-rose-950/60',
      text: 'text-rose-400',
      border: 'border-rose-500/40',
      icon: <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
    },
    HIGH: {
      bg: 'bg-orange-950/60',
      text: 'text-orange-400',
      border: 'border-orange-500/40',
      icon: <AlertTriangle className="w-3.5 h-3.5 text-orange-400" />
    },
    MEDIUM: {
      bg: 'bg-amber-950/60',
      text: 'text-amber-400',
      border: 'border-amber-500/40',
      icon: <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
    },
    LOW: {
      bg: 'bg-blue-950/60',
      text: 'text-blue-400',
      border: 'border-blue-500/40',
      icon: <Info className="w-3.5 h-3.5 text-blue-400" />
    },
    INFORMATIONAL: {
      bg: 'bg-slate-900/60',
      text: 'text-slate-400',
      border: 'border-slate-700/50',
      icon: <CheckCircle className="w-3.5 h-3.5 text-slate-400" />
    }
  };

  const style = config[sev] || config.INFORMATIONAL;
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : (size === 'lg' ? 'px-3.5 py-1.5 text-sm font-semibold' : 'px-2.5 py-1 text-xs font-medium');

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${style.bg} ${style.text} ${style.border} ${sizeClasses} tracking-wide uppercase font-mono shadow-sm`}>
      {showIcon && style.icon}
      {sev}
    </span>
  );
};
