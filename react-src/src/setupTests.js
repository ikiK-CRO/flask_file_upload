// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';
import './silenceWarnings';

// Mock for document.cookie
Object.defineProperty(document, 'cookie', {
  writable: true,
  value: '',
});

// Mock react-router-dom - use less intrusive mocking
jest.mock('react-router-dom', () => {
  const originalModule = jest.requireActual('react-router-dom');
  return {
    ...originalModule,
    useLocation: jest.fn().mockReturnValue({
      pathname: '/',
      hash: '',
      search: '',
      state: null
    }),
    useNavigate: jest.fn().mockReturnValue(jest.fn())
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
