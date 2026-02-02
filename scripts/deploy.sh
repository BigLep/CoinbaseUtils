#!/bin/bash
# Deploy Coinbase Trading Bot to AWS
# Requires .env with AWS_PROFILE=your-profile (no default).
# Configure the profile with: aws configure --profile <name>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Source .env (required for AWS_PROFILE)
if [ ! -f "$PROJECT_ROOT/.env" ]; then
  echo "❌ No .env file. Create one from .env.example and set AWS_PROFILE=your-profile"
  exit 1
fi
set -a
# shellcheck source=/dev/null
source "$PROJECT_ROOT/.env"
set +a

if [ -z "${AWS_PROFILE:-}" ]; then
  echo "❌ AWS_PROFILE is not set. Add AWS_PROFILE=your-profile to .env"
  exit 1
fi
export AWS_PROFILE

if [ -z "${AWS_REGION:-}" ]; then
  echo "❌ AWS_REGION is not set. Add AWS_REGION=us-west-2 (or your region) to .env"
  exit 1
fi

# Optional overrides from command line: ./scripts/deploy.sh [email] [region]
NOTIFICATION_EMAIL=${1:-"your-email@example.com"}
if [ -n "${2:-}" ]; then AWS_REGION=$2; fi
export AWS_DEFAULT_REGION=$AWS_REGION

echo "=== Coinbase Trading Bot Deployment ==="
echo "AWS Profile: $AWS_PROFILE"
echo "Notification Email: $NOTIFICATION_EMAIL"
echo "AWS Region: $AWS_REGION"
echo ""

# Check AWS credentials (uses $AWS_PROFILE)
echo "Checking AWS credentials..."
aws sts get-caller-identity || {
    echo "❌ AWS credentials not configured for profile '$AWS_PROFILE'."
    echo "   Run: aws configure --profile $AWS_PROFILE"
    exit 1
}

# Prepare Lambda package (with bundled dependencies)
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