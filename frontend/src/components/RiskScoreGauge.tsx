import React from 'react';
import type { SeverityLevel } from '../types';

interface Props {
  score: number;
  level: SeverityLevel | string;
  size?: number;
}

export const RiskScoreGauge: React.FC<Props> = ({ score, level, size = 160 }) => {
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  // Score is 0 - 100
  const normalizedScore = Math.min(100, Math.max(0, score));
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  const getColor = (lvl: string) => {
    switch (lvl.toUpperCase()) {
      case 'CRITICAL':
        return { stroke: '#f43f5e', glow: 'rgba(244, 63, 94, 0.4)', text: 'text-rose-400' };
      case 'HIGH':
        return { stroke: '#fb923c', glow: 'rgba(251, 146, 60, 0.4)', text: 'text-orange-400' };
      case 'MEDIUM':
        return { stroke: '#fbbf24', glow: 'rgba(251, 191, 36, 0.4)', text: 'text-amber-400' };
      case 'LOW':
        return { stroke: '#60a5fa', glow: 'rgba(96, 165, 250, 0.4)', text: 'text-blue-400' };
      default:
        return { stroke: '#34d399', glow: 'rgba(52, 211, 153, 0.4)', text: 'text-emerald-400' };
    }
  };

  const theme = getColor(level);

  return (
    <div className="relative inline-flex flex-col items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Track circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#1e293b"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        {/* Animated Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={theme.stroke}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          style={{
            transition: 'stroke-dashoffset 1s ease-in-out',
            filter: `drop-shadow(0 0 6px ${theme.glow})`
          }}
        />
      </svg>
      {/* Center Label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-3xl font-extrabold tracking-tight font-mono text-white">
          {score.toFixed(1)}
        </span>
        <span className="text-xs uppercase tracking-wider text-slate-400 font-medium">
          / 100
        </span>
        <span className={`text-xs font-bold uppercase tracking-widest mt-1 ${theme.text}`}>
          {level}
        </span>
      </div>
    </div>
  );
};
