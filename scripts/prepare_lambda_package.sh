#!/bin/bash
# Prepare Lambda deployment package
# Uses uv to install prebuilt Linux (manylinux x86_64) wheels for the Lambda Python version,
# so cryptography works on Lambda even when building on a Mac. No Docker needed.
# (Mac-built wheels are incompatible with Lambda and cause "Mock trader" fallback every run.)

set -e

# Keep in sync with the runtime in cdk/stacks/trading_bot_stack.py
LAMBDA_PYTHON_VERSION="3.14"

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
if ! command -v uv &>/dev/null; then
    echo "❌ uv not found. Install it: brew install uv (or see https://docs.astral.sh/uv/)"
    exit 1
fi
echo "Installing Python dependencies for Lambda (Python $LAMBDA_PYTHON_VERSION, linux x86_64) with uv..."
# --only-binary: fail rather than build an sdist for the wrong OS
uv pip install \
    --target lambda \
    --python-version "$LAMBDA_PYTHON_VERSION" \
    --python-platform x86_64-manylinux2014 \
    --only-binary :all: \
    -r requirements.txt

# Clean up unnecessary files to reduce package size
echo "Cleaning up unnecessary files..."
find lambda -type f -name "*.pyc" -delete
rm -f lambda/.lock  # uv --target lock file
find lambda -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find lambda -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find lambda -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

echo "Lambda package prepared successfully"
echo "Contents of lambda directory:"
ls -la lambda/
echo "Package size: $(du -sh lambda | cut -f1)"