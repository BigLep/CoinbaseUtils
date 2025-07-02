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
   ```bash
   # Install AWS CDK
   npm install -g aws-cdk
   
   # Install Python dependencies
   cd cdk && npm install
   pip install aws-cdk-lib constructs
   ```

2. **Deploy infrastructure:**
   ```bash
   # Configure AWS credentials
   aws configure
   
   # Deploy to AWS
   ./scripts/deploy.sh
   ```

3. **Configure secrets and trading config:**
   ```bash
   # Store API credentials in Secrets Manager
   aws secretsmanager put-secret-value \
     --secret-id <SECRET_ARN> \
     --secret-string '{"name":"organizations/.../apiKeys/...","privateKey":"-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----\n"}'
   
   # Upload trading configuration to S3
   aws s3 cp trading_config.json s3://<BUCKET_NAME>/trading_config.json
   ```

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
├── lambda/                   # AWS Lambda code
│   ├── lambda_function.py   # Lambda handler
│   ├── coinbase_trader.py   # Trading logic (copied)
│   └── trading_config.json  # Config (uploaded to S3)
│
└── scripts/                  # Deployment scripts
    ├── deploy.sh            # Main deployment script
    └── prepare_lambda_package.sh # Lambda package builder
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

| Variable | Description | Default |
|----------|-------------|---------|
| `CONFIG_BUCKET` | S3 bucket for trading config | Set by CDK |
| `SECRETS_ARN` | Secrets Manager ARN | Set by CDK |
| `NOTIFICATION_TOPIC_ARN` | SNS topic for notifications | Set by CDK |
| `LOG_LEVEL` | Logging level | `INFO` |

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

**Issue**: Mac-built `cryptography` library incompatible with AWS Lambda Linux environment.

**Solutions**:
1. **GitHub Actions CI/CD** (Recommended):
   ```yaml
   # .github/workflows/deploy.yml
   - name: Build Lambda package
     run: |
       pip install --target lambda -r requirements.txt
       # Builds in Linux environment
   ```

2. **Docker-based local development**:
   ```bash
   docker run --rm -v $(pwd):/app amazonlinux:2 bash -c "
     yum install -y python3 python3-pip && 
     cd /app && 
     pip3 install --target lambda -r requirements.txt
   "
   ```

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

# Test API connection
python coinbase_trader.py

# Test market data
python test_fil_data.py

# Dry run trading strategy
python execute_trading_strategy.py --dry-run --verbose

# Test Lambda function locally (requires Docker)
docker run --rm -p 9000:8080 coinbase-trading-bot:latest
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'
```

## Deployment Workflows

### Local Development → AWS
```bash
# Build Lambda package
./scripts/prepare_lambda_package.sh

# Deploy infrastructure
./scripts/deploy.sh
```

### GitHub Actions CI/CD (Recommended)
```bash
# Push to GitHub triggers automatic deployment
git push origin main
```

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