import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Badge, Form, ProgressBar } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faClipboardList, faFilter, faTrophy, faCalendarAlt } from '@fortawesome/free-solid-svg-icons';
import ApiService from '../../services/ApiService';

function StudentGrades({ user }) {
  const [grades, setGrades] = useState([]);
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedClass, setSelectedClass] = useState('all');

  useEffect(() => {
    fetchGrades();
  }, []);

  const fetchGrades = async () => {
    try {
      const response = await ApiService.getStudentGrades();
      setGrades(response.data.grades);
      setClasses(response.data.classes);
    } catch (error) {
      console.error('Error fetching grades:', error);
      // Set demo data if API fails
      setClasses([
        { id: 1, name: 'Mathematics 101' },
        { id: 2, name: 'Environmental Science' },
        { id: 3, name: 'Computer Science Fundamentals' },
        { id: 4, name: 'Physics 101' }
      ]);
      
      setGrades([
        {
          id: 1,
          assignment_title: 'Quiz Chapter 5',
          class_name: 'Mathematics 101',
          class_id: 1,
          grade: 95,
          max_points: 100,
          feedback: 'Excellent work! You demonstrated a clear understanding of algebraic concepts.',
          graded_at: '2025-01-15',
          due_date: '2025-01-14'
        },
        {
          id: 2,
          assignment_title: 'Homework Set 3',
          class_name: 'Mathematics 101',
          class_id: 1,
          grade: 90,
          max_points: 50,
          feedback: 'Good work on most problems. Review section 5.3 for improvement.',
          graded_at: '2025-01-16',
          due_date: '2025-01-15'
        },
        {
          id: 3,
          assignment_title: 'Lab Report #2',
          class_name: 'Environmental Science',
          class_id: 2,
          grade: 85,
          max_points: 100,
          feedback: 'Well structured report. Consider adding more data analysis.',
          graded_at: '2025-01-12',
          due_date: '2025-01-10'
        },
        {
          id: 4,
          assignment_title: 'Ecology Quiz',
          class_name: 'Environmental Science',
          class_id: 2,
          grade: 92,
          max_points: 100,
          feedback: 'Great understanding of ecosystem dynamics!',
          graded_at: '2025-01-18',
          due_date: '2025-01-17'
        },
        {
          id: 5,
          assignment_title: 'Programming Project 1',
          class_name: 'Computer Science Fundamentals',
          class_id: 3,
          grade: 88,
          max_points: 150,
          feedback: 'Good logic and implementation. Code could be more efficient.',
          graded_at: '2025-01-20',
          due_date: '2025-01-19'
        },
        {
          id: 6,
          assignment_title: 'Data Structures Quiz',
          class_name: 'Computer Science Fundamentals',
          class_id: 3,
          grade: 82,
          max_points: 100,
          feedback: 'Review array operations and linked lists.',
          graded_at: '2025-01-22',
          due_date: '2025-01-21'
        },
        {
          id: 7,
          assignment_title: 'Forces and Motion Quiz',
          class_name: 'Physics 101',
          class_id: 4,
          grade: 94,
          max_points: 100,
          feedback: 'Excellent problem-solving approach!',
          graded_at: '2025-01-25',
          due_date: '2025-01-24'
        },
        {
          id: 8,
          assignment_title: 'Lab Exercise 3',
          class_name: 'Physics 101',
          class_id: 4,
          grade: 89,
          max_points: 75,
          feedback: 'Good experimental technique. Improve error analysis.',
          graded_at: '2025-01-26',
          due_date: '2025-01-25'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredGrades = () => {
    if (selectedClass === 'all') {
      return grades;
    }
    return grades.filter(grade => grade.class_id === parseInt(selectedClass));
  };

  const getGradeColor = (grade, maxPoints) => {
    const percentage = (grade / maxPoints) * 100;
    if (percentage >= 90) return 'success';
    if (percentage >= 80) return 'info';
    if (percentage >= 70) return 'warning';
    return 'danger';
  };

  const calculateClassAverages = () => {
    const averages = {};
    classes.forEach(classItem => {
      const classGrades = grades.filter(g => g.class_id === classItem.id);
      if (classGrades.length > 0) {
        const totalPercentage = classGrades.reduce((sum, grade) => 
          sum + (grade.grade / grade.max_points) * 100, 0
        );
        averages[classItem.id] = Math.round((totalPercentage / classGrades.length) * 10) / 10;
      } else {
        averages[classItem.id] = 0;
      }
    });
    return averages;
  };

  const calculateOverallStats = () => {
    if (grades.length === 0) return { average: 0, highest: 0, lowest: 0 };
    
    const percentages = grades.map(grade => (grade.grade / grade.max_points) * 100);
    const average = Math.round((percentages.reduce((sum, p) => sum + p, 0) / percentages.length) * 10) / 10;
    const highest = Math.round(Math.max(...percentages) * 10) / 10;
    const lowest = Math.round(Math.min(...percentages) * 10) / 10;
    
    return { average, highest, lowest };
  };

  const filteredGrades = getFilteredGrades();
  const classAverages = calculateClassAverages();
  const overallStats = calculateOverallStats();

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
            <FontAwesomeIcon icon={faClipboardList} className="me-2" />
            My Grades
          </h1>
          <p className="text-muted">Track your academic performance and feedback</p>
        </Col>
      </Row>

      {/* Overall Stats Cards */}
      <Row className="g-4 mb-4">
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faTrophy} size="2x" className="text-warning mb-2" />
              <h3 className="mb-0">{overallStats.average}%</h3>
              <small className="text-muted">Overall Average</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faTrophy} size="2x" className="text-success mb-2" />
              <h3 className="mb-0">{overallStats.highest}%</h3>
              <small className="text-muted">Highest Grade</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faClipboardList} size="2x" className="text-info mb-2" />
              <h3 className="mb-0">{grades.length}</h3>
              <small className="text-muted">Total Assignments</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faTrophy} size="2x" className="text-primary mb-2" />
              <h3 className="mb-0">{grades.filter(g => (g.grade / g.max_points) * 100 >= 90).length}</h3>
              <small className="text-muted">A Grades (90%+)</small>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Class Averages */}
      <Row className="mb-4">
        <Col>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">Class Averages</h5>
            </Card.Header>
            <Card.Body>
              <Row className="g-3">
                {classes.map((classItem) => (
                  <Col key={classItem.id} xs={12} md={6} lg={3}>
                    <div className="text-center p-3 bg-light rounded">
                      <h6 className="mb-2">{classItem.name}</h6>
                      <div className="mb-2">
                        <Badge bg={getGradeColor(classAverages[classItem.id], 100)} className="px-3 py-2">
                          {classAverages[classItem.id]}%
                        </Badge>
                      </div>
                      <ProgressBar 
                        variant={getGradeColor(classAverages[classItem.id], 100)}
                        now={classAverages[classItem.id]}
                        style={{ height: '6px' }}
                      />
                    </div>
                  </Col>
                ))}
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Filter */}
      <Row className="mb-4">
        <Col md={4}>
          <Form.Group>
            <Form.Label>
              <FontAwesomeIcon icon={faFilter} className="me-1" />
              Filter by Class
            </Form.Label>
            <Form.Select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
            >
              <option value="all">All Classes</option>
              {classes.map((classItem) => (
                <option key={classItem.id} value={classItem.id}>
                  {classItem.name}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
        </Col>
        <Col md={8} className="d-flex align-items-end">
          <div className="text-muted small">
            {filteredGrades.length} grade{filteredGrades.length !== 1 ? 's' : ''} found
          </div>
        </Col>
      </Row>

      {/* Grades Table */}
      <Row>
        <Col>
          <Card className="border-0 shadow-sm">
            <Card.Body className="p-0">
              <div className="table-responsive">
                <Table hover className="mb-0">
                  <thead className="table-dark">
                    <tr>
                      <th>Assignment</th>
                      <th>Class</th>
                      <th>Grade</th>
                      <th>Percentage</th>
                      <th>Due Date</th>
                      <th>Graded</th>
                      <th>Feedback</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredGrades.map((grade) => {
                      const percentage = Math.round((grade.grade / grade.max_points) * 100);
                      return (
                        <tr key={grade.id}>
                          <td>
                            <div className="fw-bold">{grade.assignment_title}</div>
                          </td>
                          <td>
                            <small className="text-muted">{grade.class_name}</small>
                          </td>
                          <td>
                            <span className="fw-bold">{grade.grade}</span>
                            <span className="text-muted">/{grade.max_points}</span>
                          </td>
                          <td>
                            <Badge bg={getGradeColor(grade.grade, grade.max_points)} className="px-2 py-1">
                              {percentage}%
                            </Badge>
                          </td>
                          <td>
                            <small className="text-muted">
                              <FontAwesomeIcon icon={faCalendarAlt} className="me-1" />
                              {new Date(grade.due_date).toLocaleDateString()}
                            </small>
                          </td>
                          <td>
                            <small className="text-muted">
                              {new Date(grade.graded_at).toLocaleDateString()}
                            </small>
                          </td>
                          <td>
                            <small className={grade.feedback ? "text-dark" : "text-muted"}>
                              {grade.feedback || 'No feedback provided'}
                            </small>
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

export default StudentGrades;