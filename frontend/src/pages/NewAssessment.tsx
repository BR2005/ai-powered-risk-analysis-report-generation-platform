import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  UploadCloud, 
  CheckSquare, 
  Square, 
  AlertCircle, 
  Loader2, 
  ShieldCheck, 
  FileText 
} from 'lucide-react';
import { uploadAssessment, createAssessment } from '../api/client';
import { PipelineTimeline } from '../components/PipelineTimeline';

export const NewAssessment: React.FC = () => {
  const navigate = useNavigate();

  // Mode: "upload" or "manual"
  const [mode, setMode] = useState<'upload' | 'manual'>('upload');

  // Form Fields
  const [projectName, setProjectName] = useState('');
  const [description, setDescription] = useState('');
  const [architectureText, setArchitectureText] = useState('');
  const [file, setFile] = useState<File | null>(null);

  // Framework Selection
  const allFrameworks = [
    { id: 'OWASP-GENAI', name: 'OWASP GenAI Top 10', category: 'AppSec' },
    { id: 'NIST-AI-RMF', name: 'NIST AI RMF 1.0', category: 'Risk' },
    { id: 'MITRE-ATLAS', name: 'MITRE ATLAS', category: 'Threats' },
    { id: 'ISO-42001', name: 'ISO/IEC 42001 (AIMS)', category: 'Management' },
    { id: 'ISO-23894', name: 'ISO/IEC 23894', category: 'Guidance' },
    { id: 'EU-AI-ACT', name: 'EU AI Act Obligations', category: 'Regulatory' },
  ];
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([
    'OWASP-GENAI',
    'NIST-AI-RMF',
    'MITRE-ATLAS',
    'ISO-42001',
    'ISO-23894',
    'EU-AI-ACT',
  ]);

  // Submission State
  const [submitting, setSubmitting] = useState(false);
  const [progressStatus, setProgressStatus] = useState<'PENDING' | 'SCANNING' | 'ANALYZING' | 'COMPLETED' | 'FAILED'>('PENDING');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const toggleFramework = (id: string) => {
    setSelectedFrameworks((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectName.trim()) {
      setErrorMsg('Please enter a project name.');
      return;
    }

    if (mode === 'upload' && !file) {
      setErrorMsg('Please select a ZIP source code archive or code file to upload.');
      return;
    }

    if (mode === 'manual' && !architectureText.trim()) {
      setErrorMsg('Please provide an architecture description or component list.');
      return;
    }

    if (selectedFrameworks.length === 0) {
      setErrorMsg('Please select at least one compliance framework to evaluate.');
      return;
    }

    setErrorMsg(null);
    setSubmitting(true);
    setProgressStatus('SCANNING');

    try {
      if (mode === 'upload' && file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('project_name', projectName);
        if (description) formData.append('description', description);
        if (architectureText) formData.append('architecture_text', architectureText);
        formData.append('target_frameworks', JSON.stringify(selectedFrameworks));

        // Advance visual timeline
        setTimeout(() => setProgressStatus('ANALYZING'), 600);

        const res = await uploadAssessment(formData);
        setProgressStatus('COMPLETED');
        setTimeout(() => navigate(`/assessments/${res.id}`), 500);
      } else {
        setTimeout(() => setProgressStatus('ANALYZING'), 400);

        const res = await createAssessment({
          project_name: projectName,
          description,
          architecture_text: architectureText,
          target_frameworks: selectedFrameworks,
        });
        setProgressStatus('COMPLETED');
        setTimeout(() => navigate(`/assessments/${res.id}`), 500);
      }
    } catch (err: any) {
      setProgressStatus('FAILED');
      const msg = err.response?.data?.detail || err.message || 'Assessment execution failed.';
      setErrorMsg(msg);
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn pb-12">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          New Security & Compliance Assessment
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Initiate static security analysis, agentic threat assessment, and crosswalk compliance mapping.
        </p>
      </div>

      {/* Progress Timeline Overlay (When Active) */}
      {submitting && (
        <div className="glass-panel rounded-2xl p-6 border border-cyan-500/40 glow-cyan animate-pulse">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-bold text-cyan-300 flex items-center gap-2 font-mono">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Multi-Agent Assessment Pipeline In Progress...</span>
            </h3>
            <span className="text-xs font-mono text-cyan-400 font-semibold">{progressStatus}</span>
          </div>
          <PipelineTimeline currentStatus={progressStatus} />
        </div>
      )}

      {/* Form Card */}
      <form onSubmit={handleSubmit} className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
        {errorMsg && (
          <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-500/50 text-rose-300 text-xs flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Project Name & Description */}
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-1.5 font-mono">
              Application / Project Name *
            </label>
            <input
              type="text"
              required
              disabled={submitting}
              placeholder="e.g. Healthcare Clinical Advisory RAG Agent"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500 transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-1.5 font-mono">
              Project Description (Optional)
            </label>
            <input
              type="text"
              disabled={submitting}
              placeholder="e.g. Multi-agent clinical summarization system utilizing Llama-3 and ChromaDB vector store"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500 transition-colors"
            />
          </div>
        </div>

        {/* Input Mode Selector */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2 font-mono">
            Input Modality
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              disabled={submitting}
              onClick={() => setMode('upload')}
              className={`p-3.5 rounded-xl border flex items-center gap-3 text-left transition-all ${
                mode === 'upload'
                  ? 'border-cyan-500/80 bg-cyan-950/30 text-white shadow-sm'
                  : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:border-slate-700'
              }`}
            >
              <UploadCloud className={`w-5 h-5 ${mode === 'upload' ? 'text-cyan-400' : 'text-slate-500'}`} />
              <div>
                <div className="text-sm font-semibold">ZIP Source Archive / Code File</div>
                <div className="text-xs text-slate-400">Upload ZIP, Python, JS, JSON, or configs</div>
              </div>
            </button>

            <button
              type="button"
              disabled={submitting}
              onClick={() => setMode('manual')}
              className={`p-3.5 rounded-xl border flex items-center gap-3 text-left transition-all ${
                mode === 'manual'
                  ? 'border-cyan-500/80 bg-cyan-950/30 text-white shadow-sm'
                  : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:border-slate-700'
              }`}
            >
              <FileText className={`w-5 h-5 ${mode === 'manual' ? 'text-cyan-400' : 'text-slate-500'}`} />
              <div>
                <div className="text-sm font-semibold">Manual Architecture Specification</div>
                <div className="text-xs text-slate-400">Describe components, LLMs, and trust boundaries</div>
              </div>
            </button>
          </div>
        </div>

        {/* Mode 1: File Upload */}
        {mode === 'upload' && (
          <div className="space-y-4">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              Upload Source Code or Archive (.zip, .py, .js, .ts, .json, .yaml)
            </label>
            <div className="border-2 border-dashed border-slate-800 hover:border-cyan-500/60 rounded-2xl p-8 text-center transition-colors bg-slate-900/30">
              <input
                type="file"
                id="file-upload"
                disabled={submitting}
                onChange={handleFileChange}
                accept=".zip,.py,.js,.ts,.jsx,.tsx,.json,.yaml,.yml,.env,.md,.txt"
                className="hidden"
              />
              <label htmlFor="file-upload" className="cursor-pointer space-y-2 block">
                <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 text-cyan-400 mx-auto flex items-center justify-center">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <div className="text-sm font-semibold text-white">
                  {file ? file.name : 'Click to browse or drop source code archive'}
                </div>
                <p className="text-xs text-slate-400">
                  {file
                    ? `${(file.size / (1024 * 1024)).toFixed(2)} MB • Path-traversal protected`
                    : 'Supports ZIP archives up to 25MB. Static analysis only; files are never executed.'}
                </p>
              </label>
            </div>

            {/* Optional Architecture Text with Upload */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5 font-mono">
                Supplementary Architecture Context (Optional)
              </label>
              <textarea
                rows={3}
                disabled={submitting}
                placeholder="Mention any external LLMs, vector databases, or security controls in use..."
                value={architectureText}
                onChange={(e) => setArchitectureText(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500 font-mono text-xs"
              />
            </div>
          </div>
        )}

        {/* Mode 2: Manual Text Form */}
        {mode === 'manual' && (
          <div className="space-y-2">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-1.5 font-mono">
              Application Architecture Description & Threat Model *
            </label>
            <textarea
              rows={8}
              required
              disabled={submitting}
              placeholder="Describe your GenAI application architecture. Example:&#10;- Foundation Model: OpenAI GPT-4 / Ollama LLaMA-3&#10;- RAG Database: ChromaDB vector store with PDF ingestion&#10;- Agent Tools: Web search scraper, SQL query tool with database execution&#10;- Stated Controls: System prompt instructions against jailbreaks, user session tokens"
              value={architectureText}
              onChange={(e) => setArchitectureText(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500 font-mono text-xs leading-relaxed"
            />
          </div>
        )}

        {/* Framework Selector */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              Target Compliance & Risk Frameworks
            </label>
            <span className="text-xs text-slate-400 font-mono">
              {selectedFrameworks.length} / {allFrameworks.length} Selected
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {allFrameworks.map((fw) => {
              const isSelected = selectedFrameworks.includes(fw.id);
              return (
                <button
                  type="button"
                  key={fw.id}
                  disabled={submitting}
                  onClick={() => toggleFramework(fw.id)}
                  className={`p-3 rounded-xl border flex items-center justify-between text-left transition-all ${
                    isSelected
                      ? 'border-cyan-500/60 bg-cyan-950/20 text-white'
                      : 'border-slate-800 bg-slate-900/30 text-slate-500 hover:border-slate-700'
                  }`}
                >
                  <div>
                    <div className="text-xs font-bold font-mono text-cyan-300">{fw.id}</div>
                    <div className="text-xs font-medium text-slate-300">{fw.name}</div>
                  </div>
                  {isSelected ? (
                    <CheckSquare className="w-4 h-4 text-cyan-400 shrink-0" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-600 shrink-0" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-4 border-t border-slate-800 flex justify-end">
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/20 transition-all cursor-pointer"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Executing Assessment Pipeline...</span>
              </>
            ) : (
              <>
                <ShieldCheck className="w-4 h-4" />
                <span>Run Assessment</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
