import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  PlusCircle, 
  ListOrdered, 
  ShieldAlert, 
  Layers, 
  FileText,
  Info
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/new-assessment', label: 'New Assessment', icon: PlusCircle },
    { to: '/assessments', label: 'Assessments', icon: ListOrdered },
    { to: '/findings', label: 'Security Findings', icon: ShieldAlert },
    { to: '/compliance', label: 'Compliance Matrix', icon: Layers },
    { to: '/reports', label: 'Audit Reports', icon: FileText },
  ];

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-slate-950 flex flex-col justify-between p-4 shrink-0">
      <div className="space-y-6">
        <div className="px-3 pt-2">
          <p className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
            Security Operations
          </p>
        </div>

        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-950/80 to-blue-950/40 text-cyan-300 border border-cyan-800/50 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Academic Disclaimer Box */}
      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 text-[11px] text-slate-400 space-y-1.5 leading-relaxed">
        <div className="flex items-center gap-1.5 text-cyan-400 font-semibold font-mono text-[10px] uppercase">
          <Info className="w-3.5 h-3.5" />
          <span>Academic Benchmark</span>
        </div>
        <p>
          Inspired by the OWASP GenAI Crosswalk concept. Not an official OWASP certification.
        </p>
      </div>
    </aside>
  );
};
