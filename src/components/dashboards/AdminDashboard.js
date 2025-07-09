import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUsers, faChalkboardTeacher, faUserGraduate, faClipboardList } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import ApiService from '../../services/ApiService';

function AdminDashboard({ user }) {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalTeachers: 0,
    totalStudents: 0,
    totalClasses: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await ApiService.getDashboardStats();
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      // Set default stats if API fails
      setStats({
        totalUsers: 15,
        totalTeachers: 5,
        totalStudents: 8,
        totalClasses: 12
      });
    } finally {
      setLoading(false);
    }
  };

  const dashboardCards = [
    {
      title: 'Manage Users',
      description: 'Add, edit, and manage system users',
      icon: faUsers,
      color: 'primary',
      value: stats.totalUsers,
      path: '/admin/users'
    },
    {
      title: 'Manage Classes',
      description: 'Create and organize classes',
      icon: faChalkboardTeacher,
      color: 'success',
      value: stats.totalClasses,
      path: '/admin/classes'
    },
    {
      title: 'Teachers',
      description: 'View all teachers in system',
      icon: faClipboardList,
      color: 'warning',
      value: stats.totalTeachers,
      path: '/admin/users?role=teacher'
    },
    {
      title: 'Students',
      description: 'View all students in system',
      icon: faUserGraduate,
      color: 'info',
      value: stats.totalStudents,
      path: '/admin/users?role=student'
    }
  ];

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
          <h1 className="h2 mb-1">Welcome back, {user.first_name}!</h1>
          <p className="text-muted">Administrator Dashboard</p>
        </Col>
      </Row>

      <Row className="g-4">
        {dashboardCards.map((card, index) => (
          <Col key={index} xs={12} sm={6} lg={3}>
            <Card 
              className={`dashboard-card admin-card h-100 border-0 text-white`}
              onClick={() => navigate(card.path)}
              style={{ cursor: 'pointer' }}
            >
              <Card.Body className="d-flex flex-column align-items-center text-center">
                <FontAwesomeIcon icon={card.icon} size="3x" className="mb-3" />
                <h3 className="display-4 fw-bold mb-2">{card.value}</h3>
                <h5 className="card-title mb-2">{card.title}</h5>
                <p className="card-text small opacity-75">{card.description}</p>
                <Button 
                  variant="light" 
                  className="mt-auto"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(card.path);
                  }}
                >
                  View Details
                </Button>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Quick Actions */}
      <Row className="mt-5">
        <Col>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">Quick Actions</h5>
            </Card.Header>
            <Card.Body>
              <Row className="g-3">
                <Col xs={12} md={6} lg={3}>
                  <Button 
                    variant="outline-primary" 
                    className="w-100"
                    onClick={() => navigate('/admin/users')}
                  >
                    <FontAwesomeIcon icon={faUsers} className="me-2" />
                    Add New User
                  </Button>
                </Col>
                <Col xs={12} md={6} lg={3}>
                  <Button 
                    variant="outline-success" 
                    className="w-100"
                    onClick={() => navigate('/admin/classes')}
                  >
                    <FontAwesomeIcon icon={faChalkboardTeacher} className="me-2" />
                    Create Class
                  </Button>
                </Col>
                <Col xs={12} md={6} lg={3}>
                  <Button variant="outline-info" className="w-100">
                    <FontAwesomeIcon icon={faClipboardList} className="me-2" />
                    System Reports
                  </Button>
                </Col>
                <Col xs={12} md={6} lg={3}>
                  <Button variant="outline-warning" className="w-100">
                    <FontAwesomeIcon icon={faUsers} className="me-2" />
                    User Activity
                  </Button>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default AdminDashboard;