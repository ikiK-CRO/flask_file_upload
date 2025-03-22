import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';
import { BrowserRouter } from 'react-router-dom';
import { ThemeContext } from './ThemeContext';

// Mock ThemeContext
const mockThemeContext = {
  theme: 'light',
  toggleTheme: jest.fn()
};

// Mock i18next module to prevent the error
jest.mock('./i18n', () => ({
  // Add any properties used by the component
  __esModule: true,
  default: {
    t: (key) => key,
    changeLanguage: jest.fn()
  }
}));

test('renders the app', () => {
  render(
    <ThemeContext.Provider value={mockThemeContext}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ThemeContext.Provider>
  );
  
  // Minimal test to check app renders without crashing
  expect(document.body).toBeInTheDocument();
});
