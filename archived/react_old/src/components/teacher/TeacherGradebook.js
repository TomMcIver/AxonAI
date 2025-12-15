import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Badge, Form, Button, Modal } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faClipboardList, faEdit, faSave, faFilter, faDownload } from '@fortawesome/free-solid-svg-icons';
import ApiService from '../../services/ApiService';

function TeacherGradebook({ user }) {
  const [gradebookData, setGradebookData] = useState({
    classes: [],
    students: [],
    assignments: [],
    grades: []
  });
  const [loading, setLoading] = useState(true);
  const [selectedClass, setSelectedClass] = useState('all');
  const [showGradeModal, setShowGradeModal] = useState(false);
  const [gradeToEdit, setGradeToEdit] = useState({
    student_id: null,
    assignment_id: null,
    grade: '',
    feedback: ''
  });

  useEffect(() => {
    fetchGradebookData();
  }, []);

  const fetchGradebookData = async () => {
    try {
      const response = await ApiService.getTeacherGradebook();
      setGradebookData(response.data);
    } catch (error) {
      console.error('Error fetching gradebook data:', error);
      // Set demo data if API fails
      setGradebookData({
        classes: [
          { id: 1, name: 'Mathematics 101' },
          { id: 2, name: 'Environmental Science' },
          { id: 3, name: 'Computer Science' }
        ],
        students: [
          { id: 1, first_name: 'Jane', last_name: 'Doe', class_ids: [1, 3] },
          { id: 2, first_name: 'Mike', last_name: 'Wilson', class_ids: [1] },
          { id: 3, first_name: 'Sarah', last_name: 'Brown', class_ids: [2] },
          { id: 4, first_name: 'Alex', last_name: 'Johnson', class_ids: [1, 2] },
          { id: 5, first_name: 'Emily', last_name: 'Davis', class_ids: [3] }
        ],
        assignments: [
          { id: 1, title: 'Quiz Chapter 5', class_id: 1, max_points: 100 },
          { id: 2, title: 'Homework Set 3', class_id: 1, max_points: 50 },
          { id: 3, title: 'Climate Essay', class_id: 2, max_points: 200 },
          { id: 4, title: 'Programming Project', class_id: 3, max_points: 150 }
        ],
        grades: [
          { student_id: 1, assignment_id: 1, grade: 92, feedback: 'Excellent work!' },
          { student_id: 1, assignment_id: 4, grade: 88, feedback: 'Good logic, minor bugs' },
          { student_id: 2, assignment_id: 1, grade: 85, feedback: 'Good understanding' },
          { student_id: 2, assignment_id: 2, grade: 90, feedback: 'Complete and accurate' },
          { student_id: 3, assignment_id: 3, grade: 95, feedback: 'Outstanding research' },
          { student_id: 4, assignment_id: 1, grade: 78, feedback: 'Needs improvement' },
          { student_id: 4, assignment_id: 3, grade: 82, feedback: 'Good effort' },
          { student_id: 5, assignment_id: 4, grade: 91, feedback: 'Creative solution' }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const getFilteredData = () => {
    if (selectedClass === 'all') {
      return gradebookData;
    }
    
    const classId = parseInt(selectedClass);
    return {
      ...gradebookData,
      students: gradebookData.students.filter(s => s.class_ids.includes(classId)),
      assignments: gradebookData.assignments.filter(a => a.class_id === classId)
    };
  };

  const getGrade = (studentId, assignmentId) => {
    const grade = gradebookData.grades.find(g => 
      g.student_id === studentId && g.assignment_id === assignmentId
    );
    return grade ? grade.grade : null;
  };

  const getGradeColor = (grade, maxPoints) => {
    if (!grade) return 'secondary';
    const percentage = (grade / maxPoints) * 100;
    if (percentage >= 90) return 'success';
    if (percentage >= 80) return 'info';
    if (percentage >= 70) return 'warning';
    return 'danger';
  };

  const handleGradeClick = (studentId, assignmentId) => {
    const existingGrade = gradebookData.grades.find(g => 
      g.student_id === studentId && g.assignment_id === assignmentId
    );
    
    setGradeToEdit({
      student_id: studentId,
      assignment_id: assignmentId,
      grade: existingGrade ? existingGrade.grade : '',
      feedback: existingGrade ? existingGrade.feedback : ''
    });
    setShowGradeModal(true);
  };

  const handleSaveGrade = async () => {
    try {
      // In a real app, this would call the API
      // await ApiService.gradeSubmission(submissionId, gradeToEdit);
      
      // Update local state for demo
      const updatedGrades = gradebookData.grades.filter(g => 
        !(g.student_id === gradeToEdit.student_id && g.assignment_id === gradeToEdit.assignment_id)
      );
      updatedGrades.push({
        student_id: gradeToEdit.student_id,
        assignment_id: gradeToEdit.assignment_id,
        grade: parseFloat(gradeToEdit.grade),
        feedback: gradeToEdit.feedback
      });
      
      setGradebookData({
        ...gradebookData,
        grades: updatedGrades
      });
      
      setShowGradeModal(false);
    } catch (error) {
      console.error('Error saving grade:', error);
    }
  };

  const calculateStats = () => {
    const filteredData = getFilteredData();
    const totalPossible = filteredData.students.length * filteredData.assignments.length;
    const totalGraded = gradebookData.grades.filter(g => 
      filteredData.students.some(s => s.id === g.student_id) &&
      filteredData.assignments.some(a => a.id === g.assignment_id)
    ).length;
    
    return {
      totalStudents: filteredData.students.length,
      totalAssignments: filteredData.assignments.length,
      totalGraded,
      pendingGrades: totalPossible - totalGraded
    };
  };

  const stats = calculateStats();
  const filteredData = getFilteredData();

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
                <FontAwesomeIcon icon={faClipboardList} className="me-2" />
                Gradebook
              </h1>
              <p className="text-muted">Grade assignments and track student progress</p>
            </div>
            <Button variant="outline-primary">
              <FontAwesomeIcon icon={faDownload} className="me-1" />
              Export Grades
            </Button>
          </div>
        </Col>
      </Row>

      {/* Stats Cards */}
      <Row className="g-4 mb-4">
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <h3 className="text-primary mb-0">{stats.totalStudents}</h3>
              <small className="text-muted">Students</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <h3 className="text-success mb-0">{stats.totalAssignments}</h3>
              <small className="text-muted">Assignments</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <h3 className="text-info mb-0">{stats.totalGraded}</h3>
              <small className="text-muted">Graded</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <h3 className="text-warning mb-0">{stats.pendingGrades}</h3>
              <small className="text-muted">Pending</small>
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
              {gradebookData.classes.map((classItem) => (
                <option key={classItem.id} value={classItem.id}>
                  {classItem.name}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
        </Col>
      </Row>

      {/* Gradebook Table */}
      <Row>
        <Col>
          <Card className="border-0 shadow-sm">
            <Card.Body className="p-0">
              <div className="table-responsive">
                <Table className="mb-0 gradebook-table">
                  <thead className="table-dark">
                    <tr>
                      <th className="sticky-column">Student Name</th>
                      {filteredData.assignments.map((assignment) => (
                        <th key={assignment.id} className="text-center min-width-100">
                          <div className="small">{assignment.title}</div>
                          <div className="text-muted" style={{fontSize: '0.75rem'}}>
                            ({assignment.max_points} pts)
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredData.students.map((student) => (
                      <tr key={student.id}>
                        <td className="sticky-column fw-bold">
                          {student.first_name} {student.last_name}
                        </td>
                        {filteredData.assignments.map((assignment) => {
                          const grade = getGrade(student.id, assignment.id);
                          return (
                            <td key={assignment.id} className="text-center">
                              <Button
                                variant={grade ? "outline-" + getGradeColor(grade, assignment.max_points) : "outline-secondary"}
                                size="sm"
                                onClick={() => handleGradeClick(student.id, assignment.id)}
                                style={{ minWidth: '60px' }}
                              >
                                {grade ? `${grade}/${assignment.max_points}` : '-'}
                              </Button>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Grade Modal */}
      <Modal show={showGradeModal} onHide={() => setShowGradeModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Grade Assignment</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Grade</Form.Label>
            <Form.Control
              type="number"
              value={gradeToEdit.grade}
              onChange={(e) => setGradeToEdit({...gradeToEdit, grade: e.target.value})}
              placeholder="Enter grade..."
            />
          </Form.Group>
          <Form.Group>
            <Form.Label>Feedback</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={gradeToEdit.feedback}
              onChange={(e) => setGradeToEdit({...gradeToEdit, feedback: e.target.value})}
              placeholder="Enter feedback for the student..."
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowGradeModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSaveGrade}>
            <FontAwesomeIcon icon={faSave} className="me-1" />
            Save Grade
          </Button>
        </Modal.Footer>
      </Modal>

      <style jsx>{`
        .gradebook-table .sticky-column {
          position: sticky;
          left: 0;
          background-color: white;
          z-index: 10;
          min-width: 150px;
        }
        .min-width-100 {
          min-width: 100px;
        }
        .table-dark .sticky-column {
          background-color: var(--bs-dark) !important;
        }
      `}</style>
    </Container>
  );
}

export default TeacherGradebook;