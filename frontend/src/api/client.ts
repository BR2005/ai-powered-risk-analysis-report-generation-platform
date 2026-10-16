import axios from 'axios';
import type { 
  AssessmentSummary, 
  AssessmentDetail, 
  Framework, 
  Finding, 
  HealthStatus 
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkHealth = async (): Promise<HealthStatus> => {
  const { data } = await api.get<HealthStatus>('/health');
  return data;
};

export const getFrameworks = async (): Promise<{ frameworks: Framework[]; total_frameworks: number; total_controls: number }> => {
  const { data } = await api.get('/api/v1/frameworks');
  return data;
};

export const listAssessments = async (): Promise<AssessmentSummary[]> => {
  const { data } = await api.get<AssessmentSummary[]>('/api/v1/assessments');
  return data;
};

export const getAssessment = async (id: string): Promise<AssessmentDetail> => {
  const { data } = await api.get<AssessmentDetail>(`/api/v1/assessments/${id}`);
  return data;
};

export const createAssessment = async (payload: {
  project_name: string;
  description?: string;
  architecture_text?: string;
  target_frameworks?: string[];
}): Promise<AssessmentDetail> => {
  const { data } = await api.post<AssessmentDetail>('/api/v1/assessments', payload);
  return data;
};

export const uploadAssessment = async (formData: FormData): Promise<AssessmentDetail> => {
  const { data } = await api.post<AssessmentDetail>('/api/v1/assessments/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return data;
};

export const getFindings = async (params?: {
  assessment_id?: string;
  severity?: string;
  category?: string;
  validation_status?: string;
}): Promise<Finding[]> => {
  const { data } = await api.get<Finding[]>('/api/v1/findings', { params });
  return data;
};

export const getReportJson = async (assessmentId: string): Promise<any> => {
  const { data } = await api.get(`/api/v1/assessments/${assessmentId}/report`);
  return data;
};

export const getReportPdfUrl = (assessmentId: string): string => {
  return `${API_BASE_URL}/api/v1/assessments/${assessmentId}/report.pdf`;
};
