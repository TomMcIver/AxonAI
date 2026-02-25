import axios from 'axios';

const INFERENCE_API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const inferenceApi = axios.create({
  baseURL: INFERENCE_API_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 15000
});

const apiService = {
  // Health check
  checkHealth() {
    return inferenceApi.get('/health');
  },

  // Model status
  getModelsStatus() {
    return inferenceApi.get('/models/status');
  },

  // Teacher endpoints
  getStudentInsights(studentId) {
    return inferenceApi.get(`/teacher/student/${studentId}/insights`);
  },

  getClassMetrics(classId) {
    return inferenceApi.get(`/teacher/class/${classId}/metrics`);
  },

  // Student endpoints
  getStudentClasses(studentId) {
    return inferenceApi.get(`/student/${studentId}/classes`);
  },

  getStudentAssignments(studentId, classId) {
    return inferenceApi.get(`/student/${studentId}/class/${classId}/assignments`);
  },

  saveAiInteraction(studentId, interactionData) {
    return inferenceApi.post(`/student/${studentId}/ai-interaction`, interactionData);
  },

  // Parent endpoints
  getChildOverview(parentId, childId) {
    return inferenceApi.get(`/parent/${parentId}/child/${childId}/overview`);
  }
};

export default apiService;
