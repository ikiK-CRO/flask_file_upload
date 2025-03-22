import React from 'react';
import { render, screen } from '@testing-library/react';
import Navbar from './Navbar';
import { ThemeContext } from '../ThemeContext';
import * as ReactRouterDom from 'react-router-dom';

// Create a proper mock for useLocation
const mockLocation = {
  pathname: '/',
  hash: '',
  search: '',
  state: null
};

// Mock useLocation directly instead of mocking the whole module
jest.spyOn(ReactRouterDom, 'useLocation').mockImplementation(() => mockLocation);

describe('Navbar component', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
  });

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