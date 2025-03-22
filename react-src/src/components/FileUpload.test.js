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
    
    // Look for the actual text in the component (from line 91 in FileUpload.js)
    expect(screen.getByText('Upload File')).toBeInTheDocument();
    
    // Check for the drag and drop instruction
    expect(screen.getByText(/drag and drop a file here/i, { exact: false })).toBeInTheDocument();
    
    // There should be a button for uploading
    expect(screen.getByRole('button', { name: 'Upload' })).toBeInTheDocument();
  });

  it('shows error when trying to upload without a file', async () => {
    render(<FileUpload />);
    
    const uploadButton = screen.getByText('Upload');
    fireEvent.click(uploadButton);
    
    await waitFor(() => {
      // The actual error message from the component (line 44)
      expect(screen.getByText('Please select a file.')).toBeInTheDocument();
    });
  });
}); 