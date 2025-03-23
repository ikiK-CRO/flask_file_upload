import React, { useEffect, useState } from 'react';
import { HashRouter as Router, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import './i18n';
import { ThemeProvider } from './ThemeContext';

// Components
import Navbar from './components/Navbar';
import FileUpload from './components/FileUpload';
import FileDownload from './components/FileDownload';
import ActivityLog from './components/ActivityLog';

function MainContent() {
  const location = useLocation();
  const navigate = useNavigate();
  const [showComponent, setShowComponent] = useState('upload');
  const [fileUuid, setFileUuid] = useState(null);
  const activityLogRef = React.useRef(null);
  
  // Custom navigation function that clears file parameter
  const navigateWithoutFileParam = (path) => {
    // Clear file UUID when navigating to home
    if (path === '/') {
      setFileUuid(null);
      setShowComponent('upload');
      window.history.replaceState({}, '', '/'); // Remove query params
    }
    navigate(path);
  };
  
  // Function to refresh logs from outside the ActivityLog component
  const refreshLogs = () => {
    console.log('Refreshing logs from App component');
    if (activityLogRef.current && typeof activityLogRef.current.fetchLogs === 'function') {
      activityLogRef.current.fetchLogs();
    }
  };
  
  useEffect(() => {
    console.log('Current location changed:', location);
    
    // Extract file UUID from URL parameters
    const windowParams = new URLSearchParams(window.location.search);
    const fileParam = windowParams.get('file');
    
    if (fileParam) {
      console.log('File UUID found in URL:', fileParam);
      setFileUuid(fileParam);
    }
    
    // Determine which component to show based on hash and parameters
    if (location.pathname === '/logs' || location.hash === '#/logs') {
      console.log('Showing logs component');
      setShowComponent('logs');
    } else if (location.pathname === '/' || location.hash === '#/' || location.hash === '') {
      // Only show upload on home page if no file parameter
      if (fileParam) {
        console.log('Showing download component (home with file)');
        setShowComponent('download');
      } else {
        console.log('Showing upload component (home)');
        setShowComponent('upload');
      }
    }
  }, [location]);
  
  return (
    <>
      <Navbar navigateWithoutFileParam={navigateWithoutFileParam} />
      <div className="row mt-4">
        <div className="col-12">
          {showComponent === 'upload' && <FileUpload onSuccessfulUpload={refreshLogs} />}
          {showComponent === 'download' && <FileDownload fileUuid={fileUuid} onSuccessfulDownload={refreshLogs} />}
          {showComponent === 'logs' && <ActivityLog ref={activityLogRef} />}
        </div>
      </div>
    </>
  );
}

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="container py-4 main-container">
          <Routes>
            <Route path="*" element={<MainContent />} />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
