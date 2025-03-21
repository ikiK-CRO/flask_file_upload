import React from 'react';
import { render, screen } from '@testing-library/react';
import Navbar from './Navbar';
import { I18nextProvider } from 'react-i18next';
import i18n from '../i18n';

// Mock the i18n instance for tests
jest.mock('../i18n', () => ({
  changeLanguage: jest.fn(),
  language: 'en',
  t: (key) => {
    const translations = {
      'navbar.fileUpload': 'File Upload',
      'navbar.logs': 'Logs',
      'navbar.language': 'Language',
      'navbar.home': 'Home'
    };
    return translations[key] || key;
  }
}));

describe('Navbar component', () => {
  it('renders navigation links correctly', () => {
    render(
      <I18nextProvider i18n={i18n}>
        <Navbar />
      </I18nextProvider>
    );
    
    expect(screen.getByText('File Upload')).toBeInTheDocument();
    expect(screen.getByText('Logs')).toBeInTheDocument();
    expect(screen.getByText('Language')).toBeInTheDocument();
    expect(screen.getByText('Home')).toBeInTheDocument();
  });
}); 