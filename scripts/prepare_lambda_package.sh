#!/bin/bash
"""
Prepare Lambda deployment package
"""

set -e

echo "Preparing Lambda deployment package..."

# Create lambda directory if it doesn't exist
mkdir -p lambda

# Copy core trading files to lambda directory
cp coinbase_trader.py lambda/
cp trading_config.json lambda/ 2>/dev/null || echo "Note: trading_config.json not found - will be handled by S3"

# Copy lambda handler (already exists)
# lambda_function.py should already be in lambda/ directory

echo "Lambda package prepared successfully"
echo "Contents of lambda directory:"
ls -la lambda/