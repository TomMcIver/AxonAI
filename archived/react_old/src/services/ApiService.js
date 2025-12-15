import axios from 'axios';
import AuthService from './AuthService';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const user = AuthService.getCurrentUser();
    if (user && user.token) {
      config.headers.Authorization = `Bearer ${user.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      AuthService.logout();
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

class ApiService {
  // User management
  getUsers() {
    return api.get('/admin/users');
  }

  createUser(userData) {
    return api.post('/admin/users', userData);
  }

  updateUser(userId, userData) {
    return api.put(`/admin/users/${userId}`, userData);
  }

  deleteUser(userId) {
    return api.delete(`/admin/users/${userId}`);
  }

  // Class management
  getClasses() {
    return api.get('/classes');
  }

  getClassById(classId) {
    return api.get(`/classes/${classId}`);
  }

  createClass(classData) {
    return api.post('/admin/classes', classData);
  }

  updateClass(classId, classData) {
    return api.put(`/admin/classes/${classId}`, classData);
  }

  deleteClass(classId) {
    return api.delete(`/admin/classes/${classId}`);
  }

  // Teacher endpoints
  getTeacherClasses() {
    return api.get('/teacher/classes');
  }

  getTeacherStudents() {
    return api.get('/teacher/students');
  }

  getTeacherGradebook() {
    return api.get('/teacher/gradebook');
  }

  getClassContent(classId) {
    return api.get(`/teacher/content/${classId}`);
  }

  // Assignment management
  createAssignment(classId, assignmentData) {
    return api.post(`/teacher/class/${classId}/assignments`, assignmentData);
  }

  getAssignments(classId) {
    return api.get(`/class/${classId}/assignments`);
  }

  gradeSubmission(submissionId, gradeData) {
    return api.post(`/teacher/grade/${submissionId}`, gradeData);
  }

  // Student endpoints
  getStudentClasses() {
    return api.get('/student/classes');
  }

  getStudentGrades() {
    return api.get('/student/grades');
  }

  submitAssignment(assignmentId, submissionData) {
    const formData = new FormData();
    formData.append('content', submissionData.content);
    if (submissionData.file) {
      formData.append('file', submissionData.file);
    }
    
    return api.post(`/student/assignment/${assignmentId}/submit`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }

  // File upload
  uploadFile(file, path) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('path', path);
    
    return api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }

  uploadContent(classId, file, contentData) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', contentData.name);
    formData.append('file_type', contentData.file_type);
    
    return api.post(`/teacher/class/${classId}/upload-content`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }

  // Dashboard stats
  getDashboardStats() {
    return api.get('/api/dashboard/stats');
  }

  // AI Chatbot Methods
  sendChatMessage(classId, message) {
    return api.post('/api/chat/send', {
      class_id: classId,
      message: message
    });
  }

  getChatHistory(classId) {
    return api.get(`/api/chat/history/${classId}`);
  }

  getTeacherInsights(classId) {
    return api.get(`/api/teacher/insights/${classId}`);
  }

  // Admin Data Export Methods
  previewExportData(selections) {
    return api.post('/api/admin/export/preview', {
      selections: selections
    });
  }

  downloadExportData(selections) {
    return api.post('/api/admin/export/download', {
      selections: selections
    }, {
      responseType: 'blob'
    });
  }

  // Enhanced class and student methods with AI features
  getClassesWithAI() {
    return api.get('/api/classes');
  }

  getStudentsWithProfiles() {
    return api.get('/api/students');
  }
}

export default new ApiService();