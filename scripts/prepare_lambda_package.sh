#!/bin/bash
# Prepare Lambda deployment package
# Uses Docker to install dependencies for Amazon Linux so cryptography works on Lambda.
# (Mac-built wheels are incompatible with Lambda and cause "Mock trader" fallback every run.)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Preparing Lambda deployment package..."

# Create lambda directory if it doesn't exist
mkdir -p lambda

# Copy core trading files to lambda directory (lambda_function.py stays in lambda/)
cp coinbase_trader.py lambda/
cp trading_config.json lambda/ 2>/dev/null || echo "Note: trading_config.json not found - will be handled by S3"

# Install dependencies for Linux (required for cryptography on Lambda)
if command -v docker &>/dev/null; then
    echo "Installing Python dependencies in Docker (Amazon Linux / Lambda runtime)..."
    # Use linux/amd64 so wheels work on default Lambda (x86_64); avoids ARM-only wheels on M1/M2 Macs
    docker run --rm --platform linux/amd64 --entrypoint pip \
        -v "$PROJECT_ROOT:/var/task" \
        -w /var/task \
        public.ecr.aws/lambda/python:3.11 \
        install --target lambda -r requirements.txt
else
    echo "WARNING: Docker not found. Installing with local pip."
    echo "If you are on Mac, Lambda may fail (cryptography built for wrong OS)."
    pip install --target lambda -r requirements.txt
fi

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