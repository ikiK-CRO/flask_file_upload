#!/bin/bash

# Install Flask-CORS
pip install -r requirements.txt

# Install React dependencies
cd react-src
npm install

# Build React app to Flask static directory
npm run build

# Create static/react directory if it doesn't exist
mkdir -p ../static/react

# Copy build files to static/react
cp -r build/* ../static/react/

echo "React build completed and copied to static/react"

# Return to project root
cd ..

# Start Flask app (for development)
echo "Starting Flask app..."
python app.py
