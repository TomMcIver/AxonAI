import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, ListGroup, Alert } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChalkboardTeacher, faUsers, faClipboardList, faFolder, faCalendarAlt, faTasks, faBrain, faExclamationTriangle } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import ApiService from '../../services/ApiService';
import apiService from '../../services/apiService';

function TeacherDashboard({ user }) {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalClasses: 0,
    totalStudents: 0,
    pendingGrades: 0,
    recentAssignments: []
  });
  const [classMetrics, setClassMetrics] = useState(null);
  const [studentInsights, setStudentInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [apiConnected, setApiConnected] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkApiHealth();
    fetchDashboardData();
  }, []);

  const checkApiHealth = async () => {
    try {
      await apiService.checkHealth();
      setApiConnected(true);
    } catch (err) {
      console.warn('Inference API not available:', err.message);
      setApiConnected(false);
    }
  };

  const fetchDashboardData = async () => {
    try {
      // Fetch base dashboard data from existing backend
      const [classesResponse, studentsResponse, gradebookResponse] = await Promise.all([
        ApiService.getTeacherClasses(),
        ApiService.getTeacherStudents(),
        ApiService.getTeacherGradebook()
      ]);

      const classes = classesResponse.data || [];
      const students = studentsResponse.data || [];

      setStats({
        totalClasses: classes.length || 3,
        totalStudents: students.length || 25,
        pendingGrades: gradebookResponse.data.pendingGrades || 8,
        recentAssignments: classes.flatMap(c => c.assignments || []).slice(0, 5) || []
      });

      // Fetch inference API data (class metrics and student insights)
      try {
        const classId = classes.length > 0 ? classes[0].id : 1;
        const metricsResponse = await apiService.getClassMetrics(classId);
        setClassMetrics(metricsResponse.data);
      } catch (metricsErr) {
        console.warn('Could not fetch class metrics:', metricsErr.message);
      }

      try {
        const studentId = students.length > 0 ? students[0].id : 1;
        const insightsResponse = await apiService.getStudentInsights(studentId);
        setStudentInsights(insightsResponse.data);
      } catch (insightsErr) {
        console.warn('Could not fetch student insights:', insightsErr.message);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('Could not load dashboard data. Showing demo data.');
      // Set demo data if API fails
      setStats({
        totalClasses: 3,
        totalStudents: 25,
        pendingGrades: 8,
        recentAssignments: [
          { id: 1, title: 'Math Quiz Chapter 5', class_name: 'Mathematics 101', due_date: '2025-01-15' },
          { id: 2, title: 'Essay on Climate Change', class_name: 'Environmental Science', due_date: '2025-01-18' },
          { id: 3, title: 'Programming Project 1', class_name: 'Computer Science', due_date: '2025-01-20' }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const dashboardCards = [
    {
      title: 'My Classes',
      description: 'Manage your teaching classes',
      icon: faChalkboardTeacher,
      color: 'primary',
      value: stats.totalClasses,
      path: '/teacher/classes'
    },
    {
      title: 'My Students',
      description: 'View all your students',
      icon: faUsers,
      color: 'success',
      value: stats.totalStudents,
      path: '/teacher/students'
    },
    {
      title: 'Gradebook',
      description: 'Grade assignments and view progress',
      icon: faClipboardList,
      color: 'warning',
      value: `${stats.pendingGrades} pending`,
      path: '/teacher/gradebook'
    },
    {
      title: 'Course Content',
      description: 'Upload and manage course materials',
      icon: faFolder,
      color: 'info',
      value: 'Manage',
      path: '/teacher/content'
    }
  ];

  if (loading) {
    return (
      <Container className="py-4">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2 text-muted">Loading dashboard data...</p>
        </div>
      </Container>
    );
  }

  return (
    <Container fluid className="py-4">
      <Row className="mb-4">
        <Col>
          <h1 className="h2 mb-1">Welcome back, {user.first_name}!</h1>
          <p className="text-muted">Teacher Dashboard</p>
        </Col>
        <Col xs="auto" className="d-flex align-items-center">
          <span className={`badge bg-${apiConnected ? 'success' : 'secondary'} me-2`}>
            {apiConnected ? 'AI Connected' : 'AI Offline'}
          </span>
        </Col>
      </Row>

      {error && (
        <Alert variant="warning" dismissible onClose={() => setError(null)}>
          <FontAwesomeIcon icon={faExclamationTriangle} className="me-2" />
          {error}
        </Alert>
      )}

      <Row className="g-4 mb-4">
        {dashboardCards.map((card, index) => (
          <Col key={index} xs={12} sm={6} lg={3}>
            <Card
              className="dashboard-card teacher-card h-100 border-0 text-white"
              onClick={() => navigate(card.path)}
              style={{ cursor: 'pointer' }}
            >
              <Card.Body className="d-flex flex-column align-items-center text-center">
                <FontAwesomeIcon icon={card.icon} size="3x" className="mb-3" />
                <h3 className="display-6 fw-bold mb-2">{card.value}</h3>
                <h5 className="card-title mb-2">{card.title}</h5>
                <p className="card-text small opacity-75">{card.description}</p>
                <Button
                  variant="light"
                  className="mt-auto"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(card.path);
                  }}
                >
                  View Details
                </Button>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>

      <Row className="g-4">
        {/* Recent Assignments */}
        <Col xs={12} lg={6}>
          <Card className="h-100 border-0 shadow-sm">
            <Card.Header className="bg-transparent d-flex justify-content-between align-items-center">
              <h5 className="mb-0">
                <FontAwesomeIcon icon={faTasks} className="me-2" />
                Recent Assignments
              </h5>
              <Button
                variant="outline-primary"
                size="sm"
                onClick={() => navigate('/teacher/classes')}
              >
                View All
              </Button>
            </Card.Header>
            <Card.Body className="p-0">
              {stats.recentAssignments.length > 0 ? (
                <ListGroup variant="flush">
                  {stats.recentAssignments.map((assignment, index) => (
                    <ListGroup.Item key={index} className="d-flex justify-content-between align-items-start">
                      <div className="ms-2 me-auto">
                        <div className="fw-bold">{assignment.title}</div>
                        <small className="text-muted">{assignment.class_name}</small>
                      </div>
                      <small className="text-muted">
                        <FontAwesomeIcon icon={faCalendarAlt} className="me-1" />
                        {assignment.due_date}
                      </small>
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              ) : (
                <div className="text-center p-4 text-muted">
                  <FontAwesomeIcon icon={faTasks} size="2x" className="mb-2" />
                  <p>No recent assignments</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* AI Insights Panel */}
        <Col xs={12} lg={6}>
          <Card className="h-100 border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">
                <FontAwesomeIcon icon={faBrain} className="me-2" />
                AI Insights
              </h5>
            </Card.Header>
            <Card.Body>
              {classMetrics ? (
                <div className="mb-3">
                  <h6>Class Metrics</h6>
                  <pre className="bg-light p-3 rounded small" style={{ maxHeight: '150px', overflow: 'auto' }}>
                    {JSON.stringify(classMetrics, null, 2)}
                  </pre>
                </div>
              ) : (
                <p className="text-muted small">Class metrics unavailable. Ensure the Inference API is running.</p>
              )}
              {studentInsights ? (
                <div>
                  <h6>Student Insights</h6>
                  <pre className="bg-light p-3 rounded small" style={{ maxHeight: '150px', overflow: 'auto' }}>
                    {JSON.stringify(studentInsights, null, 2)}
                  </pre>
                </div>
              ) : (
                <p className="text-muted small">Student insights unavailable. Ensure the Inference API is running.</p>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Row className="mt-4">
        <Col>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">Quick Actions</h5>
            </Card.Header>
            <Card.Body>
              <Row className="g-3">
                <Col xs={12} md={6} lg={3}>
                  <Button
                    variant="outline-primary"
                    className="w-100"
                    onClick={() => navigate('/teacher/classes')}
                  >
                    <FontAwesomeIcon icon={faTasks} className="me-2" />
                    Create New Assignment
                  </Button>
                </Col>
                <Col xs={12} md={6} lg={3}>
                  <Button
                    variant="outline-success"
                    className="w-100"
                    onClick={() => navigate('/teacher/gradebook')}
                  >
                    <FontAwesomeIcon icon={faClipboardList} className="me-2" />
                    Grade Submissions
                  </Button>
                </Col>
                <Col xs={12} md={6} lg={3}>
                  <Button
                    variant="outline-info"
                    className="w-100"
                    onClick={() => navigate('/teacher/content')}
                  >
                    <FontAwesomeIcon icon={faFolder} className="me-2" />
                    Upload Course Material
                  </Button>
                </Col>
                <Col xs={12} md={6} lg={3}>
                  <Button
                    variant="outline-warning"
                    className="w-100"
                    onClick={() => navigate('/teacher/students')}
                  >
                    <FontAwesomeIcon icon={faUsers} className="me-2" />
                    View Student Progress
                  </Button>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default TeacherDashboard;
