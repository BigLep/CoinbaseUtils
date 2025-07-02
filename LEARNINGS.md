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
  - `.env` files
  - `.cdp_api_key.json`
  - `*.json` (catches any other credential files)
- **Key File Approach**: Using JSON key files is more secure than environment variables for production

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
├── coinbase_trader.py          # Main trading class with configuration support
├── execute_trading_strategy.py # Configuration-driven order execution
├── config_validator.py        # Configuration validation utilities
├── trading_config.json        # Active trading configuration (not in git)
├── trading_config.example.json # Configuration template
├── test_fil_data.py           # Testing market data and balances
├── debug_order_response.py    # Order response structure analysis
├── .cdp_api_key.json          # API credentials (not in git)
├── .env.example               # Environment variable template
├── .gitignore                 # Security: excludes credentials
├── requirements.txt           # Python dependencies
├── LEARNINGS.md              # This documentation
├── agents.md                  # AI agent development guidelines
└── CdpSdkInfo.md             # CDP SDK reference (for context)
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

## Current Status (Latest Session - July 2025)

### Recently Completed Features
1. **AWS Lambda Infrastructure Deployment** - ✅ COMPLETED (July 2025)
   - Complete Infrastructure as Code using AWS CDK
   - Lambda function with bundled dependencies (simplified approach)
   - S3 bucket for trading configuration storage
   - Secrets Manager for secure API credential storage
   - SNS notifications for execution reports
   - EventBridge scheduling for daily execution (6:15 AM UTC)
   - CloudWatch monitoring and error alarms
   - **Status**: Infrastructure fully deployed to us-west-2

2. **Trading Bot Configuration Management** - ✅ COMPLETED
   - JSON-based configuration system with S3 storage
   - Secrets management with proper field mapping (`name`/`privateKey`)
   - Trading config successfully uploaded and accessible
   - Email notification system functional

3. **Core Lambda Functionality** - ✅ WORKING (with limitations)
   - Lambda function executes successfully (StatusCode: 200)
   - Credentials retrieval from Secrets Manager working
   - Configuration download from S3 working
   - Email notifications working
   - Mock trader implementation as fallback

### Current Challenges

#### 1. **Cross-Platform Dependency Build Issues** - ⚠️ BLOCKING PRODUCTION
**Problem**: The `cryptography` library contains architecture-specific compiled binaries
- **Root Cause**: Building dependencies on macOS ARM64 creates binaries incompatible with AWS Lambda runtime
- **Error**: `invalid ELF header` when Lambda tries to import `cryptography` module
- **Impact**: CoinbaseTrader cannot initialize, falling back to mock implementation
- **Attempted Solutions**:
  - Tried ARM64 Lambda architecture (still incompatible)
  - Tried x86_64 Lambda architecture (still incompatible)
  - Dependencies built locally on Mac don't work in Lambda Linux environment

#### 2. **Mac Development Environment Challenges**
- **Package Building**: `pip install --target` on Mac creates Mac-specific binaries
- **Architecture Mismatch**: Mac ARM64 → AWS Lambda x86_64/ARM64 compatibility issues
- **Development Workflow**: No local testing of actual Lambda environment

### Architecture and Infrastructure Details

#### AWS Resources Created
```
├── S3 Bucket: coinbase-trading-config-290135766346-us-west-2
├── Secrets Manager: arn:aws:secretsmanager:us-west-2:290135766346:secret:CoinbaseApiCredentialsFAECE-*
├── Lambda Function: CoinbaseTradingBotStack-TradingBotFunctionA03094A0-jOwZZd14P29v
│   ├── Runtime: Python 3.11
│   ├── Memory: 512MB
│   ├── Timeout: 5 minutes
│   └── Package Size: ~26MB (with bundled dependencies)
├── SNS Topic: Email notifications
├── EventBridge Rule: Daily execution at 6:15 AM UTC
└── CloudWatch: Logs and error monitoring
```

#### Current Lambda Execution Flow
1. ✅ Retrieve API credentials from Secrets Manager
2. ✅ Download trading configuration from S3
3. ❌ Import coinbase_trader (fails due to cryptography library)
4. ✅ Fallback to mock trader implementation
5. ✅ Process trading pairs (currently 1 enabled: FIL-USD)
6. ❌ Place actual orders (mock trader returns failure)
7. ✅ Send email notification with execution report

### Outstanding Issues
1. **Cross-Platform Build Environment** - 🚨 CRITICAL
   - Need Linux-compatible dependency building
   - Current mock trader prevents actual trading
   - **Next Action**: Implement Docker-based build process or GitHub Actions CI/CD

2. **Local Development Reproducibility** - ⚠️ IMPORTANT
   - Cannot reliably test Lambda packages locally
   - No local Lambda environment simulation
   - **Next Action**: Docker-based local development environment

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
      
      # Build dependencies in Linux environment
      - name: Build Lambda package
        run: |
          pip install --target lambda -r requirements.txt
          cp coinbase_trader.py lambda/
          cp lambda/lambda_function.py lambda/
          
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

### Current State (July 2025)
```
Local Mac → Manual CDK Deploy → AWS Lambda (us-west-2)
├── Issues: Architecture compatibility, manual process
└── Status: Infrastructure working, trading disabled
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
- **Solution**: Ensure JSON has "name" and "privateKey" fields in correct format

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