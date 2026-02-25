import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Tab, Tabs } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faGraduationCap, faUsers, faChalkboardTeacher, faBookOpen } from '@fortawesome/free-solid-svg-icons';
import AuthService from '../services/AuthService';

function Login({ onLogin }) {
  const [activeTab, setActiveTab] = useState('admin');
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await AuthService.login(formData.email, formData.password, activeTab);
      onLogin(response.user);
    } catch (error) {
      setError(error.response?.data?.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoCredentials = (role) => {
    const credentials = {
      admin: { email: 'admin@admin.com', password: 'admin123' },
      teacher: { email: 'teacher@teacher.com', password: 'teacher123' },
      student: { email: 'student@student.com', password: 'student123' },
      parent: { email: 'parent@parent.com', password: 'parent123' }
    };
    
    setFormData(credentials[role]);
    setActiveTab(role);
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'admin': return faUsers;
      case 'teacher': return faChalkboardTeacher;
      case 'student': return faBookOpen;
      case 'parent': return faGraduationCap;
      default: return faUsers;
    }
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin': return 'primary';
      case 'teacher': return 'warning';
      case 'student': return 'info';
      case 'parent': return 'success';
      default: return 'primary';
    }
  };

  return (
    <Container fluid className="min-vh-100 d-flex align-items-center justify-content-center bg-gradient">
      <Row className="w-100 justify-content-center">
        <Col xs={12} sm={10} md={8} lg={6} xl={5}>
          <div className="text-center mb-4">
            <FontAwesomeIcon icon={faGraduationCap} size="3x" className="text-primary mb-3" />
            <h2 className="fw-bold">TMC Learning</h2>
            <p className="text-muted">Please select your role and sign in</p>
          </div>
          
          <Card className="login-card shadow-lg">
            <Card.Body className="p-4">
              <Tabs
                activeKey={activeTab}
                onSelect={(k) => setActiveTab(k)}
                className="mb-4"
                justify
              >
                <Tab 
                  eventKey="admin" 
                  title={
                    <span className={`text-${getRoleColor('admin')}`}>
                      <FontAwesomeIcon icon={getRoleIcon('admin')} className="me-1" />
                      Admin
                    </span>
                  }
                />
                <Tab 
                  eventKey="teacher" 
                  title={
                    <span className={`text-${getRoleColor('teacher')}`}>
                      <FontAwesomeIcon icon={getRoleIcon('teacher')} className="me-1" />
                      Teacher
                    </span>
                  }
                />
                <Tab
                  eventKey="student"
                  title={
                    <span className={`text-${getRoleColor('student')}`}>
                      <FontAwesomeIcon icon={getRoleIcon('student')} className="me-1" />
                      Student
                    </span>
                  }
                />
                <Tab
                  eventKey="parent"
                  title={
                    <span className={`text-${getRoleColor('parent')}`}>
                      <FontAwesomeIcon icon={getRoleIcon('parent')} className="me-1" />
                      Parent
                    </span>
                  }
                />
              </Tabs>

              {error && (
                <Alert variant="danger" className="fade-in">
                  {error}
                </Alert>
              )}

              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Email Address</Form.Label>
                  <Form.Control
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="Enter your email"
                    required
                    size="lg"
                  />
                </Form.Group>

                <Form.Group className="mb-4">
                  <Form.Label>Password</Form.Label>
                  <Form.Control
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Enter your password"
                    required
                    size="lg"
                  />
                </Form.Group>

                <Button
                  type="submit"
                  variant={getRoleColor(activeTab)}
                  size="lg"
                  className="w-100 btn-login mb-3"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Signing in...
                    </>
                  ) : (
                    <>
                      <FontAwesomeIcon icon={getRoleIcon(activeTab)} className="me-2" />
                      Sign in as {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
                    </>
                  )}
                </Button>
              </Form>

              {/* Demo credentials */}
              <div className="text-center">
                <small className="text-muted d-block mb-2">Demo Credentials:</small>
                <div className="d-flex gap-2 justify-content-center flex-wrap">
                  <Button
                    variant="outline-primary"
                    size="sm"
                    onClick={() => fillDemoCredentials('admin')}
                  >
                    Admin Demo
                  </Button>
                  <Button
                    variant="outline-warning"
                    size="sm"
                    onClick={() => fillDemoCredentials('teacher')}
                  >
                    Teacher Demo
                  </Button>
                  <Button
                    variant="outline-info"
                    size="sm"
                    onClick={() => fillDemoCredentials('student')}
                  >
                    Student Demo
                  </Button>
                  <Button
                    variant="outline-success"
                    size="sm"
                    onClick={() => fillDemoCredentials('parent')}
                  >
                    Parent Demo
                  </Button>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default Login;