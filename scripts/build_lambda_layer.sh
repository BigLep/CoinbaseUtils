#!/bin/bash
# Build Lambda layer with Python dependencies

set -e

echo "Building Lambda layer with dependencies..."

# Create layer directory structure
LAYER_DIR="lambda_layer/python"
mkdir -p $LAYER_DIR

# Install dependencies to layer directory
pip install --target $LAYER_DIR -r requirements.txt

# Remove unnecessary files to reduce layer size
find $LAYER_DIR -type f -name "*.pyc" -delete
find $LAYER_DIR -type d -name "__pycache__" -exec rm -rf {} +
find $LAYER_DIR -type d -name "*.dist-info" -exec rm -rf {} +
find $LAYER_DIR -type d -name "tests" -exec rm -rf {} +

echo "Lambda layer built successfully in $LAYER_DIR"
echo "Layer size: $(du -sh $LAYER_DIR | cut -f1)"