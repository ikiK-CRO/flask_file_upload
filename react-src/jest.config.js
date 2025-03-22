module.exports = {
  testEnvironment: 'jsdom',
  transformIgnorePatterns: [
    // Change the default pattern to specifically exclude axios
    "node_modules/(?!(axios)/)"
  ],
  transform: {
    "^.+\\.(js|jsx|ts|tsx)$": "babel-jest"
  },
  moduleNameMapper: {
    // Add any module name mappings if needed
  },
  setupFilesAfterEnv: ['./src/setupTests.js']
}; 