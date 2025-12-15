import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, ListGroup, ProgressBar, Modal } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBookOpen, faClipboardList, faTrophy, faCalendarAlt, faTasks, faExclamationTriangle, faRobot, faComments } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import ApiService from '../../services/ApiService';
import ChatBot from '../shared/ChatBot';

function StudentDashboard({ user }) {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalClasses: 0,
    overallGrade: 0,
    pendingAssignments: 0,
    upcomingDeadlines: [],
    chatInteractions: 0
  });
  const [loading, setLoading] = useState(true);
  const [classes, setClasses] = useState([]);
  const [showChatBot, setShowChatBot] = useState(false);
  const [selectedClass, setSelectedClass] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [classesResponse, gradesResponse, dashboardResponse] = await Promise.all([
        ApiService.getClassesWithAI(),
        ApiService.getStudentGrades(),
        ApiService.getDashboardStats()
      ]);

      const classesData = classesResponse.data?.classes || [];
      const grades = gradesResponse.data || [];
      const dashboardStats = dashboardResponse.data || {};
      
      setClasses(classesData);
      
      // Calculate stats
      const pendingAssignments = classesData.reduce((total, cls) => 
        total + (cls.assignments?.filter(a => !a.submitted).length || 0), 0
      );
      
      const overallGrade = grades.length > 0 
        ? grades.reduce((sum, grade) => sum + grade.grade, 0) / grades.length 
        : dashboardStats.average_grade || 85.5;

      const upcomingDeadlines = classesData
        .flatMap(cls => cls.assignments || [])
        .filter(a => !a.submitted && new Date(a.due_date) > new Date())
        .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
        .slice(0, 5);

      setStats({
        totalClasses: classesData.length || dashboardStats.enrolled_classes || 4,
        overallGrade: Math.round(overallGrade * 10) / 10,
        pendingAssignments: pendingAssignments || 3,
        upcomingDeadlines: upcomingDeadlines,
        chatInteractions: dashboardStats.chat_interactions || 0
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Set demo data if API fails
      setStats({
        totalClasses: 4,
        overallGrade: 85.5,
        pendingAssignments: 3,
        upcomingDeadlines: [
          { id: 1, title: 'Math Quiz Chapter 5', class_name: 'Mathematics 101', due_date: '2025-01-15' },
          { id: 2, title: 'Essay on Climate Change', class_name: 'Environmental Science', due_date: '2025-01-18' },
          { id: 3, title: 'Programming Project 1', class_name: 'Computer Science', due_date: '2025-01-20' }
        ],
        chatInteractions: 0
      });
      
      // Set demo classes for AI chatbot
      setClasses([
        { id: 1, name: 'Mathematics 101', subject: 'mathematics', has_ai_model: true },
        { id: 2, name: 'Environmental Science', subject: 'science', has_ai_model: true },
        { id: 3, name: 'Computer Science', subject: 'science', has_ai_model: true },
        { id: 4, name: 'English Literature', subject: 'english', has_ai_model: true }
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

  const handleOpenChatBot = () => {
    if (classes.filter(cls => cls.has_ai_model).length === 1) {
      // If only one class has AI, open directly
      setSelectedClass(classes.find(cls => cls.has_ai_model));
      setShowChatBot(true);
    } else {
      // Show class selection modal
      setShowChatBot(true);
    }
  };

  const handleSelectClass = (classData) => {
    setSelectedClass(classData);
  };

  const dashboardCards = [
    {
      title: 'My Classes',
      description: 'View enrolled classes and materials',
      icon: faBookOpen,
      color: 'primary',
      value: stats.totalClasses,
      path: '/student/classes'
    },
    {
      title: 'Overall Grade',
      description: 'Your current academic performance',
      icon: faTrophy,
      color: getGradeColor(stats.overallGrade),
      value: `${stats.overallGrade}%`,
      path: '/student/grades'
    },
    {
      title: 'Pending Tasks',
      description: 'Assignments waiting for submission',
      icon: faExclamationTriangle,
      color: stats.pendingAssignments > 0 ? 'warning' : 'success',
      value: stats.pendingAssignments,
      path: '/student/classes'
    },
    {
      title: 'AI Tutor',
      description: 'Get personalized help with your studies',
      icon: faRobot,
      color: 'info',
      value: `${stats.chatInteractions} chats`,
      action: handleOpenChatBot
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
          <p className="text-muted">Student Dashboard</p>
        </Col>
      </Row>

      <Row className="g-4 mb-4">
        {dashboardCards.map((card, index) => (
          <Col key={index} xs={12} sm={6} lg={3}>
            <Card 
              className="dashboard-card student-card h-100 border-0 text-white"
              onClick={() => card.action ? card.action() : navigate(card.path)}
              style={{ cursor: 'pointer' }}
            >
              <Card.Body className="d-flex flex-column align-items-center text-center">
                <FontAwesomeIcon icon={card.icon} size="3x" className="mb-3" />
                <h3 className="display-6 fw-bold mb-2">{card.value}</h3>
                <h5 className="card-title mb-2">{card.title}</h5>
                <p className="card-text small opacity-75">{card.description}</p>
                <Button 
                  variant="light" 
                  className="mt-auto"
                  onClick={(e) => {
                    e.stopPropagation();
                    card.action ? card.action() : navigate(card.path);
                  }}
                >
                  {card.action ? 'Open Chat' : 'View Details'}
                </Button>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>

      <Row className="g-4">
        {/* Academic Progress */}
        <Col xs={12} lg={6}>
          <Card className="h-100 border-0 shadow-sm">
            <Card.Header className="bg-transparent">
              <h5 className="mb-0">
                <FontAwesomeIcon icon={faTrophy} className="me-2" />
                Academic Progress
              </h5>
            </Card.Header>
            <Card.Body>
              <div className="mb-3">
                <div className="d-flex justify-content-between mb-1">
                  <span>Overall Performance</span>
                  <span>{stats.overallGrade}%</span>
                </div>
                <ProgressBar 
                  variant={getGradeColor(stats.overallGrade)} 
                  now={stats.overallGrade} 
                  className="mb-3"
                />
              </div>
              
              <Row className="text-center">
                <Col xs={6}>
                  <div className="border-end">
                    <h4 className="text-primary mb-0">{stats.totalClasses}</h4>
                    <small className="text-muted">Enrolled Classes</small>
                  </div>
                </Col>
                <Col xs={6}>
                  <h4 className={`text-${stats.pendingAssignments > 0 ? 'warning' : 'success'} mb-0`}>
                    {stats.pendingAssignments}
                  </h4>
                  <small className="text-muted">Pending Tasks</small>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>

        {/* Upcoming Deadlines */}
        <Col xs={12} lg={6}>
          <Card className="h-100 border-0 shadow-sm">
            <Card.Header className="bg-transparent d-flex justify-content-between align-items-center">
              <h5 className="mb-0">
                <FontAwesomeIcon icon={faCalendarAlt} className="me-2" />
                Upcoming Deadlines
              </h5>
              <Button 
                variant="outline-primary" 
                size="sm"
                onClick={() => navigate('/student/classes')}
              >
                View All
              </Button>
            </Card.Header>
            <Card.Body className="p-0">
              {stats.upcomingDeadlines.length > 0 ? (
                <ListGroup variant="flush">
                  {stats.upcomingDeadlines.map((assignment, index) => (
                    <ListGroup.Item key={index} className="d-flex justify-content-between align-items-start">
                      <div className="ms-2 me-auto">
                        <div className="fw-bold">{assignment.title}</div>
                        <small className="text-muted">{assignment.class_name}</small>
                      </div>
                      <small className="text-danger">
                        <FontAwesomeIcon icon={faCalendarAlt} className="me-1" />
                        {new Date(assignment.due_date).toLocaleDateString()}
                      </small>
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              ) : (
                <div className="text-center p-4 text-muted">
                  <FontAwesomeIcon icon={faTasks} size="2x" className="mb-2" />
                  <p>No upcoming deadlines</p>
                  <small>Great job staying on top of your work!</small>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Row className="mt-4">
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
                    onClick={() => navigate('/student/classes')}
                  >
                    <FontAwesomeIcon icon={faBookOpen} className="me-2" />
                    Browse Classes
                  </Button>
                </Col>
                <Col xs={12} md={6} lg={3}>
                  <Button 
                    variant="outline-success" 
                    className="w-100"
                    onClick={() => navigate('/student/grades')}
                  >
                    <FontAwesomeIcon icon={faClipboardList} className="me-2" />
                    Check Grades
                  </Button>
                </Col>
                <Col xs={12} md={6} lg={3}>
                  <Button 
                    variant="outline-warning" 
                    className="w-100"
                    onClick={() => navigate('/student/classes')}
                  >
                    <FontAwesomeIcon icon={faTasks} className="me-2" />
                    Submit Assignment
                  </Button>
                </Col>
                <Col xs={12} md={6} lg={3}>
                  <Button variant="outline-info" className="w-100">
                    <FontAwesomeIcon icon={faCalendarAlt} className="me-2" />
                    View Schedule
                  </Button>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* AI Chatbot Modal */}
      <Modal 
        show={showChatBot} 
        onHide={() => setShowChatBot(false)}
        size="lg"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>
            <FontAwesomeIcon icon={faRobot} className="me-2" />
            AI Learning Assistant
          </Modal.Title>
        </Modal.Header>
        <Modal.Body className="p-0">
          {!selectedClass ? (
            <div className="p-4">
              <h6 className="mb-3">Select a class to get AI assistance:</h6>
              <div className="d-grid gap-2">
                {classes.filter(cls => cls.has_ai_model).map(cls => (
                  <Button
                    key={cls.id}
                    variant="outline-primary"
                    onClick={() => handleSelectClass(cls)}
                    className="text-start"
                  >
                    <FontAwesomeIcon icon={faBookOpen} className="me-2" />
                    {cls.name}
                    <small className="text-muted d-block">{cls.subject} tutor</small>
                  </Button>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ height: '500px' }}>
              <ChatBot 
                classId={selectedClass.id}
                className={selectedClass.name}
                user={user}
              />
            </div>
          )}
        </Modal.Body>
        {selectedClass && (
          <Modal.Footer>
            <Button 
              variant="secondary" 
              onClick={() => setSelectedClass(null)}
            >
              Change Class
            </Button>
          </Modal.Footer>
        )}
      </Modal>
    </Container>
  );
}

export default StudentDashboard;