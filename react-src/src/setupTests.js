// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';
import './silenceWarnings';

// Add transformIgnorePatterns setting to fix axios import issues
if (typeof window !== 'undefined') {
  // This code only runs in the browser context (during tests)
  window.jest = window.jest || {};
  window.jest.transformIgnorePatterns = ['node_modules/(?!(axios)/)'];
}

// Mock for document.cookie
Object.defineProperty(document, 'cookie', {
  writable: true,
  value: '',
});

// Setup consistent react-router-dom mocks for all tests
jest.mock('react-router-dom', () => {
  // Create mock location and navigation
  const mockLocation = {
    pathname: '/',
    hash: '',
    search: '',
    state: null
  };
  
  const mockNavigate = jest.fn();
  
  // Return mocked module
  return {
    ...jest.requireActual('react-router-dom'),
    useLocation: jest.fn().mockReturnValue(mockLocation),
    useNavigate: jest.fn().mockReturnValue(mockNavigate),
    Link: ({ children, to }) => <a href={to}>{children}</a>,
    HashRouter: ({ children }) => <div>{children}</div>,
    Routes: ({ children }) => <div>{children}</div>,
    Route: ({ children }) => <div>{children}</div>
  };
});

// Mock i18next and react-i18next
jest.mock('i18next', () => ({
  init: () => Promise.resolve(),
  use: () => ({ init: () => Promise.resolve() }),
  t: (key) => key,
  changeLanguage: () => Promise.resolve(),
  language: 'en'
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key) => key,
    i18n: {
      changeLanguage: () => Promise.resolve(),
      language: 'en'
    }
  }),
  Trans: ({ children }) => children,
  withTranslation: () => Component => {
    Component.defaultProps = { ...Component.defaultProps, t: (str) => str };
    return Component;
  },
  initReactI18next: {
    type: '3rdParty',
    init: () => {}
  },
  I18nextProvider: ({ children }) => children
}));
