import React from 'react';
import { render, screen } from '@testing-library/react';
import Navbar from './Navbar';
import { ThemeContext } from '../ThemeContext';

// Tell Jest to use the mock
jest.mock('react-router-dom');

describe('Navbar component', () => {
  it('renders navigation links correctly', () => {
    // Mock theme context
    const mockTheme = {
      theme: 'light',
      toggleTheme: jest.fn()
    };
    
    const mockNavigate = jest.fn();
    
    // Render with mocked providers
    render(
      <ThemeContext.Provider value={mockTheme}>
        <Navbar navigateWithoutFileParam={mockNavigate} />
      </ThemeContext.Provider>
    );
    
    // Check if links are rendered
    expect(screen.getByText(/home/i)).toBeInTheDocument();
    expect(screen.getByText(/activity log/i, { exact: false })).toBeInTheDocument();
  });
}); 