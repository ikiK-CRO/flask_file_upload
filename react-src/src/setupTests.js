// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Mock i18next
jest.mock('react-i18next', () => ({
  // this mock makes sure any components using the translate hook can use it without a warning being shown
  useTranslation: () => {
    return {
      t: (str) => str,
      i18n: {
        changeLanguage: () => new Promise(() => {}),
        language: 'en'
      }
    };
  },
  // mock Trans component
  Trans: ({ children }) => children,
  // mock withTranslation HOC
  withTranslation: () => Component => {
    Component.defaultProps = { ...Component.defaultProps, t: (str) => str };
    return Component;
  },
  // mock I18nextProvider component
  I18nextProvider: ({ children }) => children
}));
