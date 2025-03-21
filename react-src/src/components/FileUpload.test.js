import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FileUpload from './FileUpload';
import { I18nextProvider } from 'react-i18next';
import i18n from '../i18n';

// Mock i18n
jest.mock('../i18n', () => ({
  changeLanguage: jest.fn(),
  language: 'en',
  t: (key) => {
    const translations = {
      'fileUpload.title': 'File Upload',
      'fileUpload.dragDrop': 'Drag and drop a file here or click to select a file',
      'fileUpload.password': 'Password',
      'fileUpload.passwordPlaceholder': 'Enter password to protect your file',
      'fileUpload.upload': 'Upload',
      'fileUpload.uploading': 'Uploading...',
      'fileUpload.success': 'Upload successful!',
      'fileUpload.error': 'Upload failed'
    };
    return translations[key] || key;
  }
}));

// Mock fetch
global.fetch = jest.fn();

describe('FileUpload component', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('renders the file upload form correctly', () => {
    render(
      <I18nextProvider i18n={i18n}>
        <FileUpload />
      </I18nextProvider>
    );
    
    expect(screen.getByText('File Upload')).toBeInTheDocument();
    expect(screen.getByText('Drag and drop a file here or click to select a file')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter password to protect your file')).toBeInTheDocument();
    expect(screen.getByText('Upload')).toBeInTheDocument();
  });

  it('shows error when trying to upload without a file', async () => {
    render(
      <I18nextProvider i18n={i18n}>
        <FileUpload />
      </I18nextProvider>
    );
    
    const uploadButton = screen.getByText('Upload');
    fireEvent.click(uploadButton);
    
    await waitFor(() => {
      expect(screen.getByText('Please select a file')).toBeInTheDocument();
    });
  });
}); 