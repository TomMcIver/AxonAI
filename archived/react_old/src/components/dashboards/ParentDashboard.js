import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, ListGroup, ProgressBar, Alert } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChild, faTrophy, faClipboardList, faCalendarAlt, faExclamationTriangle, faBrain, faBookOpen } from '@fortawesome/free-solid-svg-icons';
import apiService from '../../services/apiService';

function ParentDashboard({ user }) {
  const [childOverview, setChildOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [apiConnected, setApiConnected] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkApiHealth();
    fetchChildOverview();
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

  const fetchChildOverview = async () => {
    const parentId = user.id || user.parent_id || 1;
    const childId = user.child_id || user.children?.[0]?.id || 1;

    try {
      const response = await apiService.getChildOverview(parentId, childId);
      setChildOverview(response.data);
    } catch (err) {
      console.error('Error fetching child overview:', err);
      setError('Could not load child overview from Inference API. Showing demo data.');
      // Demo fallback
      setChildOverview({
        child_name: 'Demo Student',
        grade_level: '10th Grade',
        overall_grade: 87.3,
        classes: [
          { id: 1, name: 'Mathematics 101', grade: 92, teacher: 'Ms. Johnson' },
          { id: 2, name: 'Environmental Science', grade: 85, teacher: 'Mr. Smith' },
          { id: 3, name: 'Computer Science', grade: 88, teacher: 'Dr. Williams' },
          { id: 4, name: 'English Literature', grade: 81, teacher: 'Mrs. Davis' }
        ],
        recent_assignments: [
          { title: 'Math Quiz Chapter 5', class_name: 'Mathematics 101', grade: 95, due_date: '2025-01-15' },
          { title: 'Essay on Climate Change', class_name: 'Environmental Science', grade: null, due_date: '2025-01-18' },
          { title: 'Programming Project 1', class_name: 'Computer Science', grade: 88, due_date: '2025-01-20' }
        ],
        attendance_rate: 96,
        behavior_notes: 'Excellent participation in class discussions.'
      });
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (grade) => {
    if (grade >= 90) return 'success';
    if (grade >= 80) return 'info';
    if (grade >= 70) return 'warning';
    return 'danger';
  };

  if (loading) {
    return (
      <Container className="py-4">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2 text-muted">Loading child overview...</p>
        </div>
      </Container>
    );
  }

  const overview = childOverview || {};
  const overallGrade = overview.overall_grade || 0;
  const classes = overview.classes || [];
  const recentAssignments = overview.recent_assignments || [];

  return (
    <Container fluid className="py-4">
      <Row className="mb-4">
        <Col>
          <h1 className="h2 mb-1">Welcome back, {user.first_name}!</h1>
          <p className="text-muted">Parent Dashboard</p>
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

      {/* Child Summary Cards */}
      <Row className="g-4 mb-4">
        <Col xs={12} sm={6} lg={3}>
          <Card className="dashboard-card h-100 border-0 text-white" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
            <Card.Body className="d-flex flex-column align-items-center text-center">
              <FontAwesomeIcon icon={faChild} size="3x" className="mb-3" />
              <h5 className="card-title mb-1">{overview.child_name || 'Student'}</h5>
              <p className="card-text small opacity-75">{overview.grade_level || 'Grade N/A'}</p>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="dashboard-card h-100 border-0 text-white" style={{ background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)' }}>
            <Card.Body className="d-flex flex-column align-items-center text-center">
              <FontAwesomeIcon icon={faTrophy} size="3x" className="mb-3" />
              <h3 className="display-6 fw-bold mb-2">{overallGrade}%</h3>
              <h5 className="card-title mb-2">Overall Grade</h5>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="dashboard-card h-100 border-0 text-white" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
            <Card.Body className="d-flex flex-column align-items-center text-center">
              <FontAwesomeIcon icon={faBookOpen} size="3x" className="mb-3" />
              <h3 className="display-6 fw-bold mb-2">{classes.length}</h3>
              <h5 className="card-title mb-2">Enrolled Classes</h5>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="dashboard-card h-100 border-0 text-white" style={{ background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' }}>
            <Card.Body className="d-flex flex-column align-items-center text-center">
              <FontAwesomeIcon icon={faCalendarAlt} size="3x" className="mb-3" />
              <h3 className="display-6 fw-bold mb-2">{overview.attendance_rate || 'N/A'}%</h3>
              <h5 className="card-title mb-2">Attendance</h5>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="g-4">
        {/* Class Performance */}
        <Col xs={12} lg={6}>
          <Card className="h-100 border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">
                <FontAwesomeIcon icon={faClipboardList} className="me-2" />
                Class Performance
              </h5>
            </Card.Header>
            <Card.Body>
              {classes.length > 0 ? (
                classes.map((cls, index) => (
                  <div key={index} className="mb-3">
                    <div className="d-flex justify-content-between mb-1">
                      <span>{cls.name}</span>
                      <span className={`text-${getGradeColor(cls.grade)}`}>{cls.grade}%</span>
                    </div>
                    <ProgressBar
                      variant={getGradeColor(cls.grade)}
                      now={cls.grade}
                    />
                    {cls.teacher && (
                      <small className="text-muted">Teacher: {cls.teacher}</small>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-center p-4 text-muted">
                  <p>No class data available</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* Recent Assignments */}
        <Col xs={12} lg={6}>
          <Card className="h-100 border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">
                <FontAwesomeIcon icon={faCalendarAlt} className="me-2" />
                Recent Assignments
              </h5>
            </Card.Header>
            <Card.Body className="p-0">
              {recentAssignments.length > 0 ? (
                <ListGroup variant="flush">
                  {recentAssignments.map((assignment, index) => (
                    <ListGroup.Item key={index} className="d-flex justify-content-between align-items-start">
                      <div className="ms-2 me-auto">
                        <div className="fw-bold">{assignment.title}</div>
                        <small className="text-muted">{assignment.class_name}</small>
                      </div>
                      <div className="text-end">
                        {assignment.grade !== null && assignment.grade !== undefined ? (
                          <span className={`badge bg-${getGradeColor(assignment.grade)}`}>
                            {assignment.grade}%
                          </span>
                        ) : (
                          <span className="badge bg-secondary">Pending</span>
                        )}
                        <br />
                        <small className="text-muted">{assignment.due_date}</small>
                      </div>
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              ) : (
                <div className="text-center p-4 text-muted">
                  <p>No recent assignments</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* AI Insights / Behavior Notes */}
      {overview.behavior_notes && (
        <Row className="mt-4">
          <Col>
            <Card className="border-0 shadow-sm">
              <Card.Header className="bg-transparent">
                <h5 className="mb-0">
                  <FontAwesomeIcon icon={faBrain} className="me-2" />
                  Teacher Notes
                </h5>
              </Card.Header>
              <Card.Body>
                <p className="mb-0">{overview.behavior_notes}</p>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Refresh Button */}
      <Row className="mt-4">
        <Col className="text-center">
          <Button
            variant="outline-primary"
            onClick={() => { setLoading(true); fetchChildOverview(); }}
          >
            Refresh Overview
          </Button>
        </Col>
      </Row>
    </Container>
  );
}

export default ParentDashboard;
