import React from 'react';
import { render, screen } from '@testing-library/react';
import Navbar from './Navbar';
import { ThemeContext } from '../ThemeContext';

// Mock components and hooks used in Navbar to avoid routing issues
jest.mock('react-router-dom', () => ({
  useLocation: jest.fn().mockReturnValue({
    pathname: '/',
    hash: '',
    search: '',
    state: null
  }),
  Link: ({ children }) => <span>{children}</span>
}));

describe('Navbar component', () => {
  it('renders navigation links correctly', () => {
    // Create mock context value
    const mockContext = {
      theme: 'light',
      toggleTheme: jest.fn()
    };
    
    // Create mock prop
    const mockNavigate = jest.fn();

    // Render with context provider
    render(
      <ThemeContext.Provider value={mockContext}>
        <Navbar navigateWithoutFileParam={mockNavigate} />
      </ThemeContext.Provider>
    );
    
    // Check if basic elements are rendered
    expect(screen.getByText(/home/i)).toBeInTheDocument();
    expect(screen.getByText(/activity log/i, { exact: false })).toBeInTheDocument();
  });
}); 