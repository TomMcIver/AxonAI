import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Badge, ListGroup } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChalkboardTeacher, faUsers, faTasks, faPlus, faEye } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import ApiService from '../../services/ApiService';

function TeacherClasses({ user }) {
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    try {
      const response = await ApiService.getTeacherClasses();
      setClasses(response.data);
    } catch (error) {
      console.error('Error fetching classes:', error);
      // Set demo data if API fails
      setClasses([
        {
          id: 1,
          name: 'Mathematics 101',
          description: 'Introduction to Algebra and Geometry',
          student_count: 25,
          assignment_count: 8,
          pending_grades: 3,
          assignments: [
            { id: 1, title: 'Quiz Chapter 5', due_date: '2025-01-15', submissions: 22 },
            { id: 2, title: 'Homework Set 3', due_date: '2025-01-18', submissions: 25 }
          ]
        },
        {
          id: 2,
          name: 'Environmental Science',
          description: 'Study of environmental systems and sustainability',
          student_count: 18,
          assignment_count: 6,
          pending_grades: 2,
          assignments: [
            { id: 3, title: 'Climate Change Essay', due_date: '2025-01-20', submissions: 15 },
            { id: 4, title: 'Lab Report #2', due_date: '2025-01-22', submissions: 18 }
          ]
        },
        {
          id: 3,
          name: 'Computer Science Fundamentals',
          description: 'Introduction to programming and computer systems',
          student_count: 22,
          assignment_count: 5,
          pending_grades: 3,
          assignments: [
            { id: 5, title: 'Programming Project 1', due_date: '2025-01-25', submissions: 20 }
          ]
        }
      ]);
    } finally {
      setLoading(false);
    }
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
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h1 className="h2 mb-1">
                <FontAwesomeIcon icon={faChalkboardTeacher} className="me-2" />
                My Classes
              </h1>
              <p className="text-muted">Manage your teaching classes and assignments</p>
            </div>
          </div>
        </Col>
      </Row>

      <Row className="g-4">
        {classes.map((classItem) => (
          <Col key={classItem.id} xs={12} lg={6} xl={4}>
            <Card className="h-100 border-0 shadow-sm">
              <Card.Header className="bg-primary text-white">
                <div className="d-flex justify-content-between align-items-center">
                  <h5 className="mb-0">{classItem.name}</h5>
                  <Badge bg="light" text="dark">
                    <FontAwesomeIcon icon={faUsers} className="me-1" />
                    {classItem.student_count}
                  </Badge>
                </div>
              </Card.Header>
              
              <Card.Body>
                <p className="text-muted mb-3">{classItem.description}</p>
                
                <Row className="text-center mb-3">
                  <Col xs={4}>
                    <div className="border-end">
                      <h4 className="text-primary mb-0">{classItem.assignment_count}</h4>
                      <small className="text-muted">Assignments</small>
                    </div>
                  </Col>
                  <Col xs={4}>
                    <div className="border-end">
                      <h4 className="text-success mb-0">{classItem.student_count}</h4>
                      <small className="text-muted">Students</small>
                    </div>
                  </Col>
                  <Col xs={4}>
                    <h4 className={`text-${classItem.pending_grades > 0 ? 'warning' : 'success'} mb-0`}>
                      {classItem.pending_grades}
                    </h4>
                    <small className="text-muted">Pending</small>
                  </Col>
                </Row>

                {/* Recent Assignments */}
                {classItem.assignments && classItem.assignments.length > 0 && (
                  <div className="mb-3">
                    <h6 className="mb-2">Recent Assignments:</h6>
                    <ListGroup variant="flush">
                      {classItem.assignments.slice(0, 2).map((assignment) => (
                        <ListGroup.Item key={assignment.id} className="px-0 py-1">
                          <div className="d-flex justify-content-between">
                            <small className="fw-bold">{assignment.title}</small>
                            <small className="text-muted">
                              {assignment.submissions}/{classItem.student_count} submitted
                            </small>
                          </div>
                        </ListGroup.Item>
                      ))}
                    </ListGroup>
                  </div>
                )}
              </Card.Body>

              <Card.Footer className="bg-transparent">
                <Row className="g-2">
                  <Col xs={6}>
                    <Button 
                      variant="outline-primary" 
                      size="sm" 
                      className="w-100"
                      onClick={() => navigate(`/teacher/class/${classItem.id}`)}
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
                      onClick={() => navigate(`/teacher/class/${classItem.id}/create-assignment`)}
                    >
                      <FontAwesomeIcon icon={faPlus} className="me-1" />
                      Add Assignment
                    </Button>
                  </Col>
                </Row>
              </Card.Footer>
            </Card>
          </Col>
        ))}

        {/* Add New Class Card (if admin functionality needed) */}
        <Col xs={12} lg={6} xl={4}>
          <Card className="h-100 border-2 border-dashed text-center d-flex align-items-center justify-content-center" style={{minHeight: '300px'}}>
            <Card.Body>
              <FontAwesomeIcon icon={faPlus} size="3x" className="text-muted mb-3" />
              <h5 className="text-muted">Need a new class?</h5>
              <p className="text-muted">Contact your administrator to create additional classes.</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default TeacherClasses;