import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, ProgressBar } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUpload, faSave, faArrowLeft, faFile, faTrash } from '@fortawesome/free-solid-svg-icons';
import { useParams, useNavigate } from 'react-router-dom';
import ApiService from '../../services/ApiService';

function UploadContent({ user }) {
  const { classId } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    file_type: 'pdf',
    files: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
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
      for (const file of formData.files) {
        await ApiService.uploadContent(classId, file, {
          name: formData.name || file.name,
          file_type: formData.file_type
        });
      }
      
      setUploadProgress(100);
      setSuccess('Content uploaded successfully!');
      
      setTimeout(() => {
        navigate('/teacher/content');
      }, 2000);
    } catch (error) {
      clearInterval(progressInterval);
      setUploadProgress(0);
      setError(error.response?.data?.message || 'Failed to upload content');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    
    // Validate files
    const validFiles = [];
    const errors = [];
    
    files.forEach(file => {
      // Check file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        errors.push(`${file.name}: File size must be less than 10MB`);
        return;
      }
      
      // Check file type
      const allowedTypes = {
        'pdf': ['application/pdf'],
        'word': ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'slides': ['application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'],
        'image': ['image/jpeg', 'image/jpg', 'image/png']
      };
      
      const isValidType = Object.values(allowedTypes).flat().includes(file.type);
      
      if (!isValidType) {
        errors.push(`${file.name}: Invalid file type`);
        return;
      }
      
      validFiles.push(file);
    });
    
    if (errors.length > 0) {
      setError(errors.join(', '));
    } else {
      setError('');
    }
    
    setFormData({ ...formData, files: validFiles });
  };

  const removeFile = (index) => {
    const newFiles = formData.files.filter((_, i) => i !== index);
    setFormData({ ...formData, files: newFiles });
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Container fluid className="py-4">
      <Row className="mb-4">
        <Col>
          <div className="d-flex align-items-center">
            <Button 
              variant="outline-secondary" 
              className="me-3"
              onClick={() => navigate('/teacher/content')}
            >
              <FontAwesomeIcon icon={faArrowLeft} />
            </Button>
            <div>
              <h1 className="h2 mb-1">
                <FontAwesomeIcon icon={faUpload} className="me-2" />
                Upload Course Content
              </h1>
              <p className="text-muted">Add learning materials for your class</p>
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
              <h5 className="mb-0">Content Details</h5>
            </Card.Header>
            <Card.Body>
              <Form onSubmit={handleSubmit}>
                <Row className="g-3">
                  <Col xs={12}>
                    <Form.Group>
                      <Form.Label>Content Name (Optional)</Form.Label>
                      <Form.Control
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({...formData, name: e.target.value})}
                        placeholder="Leave blank to use filename"
                      />
                      <Form.Text className="text-muted">
                        If left blank, the original filename will be used
                      </Form.Text>
                    </Form.Group>
                  </Col>

                  <Col xs={12}>
                    <Form.Group>
                      <Form.Label>Content Type</Form.Label>
                      <Form.Select
                        value={formData.file_type}
                        onChange={(e) => setFormData({...formData, file_type: e.target.value})}
                      >
                        <option value="pdf">PDF Document</option>
                        <option value="word">Word Document</option>
                        <option value="slides">Presentation Slides</option>
                        <option value="image">Image/Diagram</option>
                      </Form.Select>
                    </Form.Group>
                  </Col>

                  <Col xs={12}>
                    <Form.Group>
                      <Form.Label>Upload Files</Form.Label>
                      <div className="file-drop-zone">
                        <FontAwesomeIcon icon={faUpload} size="2x" className="mb-3" />
                        <h6>Drag & Drop Your Files Here</h6>
                        <p className="text-muted mb-3">or click to select files</p>
                        <Form.Control
                          type="file"
                          onChange={handleFileChange}
                          accept=".pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png"
                          multiple
                          className="mb-2"
                        />
                        <small className="text-muted">
                          Accepted formats: PDF, DOC, DOCX, PPT, PPTX, JPG, PNG (Max 10MB per file)
                        </small>
                      </div>
                    </Form.Group>
                  </Col>

                  {/* File List */}
                  {formData.files.length > 0 && (
                    <Col xs={12}>
                      <h6>Selected Files:</h6>
                      {formData.files.map((file, index) => (
                        <Card key={index} className="mb-2 border">
                          <Card.Body className="py-2">
                            <div className="d-flex justify-content-between align-items-center">
                              <div className="d-flex align-items-center">
                                <FontAwesomeIcon icon={faFile} className="me-2 text-primary" />
                                <div>
                                  <div className="fw-bold small">{file.name}</div>
                                  <small className="text-muted">{formatFileSize(file.size)}</small>
                                </div>
                              </div>
                              <Button 
                                variant="outline-danger" 
                                size="sm"
                                onClick={() => removeFile(index)}
                              >
                                <FontAwesomeIcon icon={faTrash} />
                              </Button>
                            </div>
                          </Card.Body>
                        </Card>
                      ))}
                    </Col>
                  )}

                  {/* Upload Progress */}
                  {loading && uploadProgress > 0 && (
                    <Col xs={12}>
                      <div className="mb-3">
                        <div className="d-flex justify-content-between mb-1">
                          <span>Uploading files...</span>
                          <span>{uploadProgress}%</span>
                        </div>
                        <ProgressBar 
                          now={uploadProgress} 
                          variant={uploadProgress === 100 ? 'success' : 'primary'}
                          animated={uploadProgress < 100}
                        />
                      </div>
                    </Col>
                  )}

                  <Col xs={12}>
                    <div className="bg-light p-3 rounded">
                      <h6 className="mb-2">Content Guidelines</h6>
                      <ul className="mb-0 small text-muted">
                        <li>Ensure all content is relevant to your course curriculum</li>
                        <li>Use clear, descriptive filenames for easy identification</li>
                        <li>PDFs should be text-searchable when possible</li>
                        <li>Images should be high resolution and clearly visible</li>
                        <li>Consider file sizes for student download convenience</li>
                      </ul>
                    </div>
                  </Col>
                </Row>

                <div className="d-flex justify-content-end gap-2 mt-4">
                  <Button 
                    variant="outline-secondary" 
                    onClick={() => navigate('/teacher/content')}
                    disabled={loading}
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="submit" 
                    variant="primary"
                    disabled={loading || formData.files.length === 0}
                  >
                    {loading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Uploading...
                      </>
                    ) : (
                      <>
                        <FontAwesomeIcon icon={faSave} className="me-2" />
                        Upload Content
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

export default UploadContent;