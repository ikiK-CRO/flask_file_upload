import React from 'react';
import { render, screen } from '@testing-library/react';
import Navbar from './Navbar';
import { BrowserRouter } from 'react-router-dom';
import { ThemeContext } from '../ThemeContext';

// Mock ThemeContext
const mockThemeContext = {
  theme: 'light',
  toggleTheme: jest.fn()
};

// Mock for navigateWithoutFileParam
const mockNavigateWithoutFileParam = jest.fn();

// Wrap component with necessary providers
const renderWithProviders = (ui) => {
  return render(
    <ThemeContext.Provider value={mockThemeContext}>
      <BrowserRouter>
        {ui}
      </BrowserRouter>
    </ThemeContext.Provider>
  );
};

describe('Navbar component', () => {
  it('renders navigation links correctly', () => {
    renderWithProviders(<Navbar navigateWithoutFileParam={mockNavigateWithoutFileParam} />);
    
    // Using regex to make the test more flexible with translations
    expect(screen.getByText(/home/i)).toBeInTheDocument();
    expect(screen.getByText(/activity log/i, { exact: false })).toBeInTheDocument();
  });
}); 