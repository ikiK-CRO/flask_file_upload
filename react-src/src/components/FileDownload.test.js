import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FileDownload from './FileDownload';
import axios from 'axios';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

// Mock axios
jest.mock('axios', () => ({
  post: jest.fn(() => Promise.resolve({ 
    data: { 
      success: true, 
      download_url: 'http://example.com/download' 
    }
  }))
}));

// Mock i18next
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key) => key // Simply return the key for testing
  })
}));

// Mock window.location
const originalLocation = window.location;
delete window.location;
window.location = {
  href: 'http://localhost/get-file/test-uuid',
  pathname: '/get-file/test-uuid',
  search: '',
  assign: jest.fn(),
  replace: jest.fn()
};

// Helper function to render with router context
const renderWithRouter = (ui, { route = '/file/test-uuid', fileUuid = 'test-uuid' } = {}) => {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="/file/:fileUuid" element={ui} />
        <Route path="*" element={ui} />
      </Routes>
    </MemoryRouter>
  );
};

describe('FileDownload component', () => {
  beforeEach(() => {
    // Clear mocks between tests
    jest.clearAllMocks();
  });

  afterAll(() => {
    window.location = originalLocation;
  });

  it('renders the file download form', () => {
    renderWithRouter(<FileDownload />);
    
    // Check for the header
    expect(screen.getByText('Download File')).toBeInTheDocument();
    
    // Check for password field
    expect(screen.getByLabelText('Enter password:')).toBeInTheDocument();
    
    // Check for download button
    expect(screen.getByRole('button', { name: 'Download' })).toBeInTheDocument();
  });

  it('shows error when trying to download without a password', async () => {
    renderWithRouter(<FileDownload />);
    
    const downloadButton = screen.getByText('Download');
    fireEvent.click(downloadButton);
    
    await waitFor(() => {
      expect(screen.getByText('Please enter a password.')).toBeInTheDocument();
    });
  });

  it('initiates download after correct password submission', async () => {
    renderWithRouter(<FileDownload />);
    
    // Enter password
    const passwordInput = screen.getByLabelText('Enter password:');
    fireEvent.change(passwordInput, { target: { value: 'test-password' } });
    
    // Submit form
    const downloadButton = screen.getByText('Download');
    fireEvent.click(downloadButton);
    
    await waitFor(() => {
      // Should call axios.post with the UUID and password
      expect(axios.post).toHaveBeenCalledWith(
        '/api/files/test-uuid',
        { password: 'test-password' },
        { headers: { 'Content-Type': 'application/json' } }
      );
      
      // Should redirect to download URL
      expect(window.location.href).toBe('http://example.com/download');
    });
  });

  it('shows error message when download fails', async () => {
    // Mock a failed download response
    axios.post.mockRejectedValueOnce({
      response: {
        data: {
          message: 'Incorrect password'
        }
      }
    });
    
    renderWithRouter(<FileDownload />);
    
    // Enter password
    const passwordInput = screen.getByLabelText('Enter password:');
    fireEvent.change(passwordInput, { target: { value: 'wrong-password' } });
    
    // Submit form
    const downloadButton = screen.getByText('Download');
    fireEvent.click(downloadButton);
    
    await waitFor(() => {
      // Should show error message
      expect(screen.getByText('Incorrect password')).toBeInTheDocument();
    });
  });
}); 