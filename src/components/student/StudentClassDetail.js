import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Button, Badge, Tab, Tabs, ListGroup } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBookOpen, faTasks, faUpload, faDownload, faCalendarAlt, faUser, faFilePdf, faFileWord, faFileImage } from '@fortawesome/free-solid-svg-icons';
import { useParams, useNavigate } from 'react-router-dom';
import ApiService from '../../services/ApiService';

function StudentClassDetail({ user }) {
  const { classId } = useParams();
  const navigate = useNavigate();
  const [classData, setClassData] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [contentFiles, setContentFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClassData();
  }, [classId]);

  const fetchClassData = async () => {
    try {
      const response = await ApiService.getClassById(classId);
      setClassData(response.data);
      setAssignments(response.data.assignments || []);
      setContentFiles(response.data.content_files || []);
    } catch (error) {
      console.error('Error fetching class data:', error);
      // Set demo data if API fails
      setClassData({
        id: classId,
        name: 'Mathematics 101',
        description: 'Introduction to Algebra and Geometry',
        teacher_name: 'John Smith',
        teacher_email: 'john.smith@school.com',
        current_grade: 92.5
      });
      
      setAssignments([
        {
          id: 1,
          title: 'Quiz Chapter 5',
          description: 'Test your understanding of algebraic concepts',
          due_date: '2025-01-15',
          max_points: 100,
          submitted: true,
          grade: 95,
          feedback: 'Excellent work!'
        },
        {
          id: 2,
          title: 'Homework Set 3',
          description: 'Practice problems for geometric proofs',
          due_date: '2025-01-18',
          max_points: 50,
          submitted: true,
          grade: 90,
          feedback: 'Good work on most problems.'
        },
        {
          id: 3,
          title: 'Quiz Chapter 6',
          description: 'Advanced algebraic functions',
          due_date: '2025-01-20',
          max_points: 100,
          submitted: false,
          grade: null,
          feedback: null
        },
        {
          id: 4,
          title: 'Midterm Project',
          description: 'Comprehensive project covering first half of semester',
          due_date: '2025-01-25',
          max_points: 200,
          submitted: false,
          grade: null,
          feedback: null
        }
      ]);
      
      setContentFiles([
        {
          id: 1,
          name: 'Chapter 5 - Algebraic Functions',
          file_type: 'pdf',
          file_path: '/content/math_chapter5.pdf',
          uploaded_at: '2025-01-08',
          file_size: '2.3 MB'
        },
        {
          id: 2,
          name: 'Homework Assignment Template',
          file_type: 'word',
          file_path: '/content/hw_template.docx',
          uploaded_at: '2025-01-10',
          file_size: '156 KB'
        },
        {
          id: 3,
          name: 'Function Graphs Examples',
          file_type: 'image',
          file_path: '/content/function_graphs.png',
          uploaded_at: '2025-01-12',
          file_size: '890 KB'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getFileIcon = (fileType) => {
    switch (fileType) {
      case 'pdf': return faFilePdf;
      case 'word': case 'doc': case 'docx': return faFileWord;
      case 'image': case 'jpg': case 'jpeg': case 'png': return faFileImage;
      default: return faDownload;
    }
  };

  const getFileTypeColor = (fileType) => {
    switch (fileType) {
      case 'pdf': return 'danger';
      case 'word': case 'doc': case 'docx': return 'primary';
      case 'slides': case 'ppt': case 'pptx': return 'warning';
      case 'image': case 'jpg': case 'jpeg': case 'png': return 'success';
      default: return 'secondary';
    }
  };

  const getGradeColor = (grade, maxPoints) => {
    if (!grade) return 'secondary';
    const percentage = (grade / maxPoints) * 100;
    if (percentage >= 90) return 'success';
    if (percentage >= 80) return 'info';
    if (percentage >= 70) return 'warning';
    return 'danger';
  };

  const getAssignmentStatus = (assignment) => {
    if (assignment.submitted && assignment.grade !== null) {
      return { text: 'Graded', variant: 'success' };
    } else if (assignment.submitted) {
      return { text: 'Submitted', variant: 'info' };
    } else if (new Date(assignment.due_date) < new Date()) {
      return { text: 'Overdue', variant: 'danger' };
    } else {
      return { text: 'Pending', variant: 'warning' };
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
                <FontAwesomeIcon icon={faBookOpen} className="me-2" />
                {classData.name}
              </h1>
              <p className="text-muted">{classData.description}</p>
            </div>
            <div className="text-end">
              <div className="d-flex align-items-center mb-2">
                <FontAwesomeIcon icon={faUser} className="me-2 text-muted" />
                <div>
                  <div className="fw-bold">{classData.teacher_name}</div>
                  <small className="text-muted">{classData.teacher_email}</small>
                </div>
              </div>
            </div>
          </div>
        </Col>
      </Row>

      {/* Class Overview Cards */}
      <Row className="g-4 mb-4">
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faTasks} size="2x" className="text-primary mb-2" />
              <h3 className="mb-0">{assignments.length}</h3>
              <small className="text-muted">Total Assignments</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faTasks} size="2x" className="text-success mb-2" />
              <h3 className="mb-0">{assignments.filter(a => a.submitted).length}</h3>
              <small className="text-muted">Submitted</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faTasks} size="2x" className="text-warning mb-2" />
              <h3 className="mb-0">{assignments.filter(a => !a.submitted).length}</h3>
              <small className="text-muted">Pending</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faTasks} size="2x" className="text-info mb-2" />
              <h3 className="mb-0">{classData.current_grade}%</h3>
              <small className="text-muted">Current Grade</small>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Tabs for different views */}
      <Tabs defaultActiveKey="assignments" className="mb-4">
        <Tab eventKey="assignments" title="Assignments">
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">Class Assignments</h5>
            </Card.Header>
            <Card.Body className="p-0">
              <div className="table-responsive">
                <Table hover className="mb-0">
                  <thead className="table-dark">
                    <tr>
                      <th>Assignment</th>
                      <th>Due Date</th>
                      <th>Points</th>
                      <th>Status</th>
                      <th>Grade</th>
                      <th className="text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignments.map((assignment) => {
                      const status = getAssignmentStatus(assignment);
                      return (
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
                          <td>
                            <Badge bg={status.variant}>
                              {status.text}
                            </Badge>
                          </td>
                          <td>
                            {assignment.grade !== null ? (
                              <Badge bg={getGradeColor(assignment.grade, assignment.max_points)}>
                                {assignment.grade}/{assignment.max_points}
                              </Badge>
                            ) : (
                              <span className="text-muted">-</span>
                            )}
                          </td>
                          <td className="text-center">
                            {!assignment.submitted && (
                              <Button 
                                variant="primary" 
                                size="sm"
                                onClick={() => navigate(`/student/assignment/${assignment.id}/submit`)}
                              >
                                <FontAwesomeIcon icon={faUpload} className="me-1" />
                                Submit
                              </Button>
                            )}
                            {assignment.submitted && (
                              <Button variant="outline-info" size="sm">
                                <FontAwesomeIcon icon={faDownload} />
                              </Button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </Table>
              </div>
            </Card.Body>
          </Card>
        </Tab>

        <Tab eventKey="materials" title="Course Materials">
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">Course Materials</h5>
            </Card.Header>
            <Card.Body>
              {contentFiles.length > 0 ? (
                <Row className="g-3">
                  {contentFiles.map((file) => (
                    <Col key={file.id} xs={12} md={6} lg={4}>
                      <Card className="h-100 border">
                        <Card.Body className="text-center">
                          <FontAwesomeIcon 
                            icon={getFileIcon(file.file_type)} 
                            size="3x" 
                            className={`mb-3 text-${getFileTypeColor(file.file_type)}`}
                          />
                          <h6 className="card-title">{file.name}</h6>
                          <div className="mb-2">
                            <Badge bg={getFileTypeColor(file.file_type)}>
                              {file.file_type.toUpperCase()}
                            </Badge>
                          </div>
                          <small className="text-muted d-block mb-3">
                            {file.file_size} • {new Date(file.uploaded_at).toLocaleDateString()}
                          </small>
                          <Button variant="outline-primary" size="sm" className="w-100">
                            <FontAwesomeIcon icon={faDownload} className="me-1" />
                            Download
                          </Button>
                        </Card.Body>
                      </Card>
                    </Col>
                  ))}
                </Row>
              ) : (
                <div className="text-center py-5">
                  <FontAwesomeIcon icon={faDownload} size="3x" className="text-muted mb-3" />
                  <h5 className="text-muted">No course materials available</h5>
                  <p className="text-muted">Your teacher hasn't uploaded any materials yet.</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Tab>

        <Tab eventKey="grades" title="My Grades">
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">Grade Summary</h5>
            </Card.Header>
            <Card.Body>
              <ListGroup variant="flush">
                {assignments.filter(a => a.grade !== null).map((assignment) => (
                  <ListGroup.Item key={assignment.id} className="d-flex justify-content-between align-items-start">
                    <div className="ms-2 me-auto">
                      <div className="fw-bold">{assignment.title}</div>
                      <small className="text-muted">{assignment.feedback}</small>
                    </div>
                    <div className="text-end">
                      <Badge bg={getGradeColor(assignment.grade, assignment.max_points)} className="mb-1">
                        {assignment.grade}/{assignment.max_points}
                      </Badge>
                      <div>
                        <small className="text-muted">
                          {Math.round((assignment.grade / assignment.max_points) * 100)}%
                        </small>
                      </div>
                    </div>
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </Card.Body>
          </Card>
        </Tab>
      </Tabs>
    </Container>
  );
}

export default StudentClassDetail;