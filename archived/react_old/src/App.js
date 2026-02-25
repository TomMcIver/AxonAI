import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Services
import AuthService from './services/AuthService';

// Components
import Login from './components/Login';
import Navigation from './components/Navigation';

// Dashboard Components
import AdminDashboard from './components/dashboards/AdminDashboard';
import TeacherDashboard from './components/dashboards/TeacherDashboard';
import StudentDashboard from './components/dashboards/StudentDashboard';
import ParentDashboard from './components/dashboards/ParentDashboard';

// Admin Components
import ManageUsers from './components/admin/ManageUsers';
import ManageClasses from './components/admin/ManageClasses';

// Teacher Components
import TeacherClasses from './components/teacher/TeacherClasses';
import TeacherClassDetail from './components/teacher/TeacherClassDetail';
import CreateAssignment from './components/teacher/CreateAssignment';
import TeacherStudents from './components/teacher/TeacherStudents';
import TeacherGradebook from './components/teacher/TeacherGradebook';
import TeacherContent from './components/teacher/TeacherContent';
import UploadContent from './components/teacher/UploadContent';

// Student Components
import StudentClasses from './components/student/StudentClasses';
import StudentClassDetail from './components/student/StudentClassDetail';
import StudentGrades from './components/student/StudentGrades';
import SubmitAssignment from './components/student/SubmitAssignment';

// Shared Components
import StudentProfile from './components/shared/StudentProfile';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const currentUser = AuthService.getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    AuthService.logout();
    setUser(null);
  };

  // Protected Route Component
  const ProtectedRoute = ({ children, requiredRole = null }) => {
    if (!user) {
      return <Navigate to="/login" replace />;
    }
    
    if (requiredRole && user.role !== requiredRole) {
      return <Navigate to="/dashboard" replace />;
    }
    
    return children;
  };

  // Role-based Dashboard Routing
  const DashboardRouter = () => {
    switch (user?.role) {
      case 'admin':
        return <AdminDashboard user={user} />;
      case 'teacher':
        return <TeacherDashboard user={user} />;
      case 'student':
        return <StudentDashboard user={user} />;
      case 'parent':
        return <ParentDashboard user={user} />;
      default:
        return <Navigate to="/login" replace />;
    }
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center min-vh-100">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        {user && <Navigation user={user} onLogout={handleLogout} />}
        
        <Routes>
          {/* Public Routes */}
          <Route 
            path="/login" 
            element={
              user ? <Navigate to="/dashboard" replace /> : <Login onLogin={handleLogin} />
            } 
          />
          
          {/* Protected Routes */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <DashboardRouter />
              </ProtectedRoute>
            } 
          />

          {/* Admin Routes */}
          <Route 
            path="/admin/users" 
            element={
              <ProtectedRoute requiredRole="admin">
                <ManageUsers />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/classes" 
            element={
              <ProtectedRoute requiredRole="admin">
                <ManageClasses />
              </ProtectedRoute>
            } 
          />

          {/* Teacher Routes */}
          <Route 
            path="/teacher/classes" 
            element={
              <ProtectedRoute requiredRole="teacher">
                <TeacherClasses user={user} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/teacher/class/:classId" 
            element={
              <ProtectedRoute requiredRole="teacher">
                <TeacherClassDetail user={user} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/teacher/class/:classId/create-assignment" 
            element={
              <ProtectedRoute requiredRole="teacher">
                <CreateAssignment user={user} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/teacher/students" 
            element={
              <ProtectedRoute requiredRole="teacher">
                <TeacherStudents user={user} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/teacher/gradebook" 
            element={
              <ProtectedRoute requiredRole="teacher">
                <TeacherGradebook user={user} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/teacher/content" 
            element={
              <ProtectedRoute requiredRole="teacher">
                <TeacherContent user={user} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/teacher/content/upload/:classId" 
            element={
              <ProtectedRoute requiredRole="teacher">
                <UploadContent user={user} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/teacher/student/:studentId" 
            element={
              <ProtectedRoute requiredRole="teacher">
                <StudentProfile user={user} />
              </ProtectedRoute>
            } 
          />

          {/* Student Routes */}
          <Route 
            path="/student/classes" 
            element={
              <ProtectedRoute requiredRole="student">
                <StudentClasses user={user} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/student/class/:classId" 
            element={
              <ProtectedRoute requiredRole="student">
                <StudentClassDetail user={user} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/student/grades" 
            element={
              <ProtectedRoute requiredRole="student">
                <StudentGrades user={user} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/student/assignment/:assignmentId/submit" 
            element={
              <ProtectedRoute requiredRole="student">
                <SubmitAssignment user={user} />
              </ProtectedRoute>
            } 
          />

          {/* Default Routes */}
          <Route 
            path="/" 
            element={
              user ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />
            } 
          />
          
          {/* 404 Route */}
          <Route 
            path="*" 
            element={
              <div className="container py-5 text-center">
                <h1>404 - Page Not Found</h1>
                <p>The page you're looking for doesn't exist.</p>
              </div>
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;