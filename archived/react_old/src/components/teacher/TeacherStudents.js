import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Badge, Form, InputGroup, Button } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUsers, faSearch, faEye, faEnvelope, faGraduationCap } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import ApiService from '../../services/ApiService';

function TeacherStudents({ user }) {
  const navigate = useNavigate();
  const [students, setStudents] = useState([]);
  const [filteredStudents, setFilteredStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClass, setSelectedClass] = useState('all');
  const [classes, setClasses] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    filterStudents();
  }, [searchTerm, selectedClass, students]);

  const fetchData = async () => {
    try {
      const [studentsResponse, classesResponse] = await Promise.all([
        ApiService.getTeacherStudents(),
        ApiService.getTeacherClasses()
      ]);
      
      setStudents(studentsResponse.data);
      setClasses(classesResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      // Set demo data if API fails
      setStudents([
        {
          id: 1,
          first_name: 'Jane',
          last_name: 'Doe',
          email: 'jane@student.com',
          classes: ['Mathematics 101', 'Computer Science'],
          overall_grade: 92.5,
          assignment_completion: 95,
          last_login: '2025-01-14',
          status: 'active'
        },
        {
          id: 2,
          first_name: 'Mike',
          last_name: 'Wilson',
          email: 'mike@student.com',
          classes: ['Mathematics 101'],
          overall_grade: 88.0,
          assignment_completion: 90,
          last_login: '2025-01-13',
          status: 'active'
        },
        {
          id: 3,
          first_name: 'Sarah',
          last_name: 'Brown',
          email: 'sarah@student.com',
          classes: ['Environmental Science'],
          overall_grade: 95.0,
          assignment_completion: 100,
          last_login: '2025-01-14',
          status: 'active'
        },
        {
          id: 4,
          first_name: 'Alex',
          last_name: 'Johnson',
          email: 'alex@student.com',
          classes: ['Mathematics 101', 'Environmental Science'],
          overall_grade: 79.5,
          assignment_completion: 75,
          last_login: '2025-01-10',
          status: 'inactive'
        },
        {
          id: 5,
          first_name: 'Emily',
          last_name: 'Davis',
          email: 'emily@student.com',
          classes: ['Computer Science'],
          overall_grade: 91.0,
          assignment_completion: 85,
          last_login: '2025-01-14',
          status: 'active'
        }
      ]);
      
      setClasses([
        { id: 1, name: 'Mathematics 101' },
        { id: 2, name: 'Environmental Science' },
        { id: 3, name: 'Computer Science' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filterStudents = () => {
    let filtered = students;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(student =>
        `${student.first_name} ${student.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
        student.email.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by class
    if (selectedClass !== 'all') {
      filtered = filtered.filter(student =>
        student.classes.some(className => className.includes(selectedClass))
      );
    }

    setFilteredStudents(filtered);
  };

  const getGradeColor = (grade) => {
    if (grade >= 90) return 'success';
    if (grade >= 80) return 'info';
    if (grade >= 70) return 'warning';
    return 'danger';
  };

  const getCompletionColor = (completion) => {
    if (completion >= 90) return 'success';
    if (completion >= 70) return 'warning';
    return 'danger';
  };

  const getStatusColor = (status) => {
    return status === 'active' ? 'success' : 'danger';
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
            <FontAwesomeIcon icon={faUsers} className="me-2" />
            My Students
          </h1>
          <p className="text-muted">View and manage your students across all classes</p>
        </Col>
      </Row>

      {/* Filters */}
      <Row className="mb-4">
        <Col md={6}>
          <InputGroup>
            <InputGroup.Text>
              <FontAwesomeIcon icon={faSearch} />
            </InputGroup.Text>
            <Form.Control
              type="text"
              placeholder="Search students by name or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </InputGroup>
        </Col>
        <Col md={4}>
          <Form.Select
            value={selectedClass}
            onChange={(e) => setSelectedClass(e.target.value)}
          >
            <option value="all">All Classes</option>
            {classes.map((classItem) => (
              <option key={classItem.id} value={classItem.name}>
                {classItem.name}
              </option>
            ))}
          </Form.Select>
        </Col>
        <Col md={2}>
          <div className="text-muted small text-end">
            {filteredStudents.length} student{filteredStudents.length !== 1 ? 's' : ''}
          </div>
        </Col>
      </Row>

      {/* Summary Cards */}
      <Row className="g-4 mb-4">
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faUsers} size="2x" className="text-primary mb-2" />
              <h3 className="mb-0">{students.length}</h3>
              <small className="text-muted">Total Students</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faGraduationCap} size="2x" className="text-success mb-2" />
              <h3 className="mb-0">
                {students.filter(s => s.overall_grade >= 80).length}
              </h3>
              <small className="text-muted">Above 80%</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faGraduationCap} size="2x" className="text-warning mb-2" />
              <h3 className="mb-0">
                {students.filter(s => s.assignment_completion < 80).length}
              </h3>
              <small className="text-muted">Need Attention</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faUsers} size="2x" className="text-info mb-2" />
              <h3 className="mb-0">
                {students.filter(s => s.status === 'active').length}
              </h3>
              <small className="text-muted">Active Students</small>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Students Table */}
      <Row>
        <Col>
          <Card className="border-0 shadow-sm">
            <Card.Body className="p-0">
              <div className="table-responsive">
                <Table hover className="mb-0">
                  <thead className="table-dark">
                    <tr>
                      <th>Student Name</th>
                      <th>Email</th>
                      <th>Classes</th>
                      <th>Overall Grade</th>
                      <th>Assignment Completion</th>
                      <th>Last Login</th>
                      <th>Status</th>
                      <th className="text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredStudents.map((student) => (
                      <tr key={student.id}>
                        <td>
                          <div className="fw-bold">{student.first_name} {student.last_name}</div>
                        </td>
                        <td>
                          <small className="text-muted">{student.email}</small>
                        </td>
                        <td>
                          <div className="d-flex flex-wrap gap-1">
                            {student.classes.map((className, index) => (
                              <Badge key={index} bg="secondary" className="small">
                                {className}
                              </Badge>
                            ))}
                          </div>
                        </td>
                        <td>
                          <Badge bg={getGradeColor(student.overall_grade)} className="px-2 py-1">
                            {student.overall_grade}%
                          </Badge>
                        </td>
                        <td>
                          <Badge bg={getCompletionColor(student.assignment_completion)} className="px-2 py-1">
                            {student.assignment_completion}%
                          </Badge>
                        </td>
                        <td>
                          <small className="text-muted">
                            {new Date(student.last_login).toLocaleDateString()}
                          </small>
                        </td>
                        <td>
                          <Badge bg={getStatusColor(student.status)}>
                            {student.status.charAt(0).toUpperCase() + student.status.slice(1)}
                          </Badge>
                        </td>
                        <td className="text-center">
                          <Button 
                            variant="outline-primary" 
                            size="sm" 
                            className="me-1"
                            onClick={() => navigate(`/teacher/student/${student.id}`)}
                          >
                            <FontAwesomeIcon icon={faEye} />
                          </Button>
                          <Button variant="outline-info" size="sm">
                            <FontAwesomeIcon icon={faEnvelope} />
                          </Button>
                        </td>
                      </tr>
                    ))}
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

export default TeacherStudents;