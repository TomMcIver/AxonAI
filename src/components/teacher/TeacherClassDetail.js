import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Button, Badge, Tab, Tabs } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChalkboardTeacher, faUsers, faTasks, faPlus, faEdit, faDownload, faCalendarAlt } from '@fortawesome/free-solid-svg-icons';
import { useParams, useNavigate } from 'react-router-dom';
import ApiService from '../../services/ApiService';

function TeacherClassDetail({ user }) {
  const { classId } = useParams();
  const navigate = useNavigate();
  const [classData, setClassData] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClassData();
  }, [classId]);

  const fetchClassData = async () => {
    try {
      const response = await ApiService.getClassById(classId);
      setClassData(response.data);
      setAssignments(response.data.assignments || []);
      setStudents(response.data.students || []);
    } catch (error) {
      console.error('Error fetching class data:', error);
      // Set demo data if API fails
      setClassData({
        id: classId,
        name: 'Mathematics 101',
        description: 'Introduction to Algebra and Geometry',
        student_count: 25
      });
      
      setAssignments([
        {
          id: 1,
          title: 'Quiz Chapter 5',
          description: 'Test your understanding of algebraic concepts',
          due_date: '2025-01-15',
          max_points: 100,
          submissions: 22,
          created_at: '2025-01-08'
        },
        {
          id: 2,
          title: 'Homework Set 3',
          description: 'Practice problems for geometric proofs',
          due_date: '2025-01-18',
          max_points: 50,
          submissions: 25,
          created_at: '2025-01-10'
        },
        {
          id: 3,
          title: 'Midterm Project',
          description: 'Comprehensive project covering first half of semester',
          due_date: '2025-01-25',
          max_points: 200,
          submissions: 18,
          created_at: '2025-01-12'
        }
      ]);
      
      setStudents([
        { id: 1, first_name: 'Jane', last_name: 'Doe', email: 'jane@student.com', average_grade: 92.5 },
        { id: 2, first_name: 'Mike', last_name: 'Wilson', email: 'mike@student.com', average_grade: 88.0 },
        { id: 3, first_name: 'Sarah', last_name: 'Brown', email: 'sarah@student.com', average_grade: 95.0 },
        { id: 4, first_name: 'Alex', last_name: 'Johnson', email: 'alex@student.com', average_grade: 79.5 }
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

  const getSubmissionRate = (submissions, totalStudents) => {
    const rate = (submissions / totalStudents) * 100;
    if (rate >= 90) return 'success';
    if (rate >= 70) return 'warning';
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

  return (
    <Container fluid className="py-4">
      <Row className="mb-4">
        <Col>
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h1 className="h2 mb-1">
                <FontAwesomeIcon icon={faChalkboardTeacher} className="me-2" />
                {classData.name}
              </h1>
              <p className="text-muted">{classData.description}</p>
            </div>
            <Button 
              variant="primary"
              onClick={() => navigate(`/teacher/class/${classId}/create-assignment`)}
            >
              <FontAwesomeIcon icon={faPlus} className="me-2" />
              Create Assignment
            </Button>
          </div>
        </Col>
      </Row>

      {/* Class Overview Cards */}
      <Row className="g-4 mb-4">
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faUsers} size="2x" className="text-primary mb-2" />
              <h3 className="mb-0">{classData.student_count}</h3>
              <small className="text-muted">Enrolled Students</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faTasks} size="2x" className="text-success mb-2" />
              <h3 className="mb-0">{assignments.length}</h3>
              <small className="text-muted">Total Assignments</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faEdit} size="2x" className="text-warning mb-2" />
              <h3 className="mb-0">
                {assignments.reduce((sum, a) => sum + (classData.student_count - a.submissions), 0)}
              </h3>
              <small className="text-muted">Pending Submissions</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faCalendarAlt} size="2x" className="text-info mb-2" />
              <h3 className="mb-0">
                {assignments.filter(a => new Date(a.due_date) > new Date()).length}
              </h3>
              <small className="text-muted">Upcoming Deadlines</small>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Tabs for different views */}
      <Tabs defaultActiveKey="assignments" className="mb-4">
        <Tab eventKey="assignments" title="Assignments">
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <div className="d-flex justify-content-between align-items-center">
                <h5 className="mb-0">Assignments</h5>
                <Button 
                  variant="outline-primary" 
                  size="sm"
                  onClick={() => navigate(`/teacher/class/${classId}/create-assignment`)}
                >
                  <FontAwesomeIcon icon={faPlus} className="me-1" />
                  New Assignment
                </Button>
              </div>
            </Card.Header>
            <Card.Body className="p-0">
              <div className="table-responsive">
                <Table hover className="mb-0">
                  <thead className="table-dark">
                    <tr>
                      <th>Assignment</th>
                      <th>Due Date</th>
                      <th>Points</th>
                      <th>Submissions</th>
                      <th>Completion Rate</th>
                      <th className="text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignments.map((assignment) => (
                      <tr key={assignment.id}>
                        <td>
                          <div>
                            <div className="fw-bold">{assignment.title}</div>
                            <small className="text-muted">{assignment.description}</small>
                          </div>
                        </td>
                        <td>
                          <FontAwesomeIcon icon={faCalendarAlt} className="me-1 text-muted" />
                          {new Date(assignment.due_date).toLocaleDateString()}
                        </td>
                        <td>{assignment.max_points} pts</td>
                        <td>{assignment.submissions}/{classData.student_count}</td>
                        <td>
                          <Badge bg={getSubmissionRate(assignment.submissions, classData.student_count)}>
                            {Math.round((assignment.submissions / classData.student_count) * 100)}%
                          </Badge>
                        </td>
                        <td className="text-center">
                          <Button variant="outline-primary" size="sm" className="me-1">
                            <FontAwesomeIcon icon={faEdit} />
                          </Button>
                          <Button variant="outline-success" size="sm">
                            <FontAwesomeIcon icon={faDownload} />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            </Card.Body>
          </Card>
        </Tab>

        <Tab eventKey="students" title="Students">
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">Enrolled Students</h5>
            </Card.Header>
            <Card.Body className="p-0">
              <div className="table-responsive">
                <Table hover className="mb-0">
                  <thead className="table-dark">
                    <tr>
                      <th>Student Name</th>
                      <th>Email</th>
                      <th>Average Grade</th>
                      <th>Status</th>
                      <th className="text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map((student) => (
                      <tr key={student.id}>
                        <td>{student.first_name} {student.last_name}</td>
                        <td>{student.email}</td>
                        <td>
                          <Badge bg={getGradeColor(student.average_grade)}>
                            {student.average_grade}%
                          </Badge>
                        </td>
                        <td>
                          <Badge bg="success">Active</Badge>
                        </td>
                        <td className="text-center">
                          <Button 
                            variant="outline-info" 
                            size="sm"
                            onClick={() => navigate(`/teacher/student/${student.id}`)}
                          >
                            View Profile
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            </Card.Body>
          </Card>
        </Tab>
      </Tabs>
    </Container>
  );
}

export default TeacherClassDetail;