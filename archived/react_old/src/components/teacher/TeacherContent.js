import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Button, Badge, Form, Modal } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFolder, faUpload, faDownload, faTrash, faFilePdf, faFileWord, faFileImage, faFile } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import ApiService from '../../services/ApiService';

function TeacherContent({ user }) {
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [contentFiles, setContentFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedClass, setSelectedClass] = useState('all');
  const [showUploadModal, setShowUploadModal] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const classesResponse = await ApiService.getTeacherClasses();
      setClasses(classesResponse.data);
      
      // Fetch content for all classes
      const allContent = [];
      for (const classItem of classesResponse.data) {
        try {
          const contentResponse = await ApiService.getClassContent(classItem.id);
          allContent.push(...contentResponse.data.map(file => ({
            ...file,
            class_name: classItem.name
          })));
        } catch (error) {
          console.log(`No content for class ${classItem.id}`);
        }
      }
      setContentFiles(allContent);
    } catch (error) {
      console.error('Error fetching data:', error);
      // Set demo data if API fails
      setClasses([
        { id: 1, name: 'Mathematics 101' },
        { id: 2, name: 'Environmental Science' },
        { id: 3, name: 'Computer Science Fundamentals' }
      ]);
      
      setContentFiles([
        {
          id: 1,
          name: 'Chapter 5 - Algebraic Functions',
          file_type: 'pdf',
          file_path: '/content/math_chapter5.pdf',
          class_id: 1,
          class_name: 'Mathematics 101',
          uploaded_at: '2025-01-08',
          file_size: '2.3 MB'
        },
        {
          id: 2,
          name: 'Homework Assignment Template',
          file_type: 'word',
          file_path: '/content/hw_template.docx',
          class_id: 1,
          class_name: 'Mathematics 101',
          uploaded_at: '2025-01-10',
          file_size: '156 KB'
        },
        {
          id: 3,
          name: 'Climate Change Presentation',
          file_type: 'slides',
          file_path: '/content/climate_presentation.pptx',
          class_id: 2,
          class_name: 'Environmental Science',
          uploaded_at: '2025-01-12',
          file_size: '5.7 MB'
        },
        {
          id: 4,
          name: 'Programming Fundamentals Guide',
          file_type: 'pdf',
          file_path: '/content/programming_guide.pdf',
          class_id: 3,
          class_name: 'Computer Science Fundamentals',
          uploaded_at: '2025-01-14',
          file_size: '3.1 MB'
        },
        {
          id: 5,
          name: 'Data Structure Diagram',
          file_type: 'image',
          file_path: '/content/data_structures.png',
          class_id: 3,
          class_name: 'Computer Science Fundamentals',
          uploaded_at: '2025-01-15',
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
      default: return faFile;
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

  const getFilteredFiles = () => {
    if (selectedClass === 'all') {
      return contentFiles;
    }
    return contentFiles.filter(file => file.class_id === parseInt(selectedClass));
  };

  const handleDelete = async (fileId) => {
    if (window.confirm('Are you sure you want to delete this file?')) {
      try {
        // await ApiService.deleteContent(fileId);
        setContentFiles(contentFiles.filter(file => file.id !== fileId));
      } catch (error) {
        console.error('Error deleting file:', error);
      }
    }
  };

  const filteredFiles = getFilteredFiles();

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
                <FontAwesomeIcon icon={faFolder} className="me-2" />
                Course Content
              </h1>
              <p className="text-muted">Upload and manage course materials for your classes</p>
            </div>
            <Button 
              variant="primary"
              onClick={() => setShowUploadModal(true)}
            >
              <FontAwesomeIcon icon={faUpload} className="me-2" />
              Upload Content
            </Button>
          </div>
        </Col>
      </Row>

      {/* Summary Cards */}
      <Row className="g-4 mb-4">
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faFolder} size="2x" className="text-primary mb-2" />
              <h3 className="mb-0">{classes.length}</h3>
              <small className="text-muted">Classes</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faFile} size="2x" className="text-success mb-2" />
              <h3 className="mb-0">{contentFiles.length}</h3>
              <small className="text-muted">Total Files</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faFilePdf} size="2x" className="text-danger mb-2" />
              <h3 className="mb-0">{contentFiles.filter(f => f.file_type === 'pdf').length}</h3>
              <small className="text-muted">PDF Documents</small>
            </Card.Body>
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={3}>
          <Card className="text-center border-0 shadow-sm">
            <Card.Body>
              <FontAwesomeIcon icon={faFileImage} size="2x" className="text-info mb-2" />
              <h3 className="mb-0">{contentFiles.filter(f => f.file_type === 'image').length}</h3>
              <small className="text-muted">Images</small>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Filter */}
      <Row className="mb-4">
        <Col md={4}>
          <Form.Group>
            <Form.Label>Filter by Class</Form.Label>
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
            {filteredFiles.length} file{filteredFiles.length !== 1 ? 's' : ''} found
          </div>
        </Col>
      </Row>

      {/* Content Files Table */}
      <Row>
        <Col>
          <Card className="border-0 shadow-sm">
            <Card.Body className="p-0">
              <div className="table-responsive">
                <Table hover className="mb-0">
                  <thead className="table-dark">
                    <tr>
                      <th>File Name</th>
                      <th>Type</th>
                      <th>Class</th>
                      <th>Size</th>
                      <th>Uploaded</th>
                      <th className="text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredFiles.map((file) => (
                      <tr key={file.id}>
                        <td>
                          <div className="d-flex align-items-center">
                            <FontAwesomeIcon 
                              icon={getFileIcon(file.file_type)} 
                              className={`me-2 text-${getFileTypeColor(file.file_type)}`}
                            />
                            <div>
                              <div className="fw-bold">{file.name}</div>
                              <small className="text-muted">{file.file_path}</small>
                            </div>
                          </div>
                        </td>
                        <td>
                          <Badge bg={getFileTypeColor(file.file_type)}>
                            {file.file_type.toUpperCase()}
                          </Badge>
                        </td>
                        <td>{file.class_name}</td>
                        <td className="text-muted">{file.file_size}</td>
                        <td className="text-muted">
                          {new Date(file.uploaded_at).toLocaleDateString()}
                        </td>
                        <td className="text-center">
                          <Button variant="outline-success" size="sm" className="me-1">
                            <FontAwesomeIcon icon={faDownload} />
                          </Button>
                          <Button 
                            variant="outline-danger" 
                            size="sm"
                            onClick={() => handleDelete(file.id)}
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

      {/* Upload Modal */}
      <Modal show={showUploadModal} onHide={() => setShowUploadModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Upload Course Content</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Select Class</Form.Label>
            <Form.Select required>
              <option value="">Choose a class...</option>
              {classes.map((classItem) => (
                <option key={classItem.id} value={classItem.id}>
                  {classItem.name}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
          
          <div className="file-drop-zone">
            <FontAwesomeIcon icon={faUpload} size="2x" className="mb-3" />
            <h5>Drag & Drop Files Here</h5>
            <p className="text-muted">or click to select files</p>
            <Form.Control type="file" multiple accept=".pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png" />
          </div>
          
          <div className="mt-3">
            <small className="text-muted">
              Supported formats: PDF, DOC, DOCX, PPT, PPTX, JPG, PNG (Max 10MB per file)
            </small>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowUploadModal(false)}>
            Cancel
          </Button>
          <Button variant="primary">
            <FontAwesomeIcon icon={faUpload} className="me-1" />
            Upload Files
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}

export default TeacherContent;