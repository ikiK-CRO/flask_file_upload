import React, { useContext } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ThemeContext } from '../ThemeContext';

const Navbar = ({ navigateWithoutFileParam }) => {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const { theme, toggleTheme } = useContext(ThemeContext);
  
  const changeLanguage = (lang) => {
    i18n.changeLanguage(lang);
    document.cookie = `lang=${lang};path=/;max-age=31536000`;
  };
  
  // Check if a path is active - works with hash router
  const isActive = (path) => {
    // Add safety check for tests when location might be undefined
    if (!location) return false;
    
    if (path === '/') {
      return location.pathname === '/' || location.hash === '#/' || location.hash === '';
    }
    return location.pathname === path || location.hash === `#${path}`;
  };
  
  // Handle navigation
  const handleNavClick = (e, path) => {
    e.preventDefault();
    if (navigateWithoutFileParam) {
      navigateWithoutFileParam(path);
    }
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark rounded mb-4">
      <div className="container-fluid">
        <a className="navbar-brand" href="/" onClick={(e) => handleNavClick(e, '/')}>
          {t('File Sharing System')}
        </a>
        <button 
          className="navbar-toggler" 
          type="button" 
          data-bs-toggle="collapse" 
          data-bs-target="#navbarNav"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav me-auto">
            <li className="nav-item">
              <a 
                className={`nav-link fw-bold fs-5 ${isActive('/') ? 'active' : ''}`} 
                href="/"
                onClick={(e) => handleNavClick(e, '/')}
              >
                {t('Home')}
              </a>
            </li>
            <li className="nav-item">
              <a 
                className={`nav-link fw-bold fs-5 ${isActive('/logs') ? 'active' : ''}`}
                href="/logs"
                onClick={(e) => handleNavClick(e, '/logs')}
              >
                {t('Activity Log')}
              </a>
            </li>
          </ul>
          <div className="d-flex align-items-center">
            {/* Theme Toggle */}
            <div className="me-3">
              <label className="theme-toggle">
                <input 
                  type="checkbox" 
                  onChange={toggleTheme} 
                  checked={theme === 'dark'}
                />
                <span className="slider">
                  {theme === 'dark' ? (
                    <span className="d-none">{t('Light Mode')}</span>
                  ) : (
                    <span className="d-none">{t('Dark Mode')}</span>
                  )}
                </span>
              </label>
            </div>
            
            {/* Language Switchers */}
            <button 
              className={`btn ${i18n.language === 'hr' ? 'btn-light' : 'btn-outline-light'} me-2 fw-bold`}
              onClick={() => changeLanguage('hr')}
              style={{ minWidth: '45px' }}
            >
              HR
            </button>
            <button 
              className={`btn ${i18n.language === 'en' ? 'btn-light' : 'btn-outline-light'} fw-bold`}
              onClick={() => changeLanguage('en')}
              style={{ minWidth: '45px' }}
            >
              EN
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;