import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Badge, ListGroup } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUser, faEnvelope, faCalendarAlt, faTrophy, faClipboardList, faBookOpen } from '@fortawesome/free-solid-svg-icons';
import { useParams } from 'react-router-dom';
import ApiService from '../../services/ApiService';

function StudentProfile({ user }) {
  const { studentId } = useParams();
  const [student, setStudent] = useState(null);
  const [grades, setGrades] = useState([]);
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStudentData();
  }, [studentId]);

  const fetchStudentData = async () => {
    try {
      // const response = await ApiService.getStudentProfile(studentId);
      // setStudent(response.data.student);
      // setGrades(response.data.grades);
      // setClasses(response.data.classes);
      
      // Demo data
      setStudent({
        id: studentId,
        first_name: 'Jane',
        last_name: 'Doe',
        email: 'jane@student.com',
        created_at: '2024-09-01',
        last_login: '2025-01-14',
        overall_grade: 92.5,
        total_assignments: 15,
        completed_assignments: 14,
        is_active: true
      });
      
      setGrades([
        { assignment_title: 'Quiz Chapter 5', class_name: 'Mathematics 101', grade: 95, max_points: 100, graded_at: '2025-01-15' },
        { assignment_title: 'Programming Project 1', class_name: 'Computer Science', grade: 88, max_points: 150, graded_at: '2025-01-20' },
        { assignment_title: 'Lab Report #2', class_name: 'Environmental Science', grade: 92, max_points: 100, graded_at: '2025-01-18' }
      ]);
      
      setClasses([
        { id: 1, name: 'Mathematics 101', teacher_name: 'John Smith', grade: 92.5 },
        { id: 3, name: 'Computer Science', teacher_name: 'John Smith', grade: 85.0 }
      ]);
    } catch (error) {
      console.error('Error fetching student data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (grade, maxPoints) => {
    const percentage = (grade / maxPoints) * 100;
    if (percentage >= 90) return 'success';
    if (percentage >= 80) return 'info';
    if (percentage >= 70) return 'warning';
    return 'danger';
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

  if (!student) {
    return (
      <Container className="py-4">
        <div className="text-center">
          <h4>Student not found</h4>
        </div>
      </Container>
    );
  }

  return (
    <Container fluid className="py-4">
      <Row className="mb-4">
        <Col>
          <h1 className="h2 mb-1">
            <FontAwesomeIcon icon={faUser} className="me-2" />
            Student Profile
          </h1>
          <p className="text-muted">Detailed view of student academic performance</p>
        </Col>
      </Row>

      <Row className="g-4">
        {/* Student Information */}
        <Col xs={12} md={4}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Header className="bg-primary text-white text-center">
              <FontAwesomeIcon icon={faUser} size="3x" className="mb-2" />
              <h5 className="mb-0">{student.first_name} {student.last_name}</h5>
            </Card.Header>
            <Card.Body>
              <ListGroup variant="flush">
                <ListGroup.Item className="d-flex justify-content-between">
                  <span>
                    <FontAwesomeIcon icon={faEnvelope} className="me-2 text-muted" />
                    Email
                  </span>
                  <small className="text-muted">{student.email}</small>
                </ListGroup.Item>
                <ListGroup.Item className="d-flex justify-content-between">
                  <span>
                    <FontAwesomeIcon icon={faCalendarAlt} className="me-2 text-muted" />
                    Enrolled
                  </span>
                  <small className="text-muted">{new Date(student.created_at).toLocaleDateString()}</small>
                </ListGroup.Item>
                <ListGroup.Item className="d-flex justify-content-between">
                  <span>
                    <FontAwesomeIcon icon={faCalendarAlt} className="me-2 text-muted" />
                    Last Login
                  </span>
                  <small className="text-muted">{new Date(student.last_login).toLocaleDateString()}</small>
                </ListGroup.Item>
                <ListGroup.Item className="d-flex justify-content-between">
                  <span>Status</span>
                  <Badge bg={student.is_active ? 'success' : 'danger'}>
                    {student.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </ListGroup.Item>
              </ListGroup>
            </Card.Body>
          </Card>
        </Col>

        {/* Academic Performance */}
        <Col xs={12} md={8}>
          <Row className="g-4 h-100">
            {/* Performance Stats */}
            <Col xs={12}>
              <Card className="border-0 shadow-sm">
                <Card.Header className="bg-transparent">
                  <h5 className="mb-0">
                    <FontAwesomeIcon icon={faTrophy} className="me-2" />
                    Academic Performance
                  </h5>
                </Card.Header>
                <Card.Body>
                  <Row className="text-center">
                    <Col xs={6} md={3}>
                      <div className="mb-3">
                        <h3 className="text-primary mb-1">{student.overall_grade}%</h3>
                        <small className="text-muted">Overall Grade</small>
                      </div>
                    </Col>
                    <Col xs={6} md={3}>
                      <div className="mb-3">
                        <h3 className="text-success mb-1">{student.completed_assignments}</h3>
                        <small className="text-muted">Completed</small>
                      </div>
                    </Col>
                    <Col xs={6} md={3}>
                      <div className="mb-3">
                        <h3 className="text-warning mb-1">{student.total_assignments - student.completed_assignments}</h3>
                        <small className="text-muted">Pending</small>
                      </div>
                    </Col>
                    <Col xs={6} md={3}>
                      <div className="mb-3">
                        <h3 className="text-info mb-1">{classes.length}</h3>
                        <small className="text-muted">Classes</small>
                      </div>
                    </Col>
                  </Row>
                </Card.Body>
              </Card>
            </Col>

            {/* Enrolled Classes */}
            <Col xs={12} md={6}>
              <Card className="border-0 shadow-sm h-100">
                <Card.Header className="bg-transparent">
                  <h6 className="mb-0">
                    <FontAwesomeIcon icon={faBookOpen} className="me-2" />
                    Enrolled Classes
                  </h6>
                </Card.Header>
                <Card.Body>
                  <ListGroup variant="flush">
                    {classes.map((classItem) => (
                      <ListGroup.Item key={classItem.id} className="d-flex justify-content-between align-items-center px-0">
                        <div>
                          <div className="fw-bold">{classItem.name}</div>
                          <small className="text-muted">Teacher: {classItem.teacher_name}</small>
                        </div>
                        <Badge bg={getGradeColor(classItem.grade, 100)}>
                          {classItem.grade}%
                        </Badge>
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </Card.Body>
              </Card>
            </Col>

            {/* Recent Grades */}
            <Col xs={12} md={6}>
              <Card className="border-0 shadow-sm h-100">
                <Card.Header className="bg-transparent">
                  <h6 className="mb-0">
                    <FontAwesomeIcon icon={faClipboardList} className="me-2" />
                    Recent Grades
                  </h6>
                </Card.Header>
                <Card.Body>
                  <ListGroup variant="flush">
                    {grades.slice(0, 5).map((grade, index) => (
                      <ListGroup.Item key={index} className="d-flex justify-content-between align-items-start px-0">
                        <div className="ms-2 me-auto">
                          <div className="fw-bold small">{grade.assignment_title}</div>
                          <small className="text-muted">{grade.class_name}</small>
                        </div>
                        <div className="text-end">
                          <Badge bg={getGradeColor(grade.grade, grade.max_points)}>
                            {grade.grade}/{grade.max_points}
                          </Badge>
                          <div>
                            <small className="text-muted">
                              {new Date(grade.graded_at).toLocaleDateString()}
                            </small>
                          </div>
                        </div>
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Col>
      </Row>

      {/* Detailed Grades Table */}
      <Row className="mt-4">
        <Col>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">All Grades</h5>
            </Card.Header>
            <Card.Body className="p-0">
              <div className="table-responsive">
                <Table hover className="mb-0">
                  <thead className="table-dark">
                    <tr>
                      <th>Assignment</th>
                      <th>Class</th>
                      <th>Grade</th>
                      <th>Percentage</th>
                      <th>Date Graded</th>
                    </tr>
                  </thead>
                  <tbody>
                    {grades.map((grade, index) => {
                      const percentage = Math.round((grade.grade / grade.max_points) * 100);
                      return (
                        <tr key={index}>
                          <td className="fw-bold">{grade.assignment_title}</td>
                          <td className="text-muted">{grade.class_name}</td>
                          <td>{grade.grade}/{grade.max_points}</td>
                          <td>
                            <Badge bg={getGradeColor(grade.grade, grade.max_points)}>
                              {percentage}%
                            </Badge>
                          </td>
                          <td className="text-muted">
                            {new Date(grade.graded_at).toLocaleDateString()}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </Table>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default StudentProfile;