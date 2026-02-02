#!/bin/bash
# Upload trading_config.json to the S3 config bucket used by the Lambda.
# Requires .env with AWS_PROFILE (same as deploy).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if [ ! -f "$PROJECT_ROOT/.env" ]; then
  echo "❌ No .env file. Create one from .env.example and set AWS_PROFILE."
  exit 1
fi
set -a
# shellcheck source=/dev/null
source "$PROJECT_ROOT/.env"
set +a

if [ -z "${AWS_PROFILE:-}" ]; then
  echo "❌ AWS_PROFILE is not set in .env"
  exit 1
fi
export AWS_PROFILE

if [ -z "${AWS_REGION:-}" ]; then
  echo "❌ AWS_REGION is not set in .env (use same region as deploy, e.g. AWS_REGION=us-west-2)"
  exit 1
fi
export AWS_DEFAULT_REGION=$AWS_REGION

CONFIG_FILE="${1:-$PROJECT_ROOT/trading_config.json}"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ Config file not found: $CONFIG_FILE"
  exit 1
fi

BUCKET=$(aws cloudformation describe-stacks \
  --stack-name CoinbaseTradingBotStack \
  --region "$AWS_REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ConfigBucketName'].OutputValue" \
  --output text 2>/dev/null) || true

if [ -z "$BUCKET" ] || [ "$BUCKET" == "None" ]; then
  echo "❌ Could not get config bucket from stack CoinbaseTradingBotStack."
  echo "   Is the stack deployed? Use the same AWS_PROFILE as for deploy."
  exit 1
fi

echo "Uploading $CONFIG_FILE to s3://$BUCKET/trading_config.json"
aws s3 cp "$CONFIG_FILE" "s3://$BUCKET/trading_config.json"
echo "✅ Done. Lambda will use this config on the next run."
