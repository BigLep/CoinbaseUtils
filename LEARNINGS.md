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

### 8. Development Workflow
1. **Start with Sandbox**: Use sandbox/testnet environment for initial testing
2. **Verify Connection**: Test basic API calls (get accounts, get products) before trading
3. **Small Orders**: Start with minimal order sizes when testing trading functionality (we used 1 FIL)
4. **Price Precision**: Always check product details for correct decimal places before placing orders
5. **Test Market Data**: Verify price feeds work before implementing trading logic
6. **Error Handling**: Implement comprehensive error handling for all API calls
7. **Order Validation**: Test with small amounts first, then scale up

### 9. Production Trading Insights
- **Post-Only Orders**: Always use for better maker fees when possible
- **Price Calculations**: Implement percentage-based pricing for dynamic strategies
- **Market Data**: Use `get_product()` method for current prices (includes price + volume data)
- **Order Types**: GTC (Good Till Cancelled) orders stay active until filled or cancelled
- **Fee Optimization**: Post-only orders typically have lower fees than market orders

## Project Structure
```
CoinbaseUtils/
├── coinbase_trader.py          # Main trading class with post-only orders
├── place_fil_order_direct.py  # Example: FIL sell order script
├── test_fil_data.py           # Testing market data and balances
├── .cdp_api_key.json          # API credentials (not in git)
├── .env.example               # Environment variable template
├── .gitignore                 # Security: excludes credentials
├── requirements.txt           # Python dependencies
├── LEARNINGS.md              # This documentation
└── CdpSdkInfo.md             # CDP SDK reference (for context)
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
- ✅ **Live Trading**: Successfully placed FIL sell order at +0.1% above market

## Next Steps for Scaling
1. **Order Strategy**: Implement different order types (market, stop-loss, etc.)
2. **Portfolio Management**: Track multiple assets and positions
3. **Risk Management**: Implement position sizing and risk controls
4. **Monitoring**: Add logging and alerts for order execution
5. **Automation**: Create scheduled trading strategies
6. **Testing**: Comprehensive unit tests for all trading functions

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

## Resources
- [Coinbase Advanced Trading API Docs](https://docs.cdp.coinbase.com/advanced-trade/docs/getting-started)
- [coinbase-advanced-py GitHub](https://github.com/coinbase/coinbase-advanced-py)
- [CDP API Keys Documentation](https://docs.cdp.coinbase.com/get-started/docs/cdp-api-keys/)
- [Post Order API Reference](https://docs.cdp.coinbase.com/coinbase-app/trade/reference/retailbrokerageapi_postorder) - **Key API documentation for order placement**