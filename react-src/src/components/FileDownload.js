import React, { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const FileDownload = ({ fileUuid: propFileUuid, onSuccessfulDownload }) => {
  const { t } = useTranslation();
  const { fileUuid } = useParams();
  const location = useLocation();
  const [uuid, setUuid] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Extract file UUID from URL if it's not in the route params
  useEffect(() => {
    console.log('FileDownload component mounted, current URL:', window.location.href);
    console.log('Route params fileUuid:', fileUuid);
    console.log('Prop fileUuid:', propFileUuid);
    
    // Try to get UUID from different sources
    let extractedUuid = null;
    
    // 1. Try prop first (highest priority)
    if (propFileUuid) {
      console.log('Using fileUuid from props:', propFileUuid);
      extractedUuid = propFileUuid;
    } 
    // 2. Try route params
    else if (fileUuid) {
      console.log('Using fileUuid from route params:', fileUuid);
      extractedUuid = fileUuid;
    } else {
      // 3. Try query params
      const queryParams = new URLSearchParams(location.search);
      const fileParam = queryParams.get('file');
      
      // 4. Also check window location search for redirect cases
      const windowParams = new URLSearchParams(window.location.search);
      const windowFileParam = windowParams.get('file');
      
      if (fileParam) {
        console.log('Using file from query params:', fileParam);
        extractedUuid = fileParam;
      } else if (windowFileParam) {
        console.log('Using file from window query params:', windowFileParam);
        extractedUuid = windowFileParam;
      } else {
        // 5. Try to extract UUID from pathname as a last resort
        const pathMatch = window.location.pathname.match(/\/get-file\/([^\/]+)/);
        if (pathMatch && pathMatch[1]) {
          console.log('Extracted UUID from pathname:', pathMatch[1]);
          extractedUuid = pathMatch[1];
        }
      }
    }
    
    if (extractedUuid) {
      setUuid(extractedUuid);
      console.log('Final UUID set to:', extractedUuid);
    } else {
      console.error('Could not find file UUID in URL:', window.location.href);
    }
  }, [fileUuid, location, propFileUuid]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!password) {
      setError(t('Please enter a password.'));
      return;
    }
    
    if (!uuid) {
      setError(t('No file ID found. Please try again or contact support.'));
      return;
    }
    
    console.log('Attempting to download file with UUID:', uuid);
    setLoading(true);
    
    try {
      setError(null);
      
      // Make sure we're sending the password in the expected format
      const response = await axios.post(`/api/files/${uuid}`, { password }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Download response:', response.data);
      
      if (response.data.success) {
        console.log('Download successful, redirecting to:', response.data.download_url);
        
        // Call the onSuccessfulDownload callback if provided
        if (typeof onSuccessfulDownload === 'function') {
          // Start polling for log updates
          let pollCount = 0;
          const maxPolls = 5;
          const pollInterval = 1000; // 1 second
          
          const pollForLogUpdates = () => {
            setTimeout(() => {
              onSuccessfulDownload();
              pollCount++;
              if (pollCount < maxPolls) {
                pollForLogUpdates();
              }
            }, pollInterval);
          };
          
          // Initial call to refresh logs
          onSuccessfulDownload();
          // Start polling
          pollForLogUpdates();
        }
        
        // Redirect to the download URL
        window.location.href = response.data.download_url;
      } else {
        setError(response.data.message || t('An error occurred'));
      }
    } catch (err) {
      console.error('Download error:', err);
      if (err.response) {
        console.error('Error response data:', err.response.data);
        console.error('Error response status:', err.response.status);
      }
      setError(err.response?.data?.message || t('An error occurred during download.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card shadow-sm">
      <div className="card-header">
        <h2 className="mb-0">{t('Download File')}</h2>
      </div>
      <div className="card-body">
        {!uuid && (
          <div className="alert alert-warning">
            {t('File ID not found in URL. Please check the link and try again.')}
          </div>
        )}
        
        {uuid && (
          <div className="alert alert-info">
            {t('Downloading file with ID:')} <strong>{uuid}</strong>
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="password" className="form-label">{t('Enter password:')}</label>
            <input
              type="password"
              id="password"
              className="form-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={!uuid || loading}
            />
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary" 
            disabled={!uuid || loading}
          >
            {loading ? t('Processing...') : t('Download')}
          </button>
        </form>
        
        {error && (
          <div className="alert alert-danger mt-3">{error}</div>
        )}
      </div>
    </div>
  );
};

export default FileDownload;