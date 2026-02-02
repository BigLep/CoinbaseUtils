# Coinbase Trading Bot

A Python-based automated trading bot for Coinbase Advanced Trading API with AWS Lambda deployment support.

## Overview

This project implements programmatic crypto trading using the Coinbase Advanced Trading API. It supports configuration-driven trading strategies with automated deployment to AWS Lambda for scheduled execution.

## Features

- ✅ **Coinbase Advanced Trading API Integration**
- ✅ **Multi-Asset Trading Support** via JSON configuration
- ✅ **Post-Only Limit Orders** for better maker fees
- ✅ **Risk Management** with minimum price enforcement
- ✅ **Dry-Run Mode** for safe strategy testing
- ✅ **AWS Lambda Deployment** with Infrastructure as Code
- ✅ **Automated Scheduling** via EventBridge
- ✅ **Email Notifications** with execution reports
- ✅ **Secure Credential Management** via AWS Secrets Manager

## Quick Start

### Local Development

1. **Clone and install dependencies:**
   ```bash
   git clone <repository-url>
   cd CoinbaseUtils
   pip install -r requirements.txt
   ```

2. **Configure API credentials:**
   - Create API keys on [Coinbase Developer Platform](https://www.coinbase.com/cloud)
   - **Important:** Use ECDSA keys (not Ed25519) for compatibility
   - Create `.cdp_api_key.json`:
   ```json
   {
     "name": "organizations/{org_id}/apiKeys/{key_id}",
     "privateKey": "-----BEGIN EC PRIVATE KEY-----\n{key_content}\n-----END EC PRIVATE KEY-----\n"
   }
   ```

3. **Configure trading strategy:**
   ```bash
   cp trading_config.example.json trading_config.json
   # Edit trading_config.json with your parameters
   ```

4. **Test locally:**
   ```bash
   # Validate configuration
   python config_validator.py --full-check
   
   # Dry run
   python execute_trading_strategy.py --dry-run --verbose
   
   # Live trading
   python execute_trading_strategy.py
   ```

### AWS Lambda Deployment

1. **Prerequisites:**
   - **Docker** (recommended): used by the deploy script to build Lambda dependencies for Linux. Without it, Mac-built packages may fail on Lambda.
   - **AWS CLI** with a configured profile (see step 2).
   - **Node.js** and **AWS CDK**: `npm install -g aws-cdk`, then `cd cdk && npm install`. Python: `pip install aws-cdk-lib constructs`.

2. **Configure AWS profile and region (required):**
   ```bash
   # Copy .env.example to .env and set AWS_PROFILE and AWS_REGION to match your deployment
   cp .env.example .env
   # Edit .env:
   #   AWS_PROFILE=coinbase-bot
   #   AWS_REGION=us-west-2   (or the region where you deploy)

   # Configure that profile with the AWS CLI (one-time)
   aws configure --profile coinbase-bot
   ```
   All scripts (deploy, upload_config, etc.) use this profile and region so the stack, bucket, and Lambda are in one place.

3. **Deploy infrastructure:**
   ```bash
   # Deploy reads AWS_PROFILE from .env and runs the Lambda package build + CDK deploy
   ./scripts/deploy.sh

   # Optional: override notification email and region
   ./scripts/deploy.sh your-email@example.com us-east-1
   ```
   The script builds the Lambda package (using Docker when available for Linux-compatible dependencies) and deploys the stack.

4. **Configure secrets and trading config (one-time per stack):**
   ```bash
   # Get the secret and bucket from deploy output, or:
   # aws cloudformation describe-stacks --stack-name CoinbaseTradingBotStack --query 'Stacks[0].Outputs' --profile <your-profile>

   # Store Coinbase API credentials in Secrets Manager (use ARN from stack outputs)
   aws secretsmanager put-secret-value \
     --secret-id <SECRETS_ARN> \
     --secret-string '{"name":"organizations/.../apiKeys/...","privateKey":"-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----\n"}'

   # Upload trading configuration to S3 (uses AWS_PROFILE from .env, bucket from stack)
   ./scripts/upload_config.sh
   ```
   Use the same AWS profile (e.g. set `AWS_PROFILE` in .env) when running these commands.

5. **Update trading config later:**  
   After editing `trading_config.json`, upload it so the Lambda uses the new config:
   ```bash
   ./scripts/upload_config.sh
   ```
   Optional: `./scripts/upload_config.sh /path/to/other_config.json` to upload a different file.

## Project Structure

```
CoinbaseUtils/
├── coinbase_trader.py          # Main trading class
├── execute_trading_strategy.py # Configuration-driven execution
├── config_validator.py        # Configuration validation
├── trading_config.example.json # Configuration template
├── requirements.txt           # Python dependencies
├── LEARNINGS.md              # Detailed documentation
│
├── cdk/                      # AWS CDK Infrastructure
│   ├── app.py               # CDK application
│   └── stacks/
│       └── trading_bot_stack.py # Lambda, S3, SNS, EventBridge
│
├── lambda/                   # Lambda code (handler + deps; built by prepare_lambda_package.sh)
│   ├── lambda_function.py   # Lambda handler
│   ├── coinbase_trader.py   # Trading logic (copied from root)
│   └── ...                  # Dependencies installed here for Linux (Docker)
│
└── scripts/
    ├── deploy.sh            # Deploy stack (requires .env with AWS_PROFILE; runs prepare then CDK)
    ├── prepare_lambda_package.sh # Build Lambda package (Docker for Linux deps)
    └── upload_config.sh     # Upload trading_config.json to S3 (uses .env and stack bucket)
```

## Configuration

### Trading Configuration (`trading_config.json`)

```json
{
  "default_settings": {
    "order_type": "post_only_limit",
    "price_strategy": "percentage_above_market",
    "dry_run": false
  },
  "trading_pairs": [
    {
      "symbol": "FIL-USD",
      "enabled": true,
      "quantity": "1.0",
      "minimum_sell_price": "2.00",
      "price_offset_percent": 0.1,
      "description": "Filecoin trading pair"
    }
  ]
}
```

### Environment Variables

**Local / deploy (in `.env`):**

| Variable | Description | Required |
|----------|-------------|----------|
| `AWS_PROFILE` | AWS CLI profile for deploy and AWS commands | Yes |
| `AWS_REGION` | AWS region where the stack is deployed (e.g. `us-west-2`) | Yes |
| `COINBASE_API_KEY` / `COINBASE_API_SECRET` | For local runs only; Lambda uses Secrets Manager | No |

**Lambda (set by CDK):**

| Variable | Description |
|----------|-------------|
| `CONFIG_BUCKET` | S3 bucket for trading config |
| `SECRETS_ARN` | Secrets Manager ARN |
| `NOTIFICATION_TOPIC_ARN` | SNS topic for notifications |
| `LOG_LEVEL` | Logging level (`INFO`) |

## API Credentials

### Critical Requirements

1. **Use ECDSA keys** (not Ed25519) - the Advanced Trading API SDK only supports ECDSA
2. **Correct JSON format** with `name` and `privateKey` fields
3. **Proper PEM formatting** with headers/footers

### Common Issues

- ❌ Using Ed25519 keys → Authentication failure
- ❌ Missing PEM headers → Import errors
- ❌ Wrong JSON structure → Credential parsing errors

## AWS Architecture

```
EventBridge (Daily 6:15 AM UTC)
    ↓
Lambda Function (Python 3.11)
    ↓
├── Secrets Manager (API credentials)
├── S3 (Trading configuration)
└── SNS (Email notifications)
```

### AWS Resources Created

- **Lambda Function**: Trading bot execution
- **S3 Bucket**: Configuration storage
- **Secrets Manager**: Secure credential storage
- **SNS Topic**: Email notifications
- **EventBridge Rule**: Daily scheduling
- **IAM Roles**: Least-privilege permissions
- **CloudWatch**: Logging and monitoring

## Known Issues & Solutions

### Cross-Platform Dependency Building

**Issue**: Mac-built `cryptography` (and other native deps) are incompatible with AWS Lambda’s Linux environment; the real trader fails to load and the Lambda falls back to a mock.

**Solution**: The deploy script runs `prepare_lambda_package.sh`, which uses **Docker** (when available) to install dependencies inside the AWS Lambda Python 3.11 image with `--platform linux/amd64`, so the package works on Lambda. **Install Docker** and run `./scripts/deploy.sh`; no manual build step is required. If Docker is not available, the script falls back to local `pip` and will warn that Lambda may fail on Mac.

### Price Precision Errors

**Issue**: `INVALID_PRICE_PRECISION` errors when placing orders.

**Solution**: Always check `price_increment` from product details:
```python
product = client.get_product(symbol)
price_increment = float(product.price_increment)
rounded_price = round(target_price / price_increment) * price_increment
```

## Testing

```bash
# Validate configuration
python config_validator.py --full-check

# Test API connection (uses .cdp_api_key.json or .env)
python coinbase_trader.py

# Test market data
python test_fil_data.py

# Dry run trading strategy (same logic as Lambda; test locally before deploying)
python execute_trading_strategy.py --dry-run --verbose
```
Use the commands above to test config, credentials, and trading logic locally. Lambda runs the same logic (config from S3, creds from Secrets Manager) and returns a JSON-serializable summary. Test Lambda by the scheduled run or by invoking the function from the AWS console or CLI (using the same profile as deploy).

## Deployment Workflows

### Deploy to AWS
```bash
# Ensure .env exists with AWS_PROFILE set; then deploy (builds Lambda package automatically)
./scripts/deploy.sh
```
To only rebuild the Lambda package without deploying (e.g. to inspect `lambda/`): run `./scripts/prepare_lambda_package.sh` manually.

## Security Best Practices

- ✅ **Never commit credentials** to version control
- ✅ **Use AWS Secrets Manager** for production credentials
- ✅ **Implement least-privilege IAM** policies
- ✅ **Enable CloudTrail** for audit logging
- ✅ **Use VPC endpoints** for private API access
- ✅ **Regular credential rotation**

## Monitoring & Alerts

- **CloudWatch Logs**: Lambda execution logs
- **CloudWatch Metrics**: Error rates, duration, invocations
- **SNS Notifications**: Email reports after each execution
- **CloudWatch Alarms**: Error threshold alerts

## Cost Optimization

- **Lambda**: Pay-per-execution, typically <$1/month for daily execution
- **S3**: Minimal storage costs for configuration
- **Secrets Manager**: ~$0.40/month per secret
- **SNS**: ~$0.50/month for email notifications

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test thoroughly with dry-run mode
4. Submit a pull request with detailed description

## Support

- 📖 **Documentation**: See [LEARNINGS.md](LEARNINGS.md) for detailed insights
- 🐛 **Issues**: Create GitHub issues for bugs or feature requests
- 📧 **API Support**: [Coinbase Advanced Trading API Docs](https://docs.cdp.coinbase.com/advanced-trade/docs/getting-started)

## License

This project is for educational and personal use. Ensure compliance with Coinbase's Terms of Service and applicable financial regulations.

---

**⚠️ Trading Disclaimer**: Cryptocurrency trading involves significant risk. This bot is provided as-is without warranties. Always test thoroughly in dry-run mode before live trading. Never trade more than you can afford to lose.