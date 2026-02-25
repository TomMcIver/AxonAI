import React from 'react';
import { Navbar, Nav, Container, NavDropdown, Button } from 'react-bootstrap';
import { LinkContainer } from 'react-router-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faGraduationCap, faUser, faSignOutAlt, faTachometerAlt, faUsers, faChalkboardTeacher, faBookOpen, faChild } from '@fortawesome/free-solid-svg-icons';

function Navigation({ user, onLogout }) {
  const getRoleIcon = () => {
    switch (user.role) {
      case 'admin': return faUsers;
      case 'teacher': return faChalkboardTeacher;
      case 'student': return faBookOpen;
      case 'parent': return faChild;
      default: return faUser;
    }
  };

  const getRoleColor = () => {
    switch (user.role) {
      case 'admin': return 'primary';
      case 'teacher': return 'warning';
      case 'student': return 'info';
      case 'parent': return 'success';
      default: return 'secondary';
    }
  };

  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="shadow-sm">
      <Container fluid>
        <LinkContainer to="/dashboard">
          <Navbar.Brand>
            <FontAwesomeIcon icon={faGraduationCap} className="me-2" />
            School Management
          </Navbar.Brand>
        </LinkContainer>
        
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <LinkContainer to="/dashboard">
              <Nav.Link>
                <FontAwesomeIcon icon={faTachometerAlt} className="me-1" />
                Dashboard
              </Nav.Link>
            </LinkContainer>
            
            {/* Admin Navigation */}
            {user.role === 'admin' && (
              <>
                <LinkContainer to="/admin/users">
                  <Nav.Link>
                    <FontAwesomeIcon icon={faUsers} className="me-1" />
                    Manage Users
                  </Nav.Link>
                </LinkContainer>
                <LinkContainer to="/admin/classes">
                  <Nav.Link>
                    <FontAwesomeIcon icon={faChalkboardTeacher} className="me-1" />
                    Manage Classes
                  </Nav.Link>
                </LinkContainer>
              </>
            )}
            
            {/* Teacher Navigation */}
            {user.role === 'teacher' && (
              <>
                <LinkContainer to="/teacher/classes">
                  <Nav.Link>My Classes</Nav.Link>
                </LinkContainer>
                <LinkContainer to="/teacher/students">
                  <Nav.Link>My Students</Nav.Link>
                </LinkContainer>
                <LinkContainer to="/teacher/gradebook">
                  <Nav.Link>Gradebook</Nav.Link>
                </LinkContainer>
                <LinkContainer to="/teacher/content">
                  <Nav.Link>Course Content</Nav.Link>
                </LinkContainer>
              </>
            )}
            
            {/* Student Navigation */}
            {user.role === 'student' && (
              <>
                <LinkContainer to="/student/classes">
                  <Nav.Link>My Classes</Nav.Link>
                </LinkContainer>
                <LinkContainer to="/student/grades">
                  <Nav.Link>My Grades</Nav.Link>
                </LinkContainer>
              </>
            )}

            {/* Parent Navigation */}
            {user.role === 'parent' && (
              <LinkContainer to="/dashboard">
                <Nav.Link>
                  <FontAwesomeIcon icon={faChild} className="me-1" />
                  Child Overview
                </Nav.Link>
              </LinkContainer>
            )}
          </Nav>
          
          <Nav>
            <NavDropdown 
              title={
                <>
                  <FontAwesomeIcon icon={getRoleIcon()} className={`me-1 text-${getRoleColor()}`} />
                  {user.first_name} {user.last_name}
                </>
              } 
              id="user-dropdown"
              align="end"
            >
              <NavDropdown.Item>
                <FontAwesomeIcon icon={faUser} className="me-2" />
                Profile
              </NavDropdown.Item>
              <NavDropdown.Divider />
              <NavDropdown.Item onClick={onLogout}>
                <FontAwesomeIcon icon={faSignOutAlt} className="me-2" />
                Logout
              </NavDropdown.Item>
            </NavDropdown>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}

export default Navigation;