# Coinbase Advanced Trading API - Key Learnings

## Project Overview
This project implements programmatic crypto trading using the Coinbase Advanced Trading API with Python. The goal is to build a system that can place limit sell orders for crypto assets.

## Key Learnings

### 1. API Choice: Advanced Trading vs CDP SDK
- **Initial Confusion**: There are multiple Coinbase APIs/SDKs available:
  - **CDP SDK** (`cdp-sdk`): For on-chain wallet operations and decentralized trading
  - **Advanced Trading API** (`coinbase-advanced-py`): For centralized exchange trading on Coinbase
- **Correct Choice**: For programmatic trading on Coinbase exchange, use the **Advanced Trading API**
- **Package**: `coinbase-advanced-py>=1.5.0`

### 2. API Credentials Format & Key Type
- **Critical Issue**: API credentials must be in the correct format for authentication to work
- **Key Type Requirement**: Must use **ECDSA (old) API keys** instead of **Ed25519 (new) API keys**
  - The Advanced Trading API SDK currently only supports ECDSA keys
  - Ed25519 keys will cause authentication failures
  - When creating API keys, select "ECDSA" algorithm option
- **Required Format**:
  ```json
  {
    "name": "organizations/{org_id}/apiKeys/{key_id}",
    "privateKey": "-----BEGIN EC PRIVATE KEY-----\n{key_content}\n-----END EC PRIVATE KEY-----\n"
  }
  ```
- **Common Mistakes**:
  - **Using Ed25519 keys instead of ECDSA keys** ⚠️ **Most Important**
  - Using just the key ID instead of the full `organizations/{org_id}/apiKeys/{key_id}` format
  - Missing PEM headers/footers (`-----BEGIN EC PRIVATE KEY-----` and `-----END EC PRIVATE KEY-----`)
  - Using base64 string without proper PEM formatting

### 3. Authentication Process
- **Method**: CDP API keys use JWT-based authentication with Bearer tokens
- **SDK Handles**: The `coinbase-advanced-py` SDK automatically handles JWT generation and authentication
- **Initialization Options**:
  ```python
  # Option 1: Using JSON key file (recommended)
  client = RESTClient(key_file=".cdp_api_key.json")
  
  # Option 2: Direct credentials
  client = RESTClient(api_key=api_key, api_secret=api_secret)
  ```

### 4. Response Object Handling
- **Issue**: SDK returns response objects, not plain dictionaries
- **Solution**: Access data through object attributes, not dictionary keys
  ```python
  # Correct
  accounts.accounts
  account.currency
  account.available_balance
  
  # Incorrect
  accounts['accounts']
  account['currency']
  ```

### 5. Price Precision Requirements
- **Critical**: Each trading pair has specific price precision requirements
- **Key Fields**: Check `price_increment` in product details
- **Example**: FIL-USD requires 3 decimal places (0.001 increment)
- **Solution**: Always round prices to the correct increment:
  ```python
  price_increment = float(product.price_increment)
  rounded_price = round(target_price / price_increment) * price_increment
  ```
- **Error**: `INVALID_PRICE_PRECISION` if wrong decimal places used

### 6. Order Response Structure
- **Order Success**: Check `order.success` boolean field
- **Order Errors**: Access via `order.error_response.error` and `order.error_response.message`
- **No Direct Order ID**: Successful orders don't return order ID in immediate response
- **Post-Only Orders**: Use `post_only=True` parameter for maker-only orders (better fees)

### 7. Security Best Practices
- **Credentials**: Never commit API credentials to version control
- **File Protection**: Added to `.gitignore`:
  - `.env` (and `.env.example` is the template only)
  - `.cdp_api_key.json`
  - `trading_config.json`
  - `test_*.py` (test scripts may contain temporary credentials)
- **Production**: Use AWS Secrets Manager for Lambda; use `.cdp_api_key.json` or `.env` only for local runs

### 8. Development Workflow & Git Practices
1. **Start with Sandbox**: Use sandbox/testnet environment for initial testing
2. **Verify Connection**: Test basic API calls (get accounts, get products) before trading
3. **Small Orders**: Start with minimal order sizes when testing trading functionality (we used 1 FIL)
4. **Price Precision**: Always check product details for correct decimal places before placing orders
5. **Test Market Data**: Verify price feeds work before implementing trading logic
6. **Error Handling**: Implement comprehensive error handling for all API calls
7. **Order Validation**: Test with small amounts first, then scale up
8. **Code Consolidation**: Remove redundant scripts when flexible systems replace hardcoded ones
9. **Commit Strategy**: **ALWAYS commit each feature/change immediately after implementation**
   - User expectation: Make a change, then commit it
   - Enables Claude Code restart with full context preservation
   - Follows atomic commit principles for feature tracking
   - Required for maintaining development state across sessions

### 9. Configuration System Architecture
- **JSON-Based Configuration**: External `trading_config.json` for strategy parameters
- **Multi-Asset Support**: Configure multiple trading pairs with individual settings
- **Risk Management**: Built-in minimum price checks and balance validation
- **Template System**: `trading_config.example.json` provides configuration template
- **Validation Pipeline**: Comprehensive validation before order execution
- **Dry-Run Capability**: Test strategies without placing actual orders

### 10. Order Management and Tracking
- **Order ID Structure**: Coinbase uses UUIDs for both order_id and client_order_id
- **Order URLs**: Orders viewable at https://www.coinbase.com/orders
- **Query Parameters**: Custom orderId parameter for easy order identification
- **URL Format**: `https://www.coinbase.com/orders?orderId={order_id}`
- **Order Response**: Successful orders return success_response with order details
- **Order Tracking**: System logs order ID, client ID, and direct URL with query parameter
- **Search Capability**: Order IDs can be searched in Coinbase interface or via URL parameter

### 11. Production Trading Insights
- **Post-Only Orders**: Always use for better maker fees when possible
- **Price Calculations**: Implement percentage-based pricing for dynamic strategies
- **Market Data**: Use `get_product()` method for current prices (includes price + volume data)
- **Order Types**: GTC (Good Till Cancelled) orders stay active until filled or cancelled
- **Fee Optimization**: Post-only orders typically have lower fees than market orders
- **Configuration-Driven**: Change trading parameters without code modifications
- **Order Visibility**: All orders logged with direct URLs for immediate access

## Project Structure
```
CoinbaseUtils/
├── coinbase_trader.py          # Main trading class (local + copied to lambda/)
├── execute_trading_strategy.py # Configuration-driven execution (local)
├── config_validator.py        # Configuration validation
├── trading_config.json        # Active config (not in git; upload to S3 via upload_config.sh)
├── trading_config.example.json # Configuration template
├── .cdp_api_key.json          # API credentials (not in git)
├── .env                        # AWS_PROFILE, AWS_REGION, optional Coinbase (not in git)
├── .env.example                # Template: AWS_PROFILE, AWS_REGION, Coinbase placeholders
├── requirements.txt            # Python dependencies
├── cdk/                        # AWS CDK (Lambda, S3, Secrets Manager, SNS, EventBridge)
├── lambda/                     # Lambda handler + deps (built by prepare_lambda_package.sh)
│   ├── lambda_function.py      # Handler; uses _run_strategy, _serializable_result
│   └── coinbase_trader.py      # Copy of trader (supports name or id in key file)
├── scripts/
│   ├── deploy.sh               # Deploy stack (requires .env: AWS_PROFILE, AWS_REGION)
│   ├── prepare_lambda_package.sh # Build Lambda package in Docker (linux/amd64)
│   └── upload_config.sh        # Upload trading_config.json to S3
├── LEARNINGS.md                # This documentation
└── CdpSdkInfo.md               # CDP SDK reference
```

## Configuration System Usage

### Basic Configuration
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

### Execution Commands
```bash
# Validate configuration
python config_validator.py --full-check

# Execute strategy (dry run)
python execute_trading_strategy.py --dry-run --verbose

# Execute strategy (live trading)
python execute_trading_strategy.py

# Single asset trading (replaces legacy direct scripts)
# Simply configure one trading pair and run execute_trading_strategy.py
```

## Core Functionality Implemented
- ✅ **Authentication**: Secure API key handling with ECDSA keys
- ✅ **Account Access**: View account balances and details
- ✅ **Product Discovery**: List available trading pairs
- ✅ **Market Data**: Get current prices for any trading pair
- ✅ **Limit Orders**: Place limit sell orders with proper precision
- ✅ **Post-Only Orders**: Maker-only orders for better fees
- ✅ **Order Management**: Check order status and cancel orders
- ✅ **Price Calculations**: Automatic percentage-based pricing
- ✅ **Configuration System**: JSON-based trading strategy configuration
- ✅ **Multi-Asset Trading**: Support for multiple trading pairs via configuration
- ✅ **Risk Management**: Minimum price enforcement and balance validation
- ✅ **Dry-Run Mode**: Safe testing without actual order placement
- ✅ **Validation Utilities**: Comprehensive configuration and market data validation
- ✅ **Live Trading**: Successfully placed FIL sell order at +0.1% above market
- ✅ **Order URL Logging**: Automatic order URL generation with query parameters for easy tracking
- ✅ **Post-Order Balance Logging**: Real-time balance reporting after order placement
  - Shows remaining asset quantities and percentages
  - Calculates holdings sold vs available for future trades
  - Provides trading capacity guidance

## Current Status (Latest)

### Lambda: Production-Ready
1. **AWS Lambda** – ✅ Working end-to-end
   - **Build**: `prepare_lambda_package.sh` uses Docker (`public.ecr.aws/lambda/python:3.11`) with `--platform linux/amd64` so dependencies (including `cryptography`) are built for Lambda’s environment. Without Docker, Mac-built packages fail on Lambda.
   - **Secrets Manager**: Use `SecretId=` (not `SecretArn=`) in `get_secret_value()` for boto3 compatibility.
   - **Response**: Lambda returns a JSON-serializable summary only; SDK objects (e.g. `CreateOrderResponse`) are stripped via `_serializable_result` and `_run_strategy` so the handler never serializes non-dict types.
   - **Credentials**: Key file can use either `name` or `id` (Lambda/Secrets use `name`); both are supported in root and lambda `coinbase_trader.py`.

2. **Deploy and config**
   - **.env required**: `AWS_PROFILE` and `AWS_REGION` (e.g. `us-west-2`) must be set so deploy, upload, and invoke all target the same region. No hardcoded region in scripts.
   - **Upload config**: `./scripts/upload_config.sh` uploads `trading_config.json` to the stack’s S3 bucket (reads bucket from CloudFormation outputs).
   - **Test Lambda**: Invoke with the same profile and region as deploy; otherwise you may hit a different stack or get “resource not found.”

   - **Lambda handler**: All result data must come from the `summary` dict returned by `_run_strategy` (e.g. `dry_run`, `successful_orders`, `failed_orders`); avoid referencing variables that are not in scope in the handler.

3. **Dry run vs live**
   - **Local**: `execute_trading_strategy.py --dry-run` does not place orders; without `--dry-run` it uses `dry_run` from config.
   - **Lambda**: Uses `dry_run` from the config in S3. If you invoke Lambda for testing, set `dry_run: true` in the S3 config first (or accept that a test invoke can place a real order).

### Architecture
```
├── S3 Bucket: stack-defined (config storage)
├── Secrets Manager: stack-defined secret for Coinbase API credentials
├── Lambda: Python 3.11, ~17MB package (Docker-built deps)
├── SNS: Email notifications
├── EventBridge: Daily 6:15 AM UTC
└── CloudWatch: Logs and error alarms
```

### Lambda Execution Flow (current)
1. ✅ Load env (CONFIG_BUCKET, SECRETS_ARN, NOTIFICATION_TOPIC_ARN)
2. ✅ Get credentials from Secrets Manager (`SecretId=...`)
3. ✅ Get trading config from S3
4. ✅ Initialize CoinbaseTrader (Linux-built cryptography)
5. ✅ Run strategy (_run_strategy), place orders or dry-run per config
6. ✅ Build serializable summary (_serializable_result)
7. ✅ Send SNS email and return JSON response

## Next Steps for Production Deployment

### Immediate Priority (Week 1)

#### 1. **GitHub Repository Setup with CI/CD** - 🎯 HIGH PRIORITY
**Goal**: Automated, reproducible deployments from GitHub

**Setup Steps**:
```bash
# 1. Create GitHub repository
gh repo create coinbase-trading-bot --private

# 2. Push current codebase
git remote add origin https://github.com/username/coinbase-trading-bot.git
git push -u origin main

# 3. Configure GitHub secrets
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY  
# - NOTIFICATION_EMAIL
```

**GitHub Actions Workflow** (`.github/workflows/deploy.yml`):
```yaml
name: Deploy Trading Bot
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - uses: actions/setup-node@v4
      
      # Build Lambda package in Docker (linux/amd64) so cryptography works on Lambda
      - name: Build Lambda package
        run: ./scripts/prepare_lambda_package.sh
          
      # Deploy with CDK
      - name: Deploy infrastructure
        run: |
          npm install -g aws-cdk
          cd cdk && npm install
          cdk deploy --require-approval never
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

**Benefits**:
- ✅ Linux-compatible dependency building
- ✅ Automated deployments on code changes
- ✅ Reproducible builds
- ✅ No local environment dependencies

#### 2. **Docker-Based Local Development** - 🎯 MEDIUM PRIORITY
**Goal**: Reproducible local development and testing

**Docker Setup**:
```dockerfile
# Dockerfile.lambda
FROM public.ecr.aws/lambda/python:3.11

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY coinbase_trader.py lambda_function.py ./

CMD ["lambda_function.lambda_handler"]
```

**Local Development Commands**:
```bash
# Build Lambda-compatible package
docker run --rm -v $(pwd):/app amazonlinux:2 bash -c "
  yum install -y python3 python3-pip && 
  cd /app && 
  pip3 install --target lambda -r requirements.txt
"

# Test Lambda locally
docker run --rm -p 9000:8080 \
  -e AWS_ACCESS_KEY_ID=test \
  -e AWS_SECRET_ACCESS_KEY=test \
  coinbase-trading-bot:latest

# Invoke test
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'
```

**Local Testing Script** (`scripts/test_local.sh`):
```bash
#!/bin/bash
# Build and test Lambda function locally
docker build -f Dockerfile.lambda -t trading-bot-local .
docker run --rm trading-bot-local python -c "
import lambda_function
print('✅ Lambda function imports successfully')
"
```

### Medium-Term Improvements (Month 1)

#### 3. **Production Deployment Pipeline**
- **Environment Management**: Separate dev/staging/prod environments
- **Integration Tests**: Automated testing of full trading workflow
- **Rollback Capability**: Blue/green deployments for zero-downtime updates
- **Monitoring**: Enhanced CloudWatch dashboards and alerts

#### 4. **Enhanced Security & Compliance**
- **Secret Rotation**: Automated Coinbase API key rotation
- **VPC Deployment**: Lambda in private subnets
- **Audit Logging**: CloudTrail integration for compliance
- **Cost Monitoring**: Budget alerts and cost optimization

### Long-Term Scaling (Months 2-3)

#### 5. **Feature Enhancements**
- **Multi-Exchange Support**: Extend beyond Coinbase
- **Advanced Strategies**: DCA, momentum, technical indicators
- **Portfolio Management**: Multi-asset rebalancing
- **Risk Management**: Position sizing, stop-losses, drawdown limits

#### 6. **Operations & Monitoring**
- **Grafana Dashboards**: Real-time trading metrics
- **PagerDuty Integration**: Critical error alerting
- **Performance Analytics**: Trade execution analysis
- **Backtesting Framework**: Strategy validation

## Deployment Architecture Evolution

### Current State
```
Local Mac → Manual CDK Deploy → AWS Lambda (region from .env)
├── Build: Docker (linux/amd64) for Lambda-compatible deps
└── Status: Infrastructure and trading working end-to-end
```

### Target State (Week 1)
```
GitHub → GitHub Actions CI/CD → AWS Lambda
├── Automated: Linux-compatible builds
├── Reproducible: Docker-based development
└── Status: Full production trading capability
```

### Future State (Month 3)
```
GitHub → CI/CD Pipeline → Multi-Environment AWS
├── Dev/Staging/Prod environments
├── Automated testing and deployment
├── Comprehensive monitoring and alerting
└── Status: Enterprise-grade trading platform
```

## Common Troubleshooting

### "Unable to load PEM file" Error
- **Primary Cause**: Using Ed25519 keys instead of ECDSA keys
- **Solution**: Generate new API keys using **ECDSA algorithm** (not Ed25519)
- **Secondary Cause**: Incorrect private key format
- **Solution**: Ensure private key has proper PEM headers/footers

### "AttributeError" on Response Objects
- **Cause**: Treating response objects like dictionaries
- **Solution**: Use object attributes instead of dictionary keys

### "KeyError: 'name'" Error
- **Cause**: Incorrect JSON key file structure
- **Solution**: Ensure JSON has "name" (or "id") and "privateKey" fields in correct format

### Lambda: Secrets Manager / Response Errors
- **Secrets Manager**: Use `SecretId=` (not `SecretArn=`) in boto3 `get_secret_value()`.
- **Lambda response**: Return only JSON-serializable data; convert SDK objects (e.g. `CreateOrderResponse`) via a helper like `_serializable_result` so the handler never serializes non-dict types.

### Authentication Failures
- **Most Common**: Using Ed25519 keys when ECDSA is required
- **Check**: Verify key algorithm when creating API keys on Coinbase Developer Platform

### Claude Code Bash Tool Issues (zsh Session Conflicts)
- **Error**: `zsh:source:1: no such file or directory: /var/folders/.../T/claude-shell-snapshot-xxx`
- **Root Cause**: Claude's bash tool creates custom `TERM_SESSION_ID` that conflicts with Apple Terminal's zsh session management
- **Attempted Fix**: Added `SHELL_SESSIONS_DISABLE=1` check for claude-* session IDs in `.zshrc`
- **Reference**: https://superuser.com/questions/1610587/disable-zsh-session-folder-completely
- **Current Status**: Issue persists, bash tool non-functional
- **Workaround**: Use direct Python execution or manual testing when bash tool fails

## Resources
- [Coinbase Advanced Trading API Docs](https://docs.cdp.coinbase.com/advanced-trade/docs/getting-started)
- [coinbase-advanced-py GitHub](https://github.com/coinbase/coinbase-advanced-py)
- [CDP API Keys Documentation](https://docs.cdp.coinbase.com/get-started/docs/cdp-api-keys/)
- [Post Order API Reference](https://docs.cdp.coinbase.com/coinbase-app/trade/reference/retailbrokerageapi_postorder) - **Key API documentation for order placement**