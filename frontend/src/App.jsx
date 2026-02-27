import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import TeacherDashboard from './pages/teacher/TeacherDashboard';
import ClassOverview from './pages/teacher/ClassOverview';
import StudentDetail from './pages/teacher/StudentDetail';
import KnowledgeGraphPage from './pages/teacher/KnowledgeGraphPage';
import StudentDashboard from './pages/student/StudentDashboard';
import ParentDashboard from './pages/parent/ParentDashboard';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/teacher" element={<TeacherDashboard />} />
        <Route path="/teacher/class/:id" element={<ClassOverview />} />
        <Route path="/teacher/student/:id" element={<StudentDetail />} />
        <Route path="/teacher/knowledge-graph" element={<KnowledgeGraphPage />} />
        <Route path="/student" element={<StudentDashboard />} />
        <Route path="/parent" element={<ParentDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
