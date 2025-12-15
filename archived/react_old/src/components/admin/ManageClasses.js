import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Button, Modal, Form, Alert, Badge } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faEdit, faTrash, faChalkboardTeacher, faUsers, faCalendarAlt } from '@fortawesome/free-solid-svg-icons';
import ApiService from '../../services/ApiService';

function ManageClasses() {
  const [classes, setClasses] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingClass, setEditingClass] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    teacher_id: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [classesResponse, usersResponse] = await Promise.all([
        ApiService.getClasses(),
        ApiService.getUsers()
      ]);
      
      setClasses(classesResponse.data);
      setTeachers(usersResponse.data.filter(user => user.role === 'teacher'));
    } catch (error) {
      console.error('Error fetching data:', error);
      // Set demo data if API fails
      setClasses([
        {
          id: 1,
          name: 'Mathematics 101',
          description: 'Introduction to Algebra and Geometry',
          teacher_name: 'John Smith',
          teacher_id: 2,
          student_count: 25,
          created_at: '2025-01-01',
          is_active: true
        },
        {
          id: 2,
          name: 'Environmental Science',
          description: 'Study of environmental systems and sustainability',
          teacher_name: 'Sarah Johnson',
          teacher_id: 4,
          student_count: 18,
          created_at: '2025-01-01',
          is_active: true
        },
        {
          id: 3,
          name: 'Computer Science Fundamentals',
          description: 'Introduction to programming and computer systems',
          teacher_name: 'John Smith',
          teacher_id: 2,
          student_count: 22,
          created_at: '2025-01-01',
          is_active: false
        }
      ]);
      
      setTeachers([
        { id: 2, first_name: 'John', last_name: 'Smith', email: 'teacher@teacher.com' },
        { id: 4, first_name: 'Sarah', last_name: 'Johnson', email: 'teacher2@school.com' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      if (editingClass) {
        await ApiService.updateClass(editingClass.id, formData);
        setSuccess('Class updated successfully!');
      } else {
        await ApiService.createClass(formData);
        setSuccess('Class created successfully!');
      }
      
      fetchData();
      setShowModal(false);
      resetForm();
    } catch (error) {
      setError(error.response?.data?.message || 'Operation failed');
    }
  };

  const handleEdit = (classItem) => {
    setEditingClass(classItem);
    setFormData({
      name: classItem.name,
      description: classItem.description,
      teacher_id: classItem.teacher_id
    });
    setShowModal(true);
  };

  const handleDelete = async (classId) => {
    if (window.confirm('Are you sure you want to delete this class?')) {
      try {
        await ApiService.deleteClass(classId);
        setSuccess('Class deleted successfully!');
        fetchData();
      } catch (error) {
        setError(error.response?.data?.message || 'Delete failed');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      teacher_id: ''
    });
    setEditingClass(null);
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
                Manage Classes
              </h1>
              <p className="text-muted">Create and organize classes</p>
            </div>
            <Button 
              variant="primary" 
              onClick={() => {
                resetForm();
                setShowModal(true);
              }}
            >
              <FontAwesomeIcon icon={faPlus} className="me-2" />
              Add New Class
            </Button>
          </div>
        </Col>
      </Row>

      {error && <Alert variant="danger" className="fade-in">{error}</Alert>}
      {success && <Alert variant="success" className="fade-in">{success}</Alert>}

      <Row>
        <Col>
          <Card className="border-0 shadow-sm">
            <Card.Body className="p-0">
              <div className="table-responsive">
                <Table striped hover className="mb-0">
                  <thead className="table-dark">
                    <tr>
                      <th>Class Name</th>
                      <th>Teacher</th>
                      <th>Students</th>
                      <th>Created</th>
                      <th>Status</th>
                      <th className="text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {classes.map((classItem) => (
                      <tr key={classItem.id}>
                        <td>
                          <div>
                            <div className="fw-bold">{classItem.name}</div>
                            <small className="text-muted">{classItem.description}</small>
                          </div>
                        </td>
                        <td>
                          <FontAwesomeIcon icon={faChalkboardTeacher} className="me-2 text-warning" />
                          {classItem.teacher_name || 'Not Assigned'}
                        </td>
                        <td>
                          <FontAwesomeIcon icon={faUsers} className="me-2 text-info" />
                          {classItem.student_count || 0} students
                        </td>
                        <td>
                          <FontAwesomeIcon icon={faCalendarAlt} className="me-2 text-muted" />
                          {new Date(classItem.created_at).toLocaleDateString()}
                        </td>
                        <td>
                          <Badge bg={classItem.is_active ? 'success' : 'danger'}>
                            {classItem.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </td>
                        <td className="text-center">
                          <Button
                            variant="outline-primary"
                            size="sm"
                            className="me-2"
                            onClick={() => handleEdit(classItem)}
                          >
                            <FontAwesomeIcon icon={faEdit} />
                          </Button>
                          <Button
                            variant="outline-danger"
                            size="sm"
                            onClick={() => handleDelete(classItem.id)}
                          >
                            <FontAwesomeIcon icon={faTrash} />
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

      {/* Add/Edit Class Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            {editingClass ? 'Edit Class' : 'Add New Class'}
          </Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleSubmit}>
          <Modal.Body>
            <Row className="g-3">
              <Col md={12}>
                <Form.Group>
                  <Form.Label>Class Name</Form.Label>
                  <Form.Control
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="e.g., Mathematics 101"
                    required
                  />
                </Form.Group>
              </Col>
              <Col md={12}>
                <Form.Group>
                  <Form.Label>Description</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={3}
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    placeholder="Brief description of the class content and objectives..."
                  />
                </Form.Group>
              </Col>
              <Col md={12}>
                <Form.Group>
                  <Form.Label>Assign Teacher</Form.Label>
                  <Form.Select
                    value={formData.teacher_id}
                    onChange={(e) => setFormData({...formData, teacher_id: e.target.value})}
                    required
                  >
                    <option value="">Select a teacher...</option>
                    {teachers.map((teacher) => (
                      <option key={teacher.id} value={teacher.id}>
                        {teacher.first_name} {teacher.last_name} ({teacher.email})
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              {editingClass ? 'Update Class' : 'Create Class'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </Container>
  );
}

export default ManageClasses;