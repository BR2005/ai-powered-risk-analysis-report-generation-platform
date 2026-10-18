import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
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
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans grid-bg">
        <Navbar />
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
