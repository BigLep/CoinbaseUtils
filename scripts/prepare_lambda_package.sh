#!/bin/bash
# Prepare Lambda deployment package

set -e

echo "Preparing Lambda deployment package..."

# Create lambda directory if it doesn't exist
mkdir -p lambda

# Copy core trading files to lambda directory
cp coinbase_trader.py lambda/
cp trading_config.json lambda/ 2>/dev/null || echo "Note: trading_config.json not found - will be handled by S3"

# Install dependencies directly in lambda directory
echo "Installing Python dependencies in lambda directory..."
pip install --target lambda -r requirements.txt

# Clean up unnecessary files to reduce package size
echo "Cleaning up unnecessary files..."
find lambda -type f -name "*.pyc" -delete
find lambda -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find lambda -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find lambda -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

echo "Lambda package prepared successfully"
echo "Contents of lambda directory:"
ls -la lambda/
echo "Package size: $(du -sh lambda | cut -f1)"