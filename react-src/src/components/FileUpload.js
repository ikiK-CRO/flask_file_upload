import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const FileUpload = () => {
  const { t } = useTranslation();
  const [file, setFile] = useState(null);
  const [password, setPassword] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const onDrop = useCallback(acceptedFiles => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/gif': ['.gif'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/zip': ['.zip']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: false
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError(t('Please select a file.'));
      return;
    }
    
    if (!password) {
      setError(t('Please enter a password.'));
      return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('password', password);
    
    try {
      setMessage(null);
      setError(null);
      setUploadProgress(0);
      
      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        }
      });
      
      // Enhanced debugging to see all response data
      console.log('Upload response (full):', response);
      console.log('Upload response.data:', response.data);
      console.log('file_url value:', response.data.file_url);
      
      if (response.data.success) {
        // Create a direct link to the FileDownload component with the UUID
        let fileUuid = '';
        if (response.data.file_url) {
          const match = response.data.file_url.match(/\/get-file\/([^\/\?]+)/);
          if (match && match[1]) {
            fileUuid = match[1];
            console.log('Extracted file UUID:', fileUuid);
          }
        }
        
        // Set a more direct message with the correct link format
        setMessage(t('File uploaded successfully! Access it at: ') + 
          `<a href="/get-file/${fileUuid}">/get-file/${fileUuid}</a>`);
        setFile(null);
        setPassword('');
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.message || t('An error occurred during upload.'));
    }
  };

  return (
    <div className="card shadow-sm">
      <div className="card-header">
        <h2 className="mb-0">{t('Upload File')}</h2>
      </div>
      <div className="card-body">
        {message && (
          <div className="alert alert-success" dangerouslySetInnerHTML={{ __html: message }}></div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="form-label">{t('Choose file:')}</label>
            <div 
              {...getRootProps()} 
              className={`dropzone p-5 rounded ${isDragActive ? 'border-primary' : ''}`}
            >
              <input {...getInputProps()} />
              {file ? (
                <p className="mb-0 fw-bold">{t('Selected file:')} {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)</p>
              ) : (
                <div className="text-center">
                  <div className="mb-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" className="bi bi-cloud-arrow-up" viewBox="0 0 16 16">
                      <path fillRule="evenodd" d="M7.646 5.146a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1-.708.708L8.5 6.707V10.5a.5.5 0 0 1-1 0V6.707L6.354 7.854a.5.5 0 1 1-.708-.708l2-2z"/>
                      <path d="M4.406 3.342A5.53 5.53 0 0 1 8 2c2.69 0 4.923 2 5.166 4.579C14.758 6.804 16 8.137 16 9.773 16 11.569 14.502 13 12.687 13H3.781C1.708 13 0 11.366 0 9.318c0-1.763 1.266-3.223 2.942-3.593.143-.863.698-1.723 1.464-2.383zm.653.757c-.757.653-1.153 1.44-1.153 2.056v.448l-.445.049C2.064 6.805 1 7.952 1 9.318 1 10.785 2.23 12 3.781 12h8.906C13.98 12 15 10.988 15 9.773c0-1.216-1.02-2.228-2.313-2.228h-.5v-.5C12.188 4.825 10.328 3 8 3a4.53 4.53 0 0 0-2.941 1.1z"/>
                    </svg>
                  </div>
                  <p className="mb-1">
                    {isDragActive
                      ? t('Drop the file here...')
                      : t('Drag and drop a file here, or click to select a file')}
                  </p>
                  <small className="text-muted">
                    {t('Allowed file types: txt, pdf, png, jpg, jpeg, gif, doc, docx, xls, xlsx, zip (Max 10MB)')}
                  </small>
                </div>
              )}
            </div>
          </div>
          
          <div className="mb-4">
            <label htmlFor="password" className="form-label">{t('Enter password:')}</label>
            <input
              type="password"
              id="password"
              className="form-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <small className="text-muted">
              {t('This password will be required to download the file')}
            </small>
          </div>
          
          <button type="submit" className="btn btn-primary btn-lg px-4">
            {t('Upload')}
          </button>
        </form>
        
        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="progress mt-4">
            <div 
              className="progress-bar" 
              role="progressbar" 
              style={{ width: `${uploadProgress}%` }} 
              aria-valuenow={uploadProgress} 
              aria-valuemin="0" 
              aria-valuemax="100"
            >
              {uploadProgress}%
            </div>
          </div>
        )}
        
        {error && (
          <div className="alert alert-danger mt-3">{error}</div>
        )}
      </div>
    </div>
  );
};

export default FileUpload;