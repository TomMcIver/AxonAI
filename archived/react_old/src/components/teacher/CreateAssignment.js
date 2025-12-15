import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTasks, faSave, faArrowLeft } from '@fortawesome/free-solid-svg-icons';
import { useParams, useNavigate } from 'react-router-dom';
import ApiService from '../../services/ApiService';

function CreateAssignment({ user }) {
  const { classId } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    due_date: '',
    max_points: 100
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await ApiService.createAssignment(classId, formData);
      setSuccess('Assignment created successfully!');
      setTimeout(() => {
        navigate(`/teacher/class/${classId}`);
      }, 2000);
    } catch (error) {
      setError(error.response?.data?.message || 'Failed to create assignment');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <Container fluid className="py-4">
      <Row className="mb-4">
        <Col>
          <div className="d-flex align-items-center">
            <Button 
              variant="outline-secondary" 
              className="me-3"
              onClick={() => navigate(`/teacher/class/${classId}`)}
            >
              <FontAwesomeIcon icon={faArrowLeft} />
            </Button>
            <div>
              <h1 className="h2 mb-1">
                <FontAwesomeIcon icon={faTasks} className="me-2" />
                Create New Assignment
              </h1>
              <p className="text-muted">Add a new assignment for your class</p>
            </div>
          </div>
        </Col>
      </Row>

      {error && <Alert variant="danger" className="fade-in">{error}</Alert>}
      {success && <Alert variant="success" className="fade-in">{success}</Alert>}

      <Row className="justify-content-center">
        <Col xs={12} lg={8} xl={6}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-primary text-white">
              <h5 className="mb-0">Assignment Details</h5>
            </Card.Header>
            <Card.Body>
              <Form onSubmit={handleSubmit}>
                <Row className="g-3">
                  <Col xs={12}>
                    <Form.Group>
                      <Form.Label>Assignment Title *</Form.Label>
                      <Form.Control
                        type="text"
                        name="title"
                        value={formData.title}
                        onChange={handleChange}
                        placeholder="e.g., Math Quiz Chapter 5"
                        required
                      />
                    </Form.Group>
                  </Col>

                  <Col xs={12}>
                    <Form.Group>
                      <Form.Label>Description</Form.Label>
                      <Form.Control
                        as="textarea"
                        rows={4}
                        name="description"
                        value={formData.description}
                        onChange={handleChange}
                        placeholder="Describe the assignment objectives, requirements, and any special instructions..."
                      />
                    </Form.Group>
                  </Col>

                  <Col xs={12} md={6}>
                    <Form.Group>
                      <Form.Label>Due Date *</Form.Label>
                      <Form.Control
                        type="datetime-local"
                        name="due_date"
                        value={formData.due_date}
                        onChange={handleChange}
                        required
                      />
                    </Form.Group>
                  </Col>

                  <Col xs={12} md={6}>
                    <Form.Group>
                      <Form.Label>Maximum Points *</Form.Label>
                      <Form.Control
                        type="number"
                        name="max_points"
                        value={formData.max_points}
                        onChange={handleChange}
                        min="1"
                        max="1000"
                        required
                      />
                    </Form.Group>
                  </Col>

                  <Col xs={12}>
                    <Form.Group>
                      <Form.Label>Assignment Type</Form.Label>
                      <Form.Select name="assignment_type" onChange={handleChange}>
                        <option value="homework">Homework</option>
                        <option value="quiz">Quiz</option>
                        <option value="exam">Exam</option>
                        <option value="project">Project</option>
                        <option value="lab">Lab Report</option>
                        <option value="essay">Essay</option>
                      </Form.Select>
                    </Form.Group>
                  </Col>

                  <Col xs={12}>
                    <div className="bg-light p-3 rounded">
                      <h6 className="mb-2">Assignment Guidelines</h6>
                      <ul className="mb-0 small text-muted">
                        <li>Clearly state learning objectives and expectations</li>
                        <li>Include rubric or grading criteria if applicable</li>
                        <li>Specify submission format (PDF, Word, handwritten, etc.)</li>
                        <li>Mention any required resources or materials</li>
                        <li>Set realistic deadlines considering student workload</li>
                      </ul>
                    </div>
                  </Col>
                </Row>

                <div className="d-flex justify-content-end gap-2 mt-4">
                  <Button 
                    variant="outline-secondary" 
                    onClick={() => navigate(`/teacher/class/${classId}`)}
                    disabled={loading}
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="submit" 
                    variant="primary"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Creating...
                      </>
                    ) : (
                      <>
                        <FontAwesomeIcon icon={faSave} className="me-2" />
                        Create Assignment
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

export default CreateAssignment;