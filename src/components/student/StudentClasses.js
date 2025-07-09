import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Badge, ListGroup, ProgressBar } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBookOpen, faUsers, faTasks, faEye, faCalendarAlt, faClipboardList } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import ApiService from '../../services/ApiService';

function StudentClasses({ user }) {
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    try {
      const response = await ApiService.getStudentClasses();
      setClasses(response.data);
    } catch (error) {
      console.error('Error fetching classes:', error);
      // Set demo data if API fails
      setClasses([
        {
          id: 1,
          name: 'Mathematics 101',
          description: 'Introduction to Algebra and Geometry',
          teacher_name: 'John Smith',
          current_grade: 92.5,
          total_assignments: 8,
          completed_assignments: 7,
          pending_assignments: 1,
          next_assignment: {
            title: 'Quiz Chapter 6',
            due_date: '2025-01-20'
          },
          recent_assignments: [
            { id: 1, title: 'Quiz Chapter 5', grade: 95, submitted: true },
            { id: 2, title: 'Homework Set 3', grade: 90, submitted: true }
          ]
        },
        {
          id: 2,
          name: 'Environmental Science',
          description: 'Study of environmental systems and sustainability',
          teacher_name: 'Sarah Johnson',
          current_grade: 88.0,
          total_assignments: 6,
          completed_assignments: 5,
          pending_assignments: 1,
          next_assignment: {
            title: 'Climate Research Paper',
            due_date: '2025-01-25'
          },
          recent_assignments: [
            { id: 3, title: 'Lab Report #2', grade: 85, submitted: true },
            { id: 4, title: 'Ecology Quiz', grade: 92, submitted: true }
          ]
        },
        {
          id: 3,
          name: 'Computer Science Fundamentals',
          description: 'Introduction to programming and computer systems',
          teacher_name: 'John Smith',
          current_grade: 85.0,
          total_assignments: 5,
          completed_assignments: 4,
          pending_assignments: 1,
          next_assignment: {
            title: 'Programming Project 2',
            due_date: '2025-01-30'
          },
          recent_assignments: [
            { id: 5, title: 'Programming Project 1', grade: 88, submitted: true },
            { id: 6, title: 'Data Structures Quiz', grade: 82, submitted: true }
          ]
        },
        {
          id: 4,
          name: 'Physics 101',
          description: 'Fundamental principles of physics',
          teacher_name: 'Dr. Wilson',
          current_grade: 91.0,
          total_assignments: 7,
          completed_assignments: 6,
          pending_assignments: 1,
          next_assignment: {
            title: 'Mechanics Lab Report',
            due_date: '2025-01-22'
          },
          recent_assignments: [
            { id: 7, title: 'Forces and Motion Quiz', grade: 94, submitted: true },
            { id: 8, title: 'Lab Exercise 3', grade: 89, submitted: true }
          ]
        }
      ]);
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

  const getProgressColor = (completed, total) => {
    const percentage = (completed / total) * 100;
    if (percentage >= 90) return 'success';
    if (percentage >= 70) return 'info';
    return 'warning';
  };

  if (loading) {
    return (
      <Container className="py-4">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </Container>
    );
  }

  return (
    <Container fluid className="py-4">
      <Row className="mb-4">
        <Col>
          <h1 className="h2 mb-1">
            <FontAwesomeIcon icon={faBookOpen} className="me-2" />
            My Classes
          </h1>
          <p className="text-muted">View your enrolled classes and track your progress</p>
        </Col>
      </Row>

      <Row className="g-4">
        {classes.map((classItem) => (
          <Col key={classItem.id} xs={12} lg={6}>
            <Card className="h-100 border-0 shadow-sm">
              <Card.Header className="bg-primary text-white">
                <div className="d-flex justify-content-between align-items-center">
                  <h5 className="mb-0">{classItem.name}</h5>
                  <Badge bg="light" text="dark">
                    <FontAwesomeIcon icon={faUsers} className="me-1" />
                    {classItem.teacher_name}
                  </Badge>
                </div>
              </Card.Header>
              
              <Card.Body>
                <p className="text-muted mb-3">{classItem.description}</p>
                
                {/* Current Grade */}
                <div className="mb-3">
                  <div className="d-flex justify-content-between align-items-center mb-1">
                    <span className="fw-bold">Current Grade</span>
                    <Badge bg={getGradeColor(classItem.current_grade)} className="px-2 py-1">
                      {classItem.current_grade}%
                    </Badge>
                  </div>
                </div>

                {/* Assignment Progress */}
                <div className="mb-3">
                  <div className="d-flex justify-content-between align-items-center mb-1">
                    <span className="small">Assignment Progress</span>
                    <span className="small text-muted">
                      {classItem.completed_assignments}/{classItem.total_assignments}
                    </span>
                  </div>
                  <ProgressBar 
                    variant={getProgressColor(classItem.completed_assignments, classItem.total_assignments)}
                    now={(classItem.completed_assignments / classItem.total_assignments) * 100}
                    style={{ height: '8px' }}
                  />
                </div>

                {/* Next Assignment */}
                {classItem.next_assignment && (
                  <div className="mb-3 p-2 bg-light rounded">
                    <div className="d-flex justify-content-between align-items-center">
                      <div>
                        <small className="text-muted">Next Assignment:</small>
                        <div className="fw-bold small">{classItem.next_assignment.title}</div>
                      </div>
                      <div className="text-end">
                        <small className="text-danger">
                          <FontAwesomeIcon icon={faCalendarAlt} className="me-1" />
                          {new Date(classItem.next_assignment.due_date).toLocaleDateString()}
                        </small>
                      </div>
                    </div>
                  </div>
                )}

                {/* Recent Assignments */}
                {classItem.recent_assignments && classItem.recent_assignments.length > 0 && (
                  <div className="mb-3">
                    <h6 className="mb-2">Recent Grades:</h6>
                    <ListGroup variant="flush">
                      {classItem.recent_assignments.slice(0, 2).map((assignment) => (
                        <ListGroup.Item key={assignment.id} className="px-0 py-1">
                          <div className="d-flex justify-content-between align-items-center">
                            <small className="fw-bold">{assignment.title}</small>
                            <Badge bg={getGradeColor(assignment.grade)} className="small">
                              {assignment.grade}%
                            </Badge>
                          </div>
                        </ListGroup.Item>
                      ))}
                    </ListGroup>
                  </div>
                )}

                {/* Quick Stats */}
                <Row className="text-center mb-3">
                  <Col xs={4}>
                    <div className="border-end">
                      <h6 className="text-success mb-0">{classItem.completed_assignments}</h6>
                      <small className="text-muted">Completed</small>
                    </div>
                  </Col>
                  <Col xs={4}>
                    <div className="border-end">
                      <h6 className={`text-${classItem.pending_assignments > 0 ? 'warning' : 'success'} mb-0`}>
                        {classItem.pending_assignments}
                      </h6>
                      <small className="text-muted">Pending</small>
                    </div>
                  </Col>
                  <Col xs={4}>
                    <h6 className="text-info mb-0">{classItem.total_assignments}</h6>
                    <small className="text-muted">Total</small>
                  </Col>
                </Row>
              </Card.Body>

              <Card.Footer className="bg-transparent">
                <Row className="g-2">
                  <Col xs={6}>
                    <Button 
                      variant="outline-primary" 
                      size="sm" 
                      className="w-100"
                      onClick={() => navigate(`/student/class/${classItem.id}`)}
                    >
                      <FontAwesomeIcon icon={faEye} className="me-1" />
                      View Details
                    </Button>
                  </Col>
                  <Col xs={6}>
                    <Button 
                      variant="primary" 
                      size="sm" 
                      className="w-100"
                      onClick={() => navigate(`/student/grades`)}
                    >
                      <FontAwesomeIcon icon={faClipboardList} className="me-1" />
                      View Grades
                    </Button>
                  </Col>
                </Row>
              </Card.Footer>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Summary Card */}
      <Row className="mt-4">
        <Col>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">Academic Summary</h5>
            </Card.Header>
            <Card.Body>
              <Row className="text-center">
                <Col xs={6} md={3}>
                  <div className="mb-3 mb-md-0">
                    <h3 className="text-primary mb-1">{classes.length}</h3>
                    <small className="text-muted">Enrolled Classes</small>
                  </div>
                </Col>
                <Col xs={6} md={3}>
                  <div className="mb-3 mb-md-0">
                    <h3 className="text-success mb-1">
                      {classes.reduce((sum, c) => sum + c.completed_assignments, 0)}
                    </h3>
                    <small className="text-muted">Assignments Completed</small>
                  </div>
                </Col>
                <Col xs={6} md={3}>
                  <div className="mb-3 mb-md-0">
                    <h3 className="text-warning mb-1">
                      {classes.reduce((sum, c) => sum + c.pending_assignments, 0)}
                    </h3>
                    <small className="text-muted">Assignments Pending</small>
                  </div>
                </Col>
                <Col xs={6} md={3}>
                  <div>
                    <h3 className="text-info mb-1">
                      {Math.round(classes.reduce((sum, c) => sum + c.current_grade, 0) / classes.length * 10) / 10}%
                    </h3>
                    <small className="text-muted">Overall Average</small>
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default StudentClasses;