import React, { useState } from 'react';
import { Card, Form, Button, Alert, Badge, Table, Spinner, Modal, ProgressBar } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faDownload, faEye, faTree, faDatabase, faFileExport, faCheck, faExclamationTriangle } from '@fortawesome/free-solid-svg-icons';
import ApiService from '../../services/ApiService';

function DataExport() {
  const [selections, setSelections] = useState({
    users: false,
    classes: false,
    chat_history: false,
    ai_models: false,
    include_chat_history: false,
    include_grades: false,
    include_assignments: false,
    include_content_files: false
  });
  const [exportTree, setExportTree] = useState(null);
  const [totalRecords, setTotalRecords] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [isDownloading, setIsDownloading] = useState(false);

  const handleSelectionChange = (field, value) => {
    setSelections(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Reset preview when selections change
    setExportTree(null);
    setShowPreview(false);
  };

  const previewExport = async () => {
    if (!hasSelections()) {
      setError('Please select at least one data type to export');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await ApiService.previewExportData(selections);
      setExportTree(response.export_tree);
      setTotalRecords(response.total_records);
      setShowPreview(true);
    } catch (err) {
      setError('Failed to generate preview. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const downloadExport = async () => {
    if (!hasSelections()) {
      setError('Please select at least one data type to export');
      return;
    }

    setIsDownloading(true);
    setDownloadProgress(0);
    setError('');

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setDownloadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const response = await ApiService.downloadExportData(selections);
      
      clearInterval(progressInterval);
      setDownloadProgress(100);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `school_data_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setTimeout(() => {
        setDownloadProgress(0);
      }, 2000);

    } catch (err) {
      setError('Failed to download export. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  const hasSelections = () => {
    return Object.values(selections).some(value => value === true);
  };

  const renderExportTree = (tree) => {
    if (!tree) return null;

    return (
      <div className="mt-4">
        <h6>
          <FontAwesomeIcon icon={faTree} className="me-2" />
          Export Preview
        </h6>
        
        {Object.entries(tree).map(([category, data]) => (
          <Card key={category} className="mb-3">
            <Card.Header>
              <div className="d-flex justify-content-between align-items-center">
                <strong className="text-capitalize">{category.replace('_', ' ')}</strong>
                <Badge variant="info">{data.count} records</Badge>
              </div>
            </Card.Header>
            <Card.Body>
              <div className="mb-2">
                <strong>Fields:</strong>
                <div className="mt-1">
                  {data.fields.map(field => (
                    <Badge key={field} variant="secondary" className="me-1 mb-1">
                      {field}
                    </Badge>
                  ))}
                </div>
              </div>
              
              {data.related_data && Object.keys(data.related_data).length > 0 && (
                <div>
                  <strong>Related Data:</strong>
                  {Object.entries(data.related_data).map(([relatedCategory, relatedData]) => (
                    <div key={relatedCategory} className="mt-2 ps-3 border-start">
                      <div className="d-flex justify-content-between align-items-center">
                        <span className="text-capitalize">{relatedCategory.replace('_', ' ')}</span>
                        <Badge variant="warning">{relatedData.count} records</Badge>
                      </div>
                      <div className="mt-1">
                        {relatedData.fields.map(field => (
                          <Badge key={field} variant="outline-secondary" className="me-1 mb-1">
                            {field}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>
        ))}
        
        <Alert variant="info" className="mt-3">
          <FontAwesomeIcon icon={faDatabase} className="me-2" />
          <strong>Total Records: {totalRecords}</strong>
        </Alert>
      </div>
    );
  };

  return (
    <div className="container-fluid py-4">
      <div className="row justify-content-center">
        <div className="col-lg-10">
          <Card>
            <Card.Header>
              <h4>
                <FontAwesomeIcon icon={faFileExport} className="me-2" />
                Data Export Center
              </h4>
              <p className="mb-0 text-muted">
                Select and export school data with relationship visualization
              </p>
            </Card.Header>
            
            <Card.Body>
              {error && (
                <Alert variant="danger">
                  <FontAwesomeIcon icon={faExclamationTriangle} className="me-2" />
                  {error}
                </Alert>
              )}

              {/* Selection Form */}
              <div className="row">
                <div className="col-md-6">
                  <h6>Primary Data Types</h6>
                  
                  <Form.Check
                    type="checkbox"
                    id="users"
                    label="Users (Students, Teachers, Admins)"
                    checked={selections.users}
                    onChange={(e) => handleSelectionChange('users', e.target.checked)}
                    className="mb-2"
                  />
                  
                  <Form.Check
                    type="checkbox"
                    id="classes"
                    label="Classes"
                    checked={selections.classes}
                    onChange={(e) => handleSelectionChange('classes', e.target.checked)}
                    className="mb-2"
                  />
                  
                  <Form.Check
                    type="checkbox"
                    id="chat_history"
                    label="Chat History"
                    checked={selections.chat_history}
                    onChange={(e) => handleSelectionChange('chat_history', e.target.checked)}
                    className="mb-2"
                  />
                  
                  <Form.Check
                    type="checkbox"
                    id="ai_models"
                    label="AI Models"
                    checked={selections.ai_models}
                    onChange={(e) => handleSelectionChange('ai_models', e.target.checked)}
                    className="mb-2"
                  />
                </div>
                
                <div className="col-md-6">
                  <h6>Related Data (when Users selected)</h6>
                  
                  <Form.Check
                    type="checkbox"
                    id="include_chat_history"
                    label="Include User Chat History"
                    checked={selections.include_chat_history}
                    onChange={(e) => handleSelectionChange('include_chat_history', e.target.checked)}
                    disabled={!selections.users}
                    className="mb-2"
                  />
                  
                  <Form.Check
                    type="checkbox"
                    id="include_grades"
                    label="Include User Grades"
                    checked={selections.include_grades}
                    onChange={(e) => handleSelectionChange('include_grades', e.target.checked)}
                    disabled={!selections.users}
                    className="mb-2"
                  />
                  
                  <Form.Check
                    type="checkbox"
                    id="include_assignments"
                    label="Include User Assignments"
                    checked={selections.include_assignments}
                    onChange={(e) => handleSelectionChange('include_assignments', e.target.checked)}
                    disabled={!selections.users}
                    className="mb-2"
                  />
                  
                  <Form.Check
                    type="checkbox"
                    id="include_content_files"
                    label="Include Class Content Files"
                    checked={selections.include_content_files}
                    onChange={(e) => handleSelectionChange('include_content_files', e.target.checked)}
                    disabled={!selections.classes}
                    className="mb-2"
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="d-flex gap-2 mt-4">
                <Button
                  variant="outline-primary"
                  onClick={previewExport}
                  disabled={!hasSelections() || isLoading}
                >
                  {isLoading ? (
                    <Spinner size="sm" className="me-2" />
                  ) : (
                    <FontAwesomeIcon icon={faEye} className="me-2" />
                  )}
                  Preview Export
                </Button>
                
                <Button
                  variant="primary"
                  onClick={downloadExport}
                  disabled={!hasSelections() || isDownloading}
                >
                  {isDownloading ? (
                    <Spinner size="sm" className="me-2" />
                  ) : (
                    <FontAwesomeIcon icon={faDownload} className="me-2" />
                  )}
                  Download CSV
                </Button>
              </div>

              {/* Download Progress */}
              {isDownloading && (
                <div className="mt-3">
                  <ProgressBar now={downloadProgress} label={`${downloadProgress}%`} />
                </div>
              )}

              {/* Export Tree Visualization */}
              {showPreview && renderExportTree(exportTree)}
            </Card.Body>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default DataExport;