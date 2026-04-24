
const { useState } = React;

function App() {
  const [page, setPage] = useState('landing');
  const [role, setRole] = useState('teacher');

  const navigate = (dest, newRole) => {
    if (newRole) setRole(newRole);
    setPage(dest);
    window.scrollTo(0, 0);
  };

  const p = { navigate, currentPage: page, role };

  switch (page) {
    case 'landing':           return <LandingPage onDemo={() => navigate('login')} />;
    case 'login':             return <LoginPage onLogin={navigate} />;
    // Teacher
    case 'teacher-dashboard': return <TeacherDashboard {...p} />;
    case 'teacher-students':  return <TeacherStudentsPage {...p} />;
    case 'teacher-subjects':  return <TeacherSubjectsPage {...p} />;
    case 'teacher-graph':     return <TeacherGraphPage {...p} />;
    case 'teacher-settings':  return <TeacherSettingsPage {...p} />;
    // Student
    case 'student-dashboard': return <StudentDashboard {...p} role="student" />;
    case 'student-graph':     return <StudentGraphPage {...p} role="student" />;
    case 'ai-chat':           return <AIChatPage {...p} role="student" />;
    // Parent
    case 'parent-dashboard':  return <ParentDashboard {...p} role="parent" />;
    default:                  return <LandingPage onDemo={() => navigate('login')} />;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
