#!/bin/bash

echo "🧪 Running Flask pytest tests..."
cd /Users/kiki/Documents/+posao/+bank/flask_file_upload
source venv/bin/activate
python -m pytest tests/ -v

echo "🧪 Running React tests..."
cd /Users/kiki/Documents/+posao/+bank/flask_file_upload/react-src
npm test -- --watchAll=false

echo "✅ All tests completed!" 