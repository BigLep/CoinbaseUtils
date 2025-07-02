#!/bin/bash
"""
Deploy Coinbase Trading Bot to AWS
"""

set -e

# Configuration
NOTIFICATION_EMAIL=${1:-"your-email@example.com"}
AWS_REGION=${2:-"us-east-1"}

echo "=== Coinbase Trading Bot Deployment ==="
echo "Notification Email: $NOTIFICATION_EMAIL"
echo "AWS Region: $AWS_REGION"
echo ""

# Check AWS credentials
echo "Checking AWS credentials..."
aws sts get-caller-identity || {
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
}

# Build Lambda layer
echo "Building Lambda layer..."
./scripts/build_lambda_layer.sh

# Prepare Lambda package
echo "Preparing Lambda package..."
./scripts/prepare_lambda_package.sh

# Bootstrap CDK (if needed)
echo "Bootstrapping CDK..."
cd cdk
cdk bootstrap --context notification_email="$NOTIFICATION_EMAIL" --context region="$AWS_REGION"

# Deploy stack
echo "Deploying CDK stack..."
cdk deploy --require-approval never \
    --context notification_email="$NOTIFICATION_EMAIL" \
    --context region="$AWS_REGION"

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Next steps:"
echo "1. Update Secrets Manager with your Coinbase API credentials"
echo "2. Upload your trading_config.json to the S3 bucket"
echo "3. Confirm email subscription for notifications"
echo ""
echo "To get the resource details, run:"
echo "  aws cloudformation describe-stacks --stack-name CoinbaseTradingBotStack --query 'Stacks[0].Outputs'"