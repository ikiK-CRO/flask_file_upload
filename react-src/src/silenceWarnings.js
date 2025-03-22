// Silence React Router deprecation warnings in tests
const originalConsoleError = console.error;
console.error = (...args) => {
  if (args[0] && typeof args[0] === 'string' &&
      (args[0].includes('Please update to React Router v7') ||
       args[0].includes('react-router-dom')) ||
       args[0].includes('Error: Not implemented: navigation')) {
    return;
  }
  originalConsoleError(...args);
};

export default function silenceWarnings() {
  // This function exists just to import the side effects
  return null;
} 