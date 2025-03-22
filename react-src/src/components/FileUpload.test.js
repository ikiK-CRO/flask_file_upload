import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FileUpload from './FileUpload';

// Mock axios
jest.mock('axios', () => ({
  post: jest.fn(() => Promise.resolve({ data: { success: true, file_id: 'test-file-id' } }))
}));

describe('FileUpload component', () => {
  beforeEach(() => {
    // Clear mocks between tests
    jest.clearAllMocks();
  });

  it('renders the file upload form', () => {
    render(<FileUpload />);
    
    // We're using the i18n keys directly from the mock
    expect(screen.getByText(/file upload/i, { exact: false })).toBeInTheDocument();
    expect(screen.getByText(/drag and drop/i, { exact: false })).toBeInTheDocument();
    
    // There should be a button for uploading
    expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument();
  });

  it('shows error when trying to upload without a file', async () => {
    render(<FileUpload />);
    
    const uploadButton = screen.getByText('Upload');
    fireEvent.click(uploadButton);
    
    await waitFor(() => {
      // Use regex to be more flexible with punctuation
      expect(screen.getByText(/please select a file/i)).toBeInTheDocument();
    });
  });
}); 