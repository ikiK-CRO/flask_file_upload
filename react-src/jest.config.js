module.exports = {
  testEnvironment: 'jsdom',
  transformIgnorePatterns: [
    // Exclude all node_modules except axios
    'node_modules/(?!(axios)/)'
  ],
  transform: {
    "^.+\\.(js|jsx|ts|tsx)$": "babel-jest"
  },
  moduleNameMapper: {
    // Add any module name mappings if needed
  },
  setupFilesAfterEnv: ['./src/setupTests.js'],
  // Add more time for tests to run
  testTimeout: 10000,
  // Avoid warnings about snapshot serialization
  snapshotSerializers: [],
  // Clear mocks automatically
  clearMocks: true
}; 