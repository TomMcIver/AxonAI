import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, ProgressBar } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUpload, faSave, faArrowLeft, faFile, faTrash } from '@fortawesome/free-solid-svg-icons';
import { useParams, useNavigate } from 'react-router-dom';
import ApiService from '../../services/ApiService';

function SubmitAssignment({ user }) {
  const { assignmentId } = useParams();
  const navigate = useNavigate();
  const [assignment, setAssignment] = useState(null);
  const [formData, setFormData] = useState({
    content: '',
    file: null
  });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    fetchAssignment();
  }, [assignmentId]);

  const fetchAssignment = async () => {
    try {
      // const response = await ApiService.getAssignmentById(assignmentId);
      // setAssignment(response.data);
      
      // Demo data
      setAssignment({
        id: assignmentId,
        title: 'Quiz Chapter 6',
        description: 'Complete the quiz on advanced algebraic functions. Show all work and provide clear explanations for each answer.',
        due_date: '2025-01-20T23:59:00',
        max_points: 100,
        class_name: 'Mathematics 101',
        class_id: 1,
        instructions: 'Please submit your answers in a clear format. You may upload a PDF, Word document, or image file. Make sure all work is legible and well-organized.',
        submission_format: 'PDF, DOC, DOCX, JPG, PNG'
      });
    } catch (error) {
      console.error('Error fetching assignment:', error);
      setError('Failed to load assignment details');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    setSuccess('');

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 200);

    try {
      await ApiService.submitAssignment(assignmentId, formData);
      setUploadProgress(100);
      setSuccess('Assignment submitted successfully!');
      
      setTimeout(() => {
        navigate(`/student/class/${assignment.class_id}`);
      }, 2000);
    } catch (error) {
      clearInterval(progressInterval);
      setUploadProgress(0);
      setError(error.response?.data?.message || 'Failed to submit assignment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Check file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }
      
      // Check file type
      const allowedTypes = ['application/pdf', 'application/msword', 
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                           'image/jpeg', 'image/jpg', 'image/png'];
      
      if (!allowedTypes.includes(file.type)) {
        setError('Invalid file type. Please upload PDF, DOC, DOCX, JPG, or PNG files only.');
        return;
      }
      
      setFormData({ ...formData, file });
      setError('');
    }
  };

  const removeFile = () => {
    setFormData({ ...formData, file: null });
    // Reset file input
    document.getElementById('fileInput').value = '';
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const isOverdue = () => {
    return new Date() > new Date(assignment?.due_date);
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

  if (!assignment) {
    return (
      <Container className="py-4">
        <Alert variant="danger">Assignment not found.</Alert>
      </Container>
    );
  }

  return (
    <Container fluid className="py-4">
      <Row className="mb-4">
        <Col>
          <div className="d-flex align-items-center">
            <Button 
              variant="outline-secondary" 
              className="me-3"
              onClick={() => navigate(`/student/class/${assignment.class_id}`)}
            >
              <FontAwesomeIcon icon={faArrowLeft} />
            </Button>
            <div>
              <h1 className="h2 mb-1">
                <FontAwesomeIcon icon={faUpload} className="me-2" />
                Submit Assignment
              </h1>
              <p className="text-muted">{assignment.class_name}</p>
            </div>
          </div>
        </Col>
      </Row>

      {error && <Alert variant="danger" className="fade-in">{error}</Alert>}
      {success && <Alert variant="success" className="fade-in">{success}</Alert>}

      {isOverdue() && (
        <Alert variant="warning" className="fade-in">
          <strong>Warning:</strong> This assignment is overdue. Late submissions may be penalized.
        </Alert>
      )}

      <Row className="justify-content-center">
        <Col xs={12} lg={8} xl={6}>
          {/* Assignment Details */}
          <Card className="mb-4 border-0 shadow-sm">
            <Card.Header className="bg-primary text-white">
              <h5 className="mb-0">{assignment.title}</h5>
            </Card.Header>
            <Card.Body>
              <div className="mb-3">
                <h6>Description:</h6>
                <p className="text-muted">{assignment.description}</p>
              </div>
              
              <div className="mb-3">
                <h6>Instructions:</h6>
                <p className="text-muted">{assignment.instructions}</p>
              </div>
              
              <Row className="text-center">
                <Col xs={6} md={3}>
                  <div className="border-end">
                    <strong className="text-primary">{assignment.max_points}</strong>
                    <div className="small text-muted">Points</div>
                  </div>
                </Col>
                <Col xs={6} md={3}>
                  <div className="border-end">
                    <strong className={isOverdue() ? 'text-danger' : 'text-success'}>
                      {new Date(assignment.due_date).toLocaleDateString()}
                    </strong>
                    <div className="small text-muted">Due Date</div>
                  </div>
                </Col>
                <Col xs={6} md={3}>
                  <div className="border-end">
                    <strong className="text-info">
                      {new Date(assignment.due_date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </strong>
                    <div className="small text-muted">Due Time</div>
                  </div>
                </Col>
                <Col xs={6} md={3}>
                  <div>
                    <strong className="text-secondary">Multiple</strong>
                    <div className="small text-muted">Formats</div>
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>

          {/* Submission Form */}
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">Your Submission</h5>
            </Card.Header>
            <Card.Body>
              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-4">
                  <Form.Label>Written Response (Optional)</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={6}
                    value={formData.content}
                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    placeholder="Type your response here, or upload a file below..."
                  />
                  <Form.Text className="text-muted">
                    You can provide written answers here or upload a file with your work.
                  </Form.Text>
                </Form.Group>

                <Form.Group className="mb-4">
                  <Form.Label>Upload File</Form.Label>
                  <div className="file-drop-zone">
                    <FontAwesomeIcon icon={faUpload} size="2x" className="mb-3" />
                    <h6>Drag & Drop Your File Here</h6>
                    <p className="text-muted mb-3">or click to select a file</p>
                    <Form.Control
                      id="fileInput"
                      type="file"
                      onChange={handleFileChange}
                      accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                      className="mb-2"
                    />
                    <small className="text-muted">
                      Accepted formats: {assignment.submission_format} (Max 10MB)
                    </small>
                  </div>
                </Form.Group>

                {/* File Preview */}
                {formData.file && (
                  <Card className="mb-4 border">
                    <Card.Body className="py-3">
                      <div className="d-flex justify-content-between align-items-center">
                        <div className="d-flex align-items-center">
                          <FontAwesomeIcon icon={faFile} className="me-2 text-primary" />
                          <div>
                            <div className="fw-bold">{formData.file.name}</div>
                            <small className="text-muted">{formatFileSize(formData.file.size)}</small>
                          </div>
                        </div>
                        <Button 
                          variant="outline-danger" 
                          size="sm"
                          onClick={removeFile}
                        >
                          <FontAwesomeIcon icon={faTrash} />
                        </Button>
                      </div>
                    </Card.Body>
                  </Card>
                )}

                {/* Upload Progress */}
                {submitting && uploadProgress > 0 && (
                  <div className="mb-4">
                    <div className="d-flex justify-content-between mb-1">
                      <span>Uploading...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <ProgressBar 
                      now={uploadProgress} 
                      variant={uploadProgress === 100 ? 'success' : 'primary'}
                      animated={uploadProgress < 100}
                    />
                  </div>
                )}

                {/* Submit Buttons */}
                <div className="d-flex justify-content-end gap-2">
                  <Button 
                    variant="outline-secondary" 
                    onClick={() => navigate(`/student/class/${assignment.class_id}`)}
                    disabled={submitting}
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="submit" 
                    variant="primary"
                    disabled={submitting || (!formData.content.trim() && !formData.file)}
                  >
                    {submitting ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Submitting...
                      </>
                    ) : (
                      <>
                        <FontAwesomeIcon icon={faSave} className="me-2" />
                        Submit Assignment
                      </>
                    )}
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default SubmitAssignment;