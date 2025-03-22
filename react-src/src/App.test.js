import React from 'react';
import { render } from '@testing-library/react';
import App from './App';

// Mock components used in App
jest.mock('./components/Navbar', () => () => <div data-testid="navbar-mock">Navbar Mock</div>);
jest.mock('./components/FileUpload', () => () => <div data-testid="file-upload-mock">FileUpload Mock</div>);
jest.mock('./components/FileDownload', () => () => <div data-testid="file-download-mock">FileDownload Mock</div>);
jest.mock('./components/ActivityLog', () => () => <div data-testid="activity-log-mock">ActivityLog Mock</div>);

// Mock ThemeContext
jest.mock('./ThemeContext', () => ({
  ThemeProvider: ({ children }) => <div data-testid="theme-provider-mock">{children}</div>
}));

// Mock i18next module to prevent the error
jest.mock('./i18n', () => ({
  __esModule: true,
  default: {
    t: (key) => key,
    changeLanguage: jest.fn()
  }
}));

describe('App component', () => {
  it('renders without crashing', () => {
    const { container } = render(<App />);
    expect(container).toBeInTheDocument();
  });
});
