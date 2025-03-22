module.exports = {
  moduleNameMapper: {
    // Handle CSS imports
    '\\.(css|less|scss|sass)$': '<rootDir>/src/__mocks__/styleMock.js',
    // Handle image imports
    '\\.(jpg|jpeg|png|gif|webp|svg)$': '<rootDir>/src/__mocks__/fileMock.js'
  },
  testEnvironment: 'jsdom',
  transformIgnorePatterns: [
    // Exclude all node_modules except axios
    '/node_modules/(?!axios)/'
  ],
  transform: {
    "^.+\\.(js|jsx|ts|tsx)$": "babel-jest"
  },
  setupFilesAfterEnv: ['./src/setupTests.js'],
  // Add more time for tests to run
  testTimeout: 10000,
  // Avoid warnings about snapshot serialization
  snapshotSerializers: [],
  // Clear mocks automatically
  clearMocks: true
}; 