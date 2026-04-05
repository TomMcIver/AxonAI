import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/Login';
import TeacherDashboard from './pages/teacher/TeacherDashboard';
import ClassOverview from './pages/teacher/ClassOverview';
import StudentDetail from './pages/teacher/StudentDetail';
import KnowledgeGraphPage from './pages/teacher/KnowledgeGraphPage';
import StudentsPage from './pages/teacher/StudentsPage';
import SubjectsPage from './pages/teacher/SubjectsPage';
import SettingsPage from './pages/teacher/SettingsPage';
import StudentDashboard from './pages/student/StudentDashboard';
import ParentDashboard from './pages/parent/ParentDashboard';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/landing" element={<Landing />} />
        <Route path="/teacher" element={<TeacherDashboard />} />
        <Route path="/teacher/students" element={<StudentsPage />} />
        <Route path="/teacher/subjects" element={<SubjectsPage />} />
        <Route path="/teacher/settings" element={<SettingsPage />} />
        <Route path="/teacher/class/:id" element={<ClassOverview />} />
        <Route path="/teacher/student/:id" element={<StudentDetail />} />
        <Route path="/teacher/knowledge-graph" element={<KnowledgeGraphPage />} />
        <Route path="/student" element={<StudentDashboard />} />
        <Route path="/student/:id" element={<StudentDashboard />} />
        <Route path="/parent" element={<ParentDashboard />} />
        <Route path="/parent/:id" element={<ParentDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
