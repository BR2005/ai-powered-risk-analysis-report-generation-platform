import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { authenticateApiKey, clearApiKey } from './api/client';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { NewAssessment } from './pages/NewAssessment';
import { AssessmentsList } from './pages/AssessmentsList';
import { AssessmentDetails } from './pages/AssessmentDetails';
import { FindingsPage } from './pages/FindingsPage';
import { ComplianceMatrixPage } from './pages/ComplianceMatrixPage';
import { ReportsPage } from './pages/ReportsPage';

export const App: React.FC = () => {
  const [authorized, setAuthorized] = useState(false);
  const [checkingKey, setCheckingKey] = useState(
    () => Boolean(sessionStorage.getItem('lucifer_api_key')),
  );
  const [apiKey, setApiKey] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [authError, setAuthError] = useState('');

  useEffect(() => {
    const storedKey = sessionStorage.getItem('lucifer_api_key');
    if (!storedKey) return;
    authenticateApiKey(storedKey)
      .then(() => setAuthorized(true))
      .catch(() => {
        clearApiKey();
        setAuthError('Saved API key could not be verified. Enter a valid key.');
      })
      .finally(() => setCheckingKey(false));
  }, []);

  const handleAuthenticate = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setAuthError('');
    try {
      await authenticateApiKey(apiKey);
      setAuthorized(true);
      setApiKey('');
    } catch {
      setAuthError('Authentication failed. Check the API key and backend configuration.');
    } finally {
      setSubmitting(false);
    }
  };

  if (checkingKey) {
    return <div className="min-h-screen bg-slate-950 text-slate-300 grid place-items-center">Checking API access…</div>;
  }

  if (!authorized) {
    return (
      <main className="min-h-screen bg-slate-950 text-slate-100 grid place-items-center p-6">
        <form onSubmit={handleAuthenticate} className="w-full max-w-md space-y-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-8">
          <div>
            <h1 className="text-xl font-bold">Lucifer API access</h1>
            <p className="mt-2 text-sm text-slate-400">
              Enter the shared API key configured by your administrator. It is kept only in this browser tab.
            </p>
          </div>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>API key</span>
            <input
              type="password"
              autoComplete="current-password"
              required
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white"
            />
          </label>
          {authError && <p role="alert" className="text-sm text-rose-400">{authError}</p>}
          <button
            type="submit"
            disabled={submitting || !apiKey}
            className="w-full rounded-lg bg-cyan-500 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50"
          >
            {submitting ? 'Verifying…' : 'Continue'}
          </button>
        </form>
      </main>
    );
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans grid-bg">
        <Navbar />
        <div className="flex justify-end px-6 pt-2">
          <button
            onClick={() => {
              clearApiKey();
              setAuthorized(false);
            }}
            className="text-xs text-slate-400 hover:text-white"
          >
            Sign out
          </button>
        </div>
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-y-auto p-6 md:p-8 max-w-7xl mx-auto w-full">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/new-assessment" element={<NewAssessment />} />
              <Route path="/assessments" element={<AssessmentsList />} />
              <Route path="/assessments/:id" element={<AssessmentDetails />} />
              <Route path="/findings" element={<FindingsPage />} />
              <Route path="/compliance" element={<ComplianceMatrixPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
};

export default App;
