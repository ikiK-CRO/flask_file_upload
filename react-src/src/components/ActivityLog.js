import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const ActivityLog = () => {
  const { t } = useTranslation();
  const [files, setFiles] = useState([]);
  const [uploadLogs, setUploadLogs] = useState([]);
  const [downloadLogs, setDownloadLogs] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('files');
  const [password, setPassword] = useState('');
  const [selectedFileId, setSelectedFileId] = useState(null);
  const [passwordError, setPasswordError] = useState('');
  const [downloadLoading, setDownloadLoading] = useState(false);

  // Create fetchLogs as a callback function so we can reuse it
  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/logs');
      
      if (response.data.success) {
        setFiles(response.data.files || []);
        setUploadLogs(response.data.upload_logs || []);
        setDownloadLogs(response.data.download_logs || []);
      } else {
        setError(response.data.message || t('Could not load logs.'));
      }
      
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.message || t('Could not load logs.'));
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    fetchLogs();
    
    // Load Bootstrap modal functionality dynamically
    const loadBootstrapModal = () => {
      // Ensure we have Bootstrap JS available
      if (typeof window !== 'undefined' && !window.bootstrap) {
        const bootstrapScript = document.createElement('script');
        bootstrapScript.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js';
        bootstrapScript.integrity = 'sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p';
        bootstrapScript.crossOrigin = 'anonymous';
        document.body.appendChild(bootstrapScript);
      }
    };
    
    loadBootstrapModal();
  }, [fetchLogs]);

  const initiateDownload = (fileId) => {
    console.log('Initiating download for file:', fileId);
    setSelectedFileId(fileId);
    setPassword('');
    setPasswordError('');
    
    // Show password modal
    setTimeout(() => {
      const modalElement = document.getElementById('passwordModal');
      if (modalElement && window.bootstrap) {
        const modal = new window.bootstrap.Modal(modalElement);
        modal.show();
      } else {
        console.error('Modal element or Bootstrap not found');
        alert(t('Please enter a password to download the file'));
      }
    }, 100);
  };

  const handleDownload = async () => {
    if (!password) {
      setPasswordError(t('Password is required'));
      return;
    }
    
    if (!selectedFileId) {
      setPasswordError(t('No file selected'));
      return;
    }

    console.log('Attempting download with password for file:', selectedFileId);
    setDownloadLoading(true);

    try {
      const response = await axios.post(`/api/files/${selectedFileId}`, { password }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Download response:', response.data);
      
      if (response.data.success) {
        // Hide modal if exists
        try {
          const modalElement = document.getElementById('passwordModal');
          if (modalElement && window.bootstrap) {
            const bsModal = window.bootstrap.Modal.getInstance(modalElement);
            if (bsModal) bsModal.hide();
          }
        } catch (e) {
          console.error('Error hiding modal:', e);
        }
        
        // Set up a listener to refresh logs after download completes
        const refreshLogsAfterDownload = () => {
          console.log('Download completed, refreshing logs');
          setTimeout(() => {
            fetchLogs();
          }, 1000); // Give the server a moment to process the download
          window.removeEventListener('focus', refreshLogsAfterDownload);
        };
        
        // Add listener for when window regains focus (after download dialog)
        window.addEventListener('focus', refreshLogsAfterDownload);
        
        // Redirect to download URL
        console.log('Redirecting to download URL:', response.data.download_url);
        window.location.href = response.data.download_url;
      } else {
        setPasswordError(response.data.message || t('Download failed.'));
      }
    } catch (err) {
      console.error('Download error:', err);
      if (err.response) {
        console.error('Error response data:', err.response.data);
        console.error('Error response status:', err.response.status);
      }
      setPasswordError(err.response?.data?.message || t('Download failed.'));
    } finally {
      setDownloadLoading(false);
    }
  };

  // Function to explicitly refresh the logs
  const refreshLogs = () => {
    fetchLogs();
  };

  if (loading) {
    return <div className="text-center py-5">{t('Loading logs...')}</div>;
  }

  return (
    <>
      <div className="card shadow-sm">
        <div className="card-header">
          <div className="d-flex justify-content-between align-items-center">
            <h2 className="mb-0">{t('Activity Logs')}</h2>
            <button 
              className="btn btn-sm btn-outline-secondary" 
              onClick={refreshLogs}
            >
              {t('Refresh')}
            </button>
          </div>
        </div>
        <div className="card-body">
          {error ? (
            <div className="alert alert-danger">{error}</div>
          ) : (
            <>
              <ul className="nav nav-tabs mb-4">
                <li className="nav-item">
                  <button 
                    className={`nav-link ${activeTab === 'files' ? 'active' : ''}`}
                    onClick={() => setActiveTab('files')}
                  >
                    {t('Files')}
                  </button>
                </li>
                <li className="nav-item">
                  <button 
                    className={`nav-link ${activeTab === 'uploads' ? 'active' : ''}`}
                    onClick={() => setActiveTab('uploads')}
                  >
                    {t('Upload Logs')}
                  </button>
                </li>
                <li className="nav-item">
                  <button 
                    className={`nav-link ${activeTab === 'downloads' ? 'active' : ''}`}
                    onClick={() => setActiveTab('downloads')}
                  >
                    {t('Download Logs')}
                  </button>
                </li>
              </ul>
              
              {activeTab === 'files' && (
                <div className="table-responsive">
                  <table className="table table-striped">
                    <thead className="bg-primary-custom">
                      <tr>
                        <th>{t('File Name')}</th>
                        <th>{t('Upload Date')}</th>
                        <th>{t('Downloads')}</th>
                        <th>{t('Actions')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {files.length > 0 ? (
                        files.map((file) => (
                          <tr key={file.id}>
                            <td>{file.file_name}</td>
                            <td>{file.upload_date}</td>
                            <td>{file.download_count}</td>
                            <td>
                              <button 
                                className="btn btn-success btn-sm"
                                onClick={() => initiateDownload(file.id)}
                              >
                                {t('Download')}
                              </button>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="4" className="text-center">{t('No files found.')}</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}
              
              {activeTab === 'uploads' && (
                <div className="log-container">
                  {uploadLogs.length > 0 ? (
                    <ul className="list-group">
                      {uploadLogs.map((log, index) => (
                        <li key={index} className="list-group-item">{log}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-center">{t('No upload logs found.')}</p>
                  )}
                </div>
              )}
              
              {activeTab === 'downloads' && (
                <div className="log-container">
                  {downloadLogs.length > 0 ? (
                    <ul className="list-group">
                      {downloadLogs.map((log, index) => (
                        <li key={index} className="list-group-item">{log}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-center">{t('No download logs found.')}</p>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Password Modal */}
      <div className="modal fade" id="passwordModal" tabIndex="-1" aria-labelledby="passwordModalLabel" aria-hidden="true">
        <div className="modal-dialog">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title" id="passwordModalLabel">{t('Enter Password')}</h5>
              <button type="button" className="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div className="modal-body">
              {passwordError && (
                <div className="alert alert-danger">{passwordError}</div>
              )}
              <div className="mb-3">
                <label htmlFor="filePassword" className="form-label">{t('Password')}</label>
                <input 
                  type="password" 
                  className="form-control" 
                  id="filePassword" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleDownload();
                    }
                  }}
                  autoFocus
                />
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">{t('Cancel')}</button>
              <button 
                type="button" 
                className="btn btn-success" 
                onClick={handleDownload}
                disabled={downloadLoading}
              >
                {downloadLoading ? t('Processing...') : t('Download')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ActivityLog;