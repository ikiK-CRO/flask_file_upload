import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ActivityLog from './ActivityLog';
import axios from 'axios';

// Mock axios
jest.mock('axios', () => ({
  get: jest.fn(),
  post: jest.fn()
}));

// Mock successful log data
const mockLogData = {
  success: true,
  files: [
    { id: 'file-1', file_name: 'test-file.pdf', upload_date: '2023-03-21', download_count: 5 },
    { id: 'file-2', file_name: 'example.doc', upload_date: '2023-03-22', download_count: 3 }
  ],
  upload_logs: [
    { timestamp: '2023-03-21 10:00:00', message: 'File uploaded: test-file.pdf' }
  ],
  download_logs: [
    { timestamp: '2023-03-21 11:00:00', message: 'File downloaded: test-file.pdf' }
  ]
};

// Mock i18next
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key) => key // Simply return the key for testing
  })
}));

describe('ActivityLog component', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Default successful response
    axios.get.mockResolvedValue({ data: mockLogData });
  });

  it('renders the activity log component with tabs', async () => {
    render(<ActivityLog />);
    
    // Should show loading initially
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Files')).toBeInTheDocument();
    });
    
    // Tabs should be visible
    expect(screen.getByText('Files')).toBeInTheDocument();
    expect(screen.getByText('Upload Logs')).toBeInTheDocument();
    expect(screen.getByText('Download Logs')).toBeInTheDocument();
  });

  it('displays file list after loading', async () => {
    render(<ActivityLog />);
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // File list should be visible (default tab)
    expect(screen.getByText('test-file.pdf')).toBeInTheDocument();
    expect(screen.getByText('example.doc')).toBeInTheDocument();
  });

  it('switches between tabs when clicked', async () => {
    render(<ActivityLog />);
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Check files tab content is displayed first
    expect(screen.getByText('test-file.pdf')).toBeInTheDocument();
    
    // Click on Upload Logs tab
    fireEvent.click(screen.getByText('Upload Logs'));
    
    // Should show upload logs
    await waitFor(() => {
      expect(screen.getByText(/File uploaded: test-file.pdf/i)).toBeInTheDocument();
    });
    
    // Click on Download Logs tab
    fireEvent.click(screen.getByText('Download Logs'));
    
    // Should show download logs
    await waitFor(() => {
      expect(screen.getByText(/File downloaded: test-file.pdf/i)).toBeInTheDocument();
    });
  });

  it('shows error message when API request fails', async () => {
    // Mock API failure
    axios.get.mockRejectedValue({ 
      response: { 
        data: { message: 'Failed to load logs' } 
      } 
    });
    
    render(<ActivityLog />);
    
    // Wait for error to show
    await waitFor(() => {
      expect(screen.getByText('Failed to load logs')).toBeInTheDocument();
    });
  });
}); 