import os
import json
from decimal import Decimal
from dotenv import load_dotenv
from coinbase.rest import RESTClient

load_dotenv()

class CoinbaseTrader:
    def __init__(self, key_file=".cdp_api_key.json", config_file="trading_config.json"):
        self.key_file = key_file
        self.config_file = config_file
        self.config = None
        
        # Check if key file exists
        if not os.path.exists(self.key_file):
            raise ValueError(f"API key file not found: {self.key_file}")
        
        # Load and parse the key file
        with open(self.key_file, 'r') as f:
            key_data = json.load(f)
        
        # Extract credentials from the JSON structure
        if 'id' in key_data and 'privateKey' in key_data:
            # This is the format you have - convert to what SDK expects
            api_key = key_data['id']
            api_secret = f"-----BEGIN EC PRIVATE KEY-----\n{key_data['privateKey']}\n-----END EC PRIVATE KEY-----"
            
            # Initialize REST client with credentials
            self.client = RESTClient(
                api_key=api_key,
                api_secret=api_secret
            )
        else:
            # Try to use the file directly (standard CDP format)
            self.client = RESTClient(key_file=self.key_file)
        
        # Load trading configuration if file exists
        if os.path.exists(self.config_file):
            self.load_trading_config(self.config_file)
    
    def get_accounts(self):
        """Get account information"""
        try:
            return self.client.get_accounts()
        except Exception as e:
            print(f"Error getting accounts: {e}")
            return None
    
    def get_products(self):
        """Get available trading products"""
        try:
            return self.client.get_products()
        except Exception as e:
            print(f"Error getting products: {e}")
            return None
    
    def get_current_price(self, product_id: str):
        """Get current market price for a product"""
        try:
            product = self.client.get_product(product_id)
            if product and hasattr(product, 'price'):
                return float(product.price)
            return None
        except Exception as e:
            print(f"Error getting price for {product_id}: {e}")
            return None
    
    def place_limit_sell_order(self, product_id: str, size: str, price: str):
        """
        Place a limit sell order
        
        Args:
            product_id (str): The trading pair (e.g., 'BTC-USD')
            size (str): Amount to sell
            price (str): Limit price
        
        Returns:
            dict: Order response
        """
        try:
            order = self.client.limit_order_gtc(
                client_order_id="",
                product_id=product_id,
                side="SELL",
                base_size=size,
                limit_price=price
            )
            return order
        except Exception as e:
            print(f"Error placing sell order: {e}")
            return None
    
    def place_post_only_limit_sell(self, product_id: str, size: str, price: str):
        """
        Place a post-only limit sell order (maker only)
        
        Args:
            product_id (str): The trading pair (e.g., 'FIL-USD')
            size (str): Amount to sell
            price (str): Limit price
        
        Returns:
            dict: Order response
        """
        try:
            order = self.client.limit_order_gtc(
                client_order_id="",
                product_id=product_id,
                side="SELL",
                base_size=size,
                limit_price=price,
                post_only=True  # This makes it post-only (maker only)
            )
            return order
        except Exception as e:
            print(f"Error placing post-only sell order: {e}")
            return None
    
    def create_fil_sell_order(self, size: str = None, price_offset_percent: float = 0.1):
        """
        Create a post-only limit sell order for FIL at current price + offset
        
        Args:
            size (str): Amount of FIL to sell (if None, will check balance)
            price_offset_percent (float): Percentage above current price (default 0.1%)
        
        Returns:
            dict: Order response with details
        """
        product_id = "FIL-USD"
        
        # Get current price
        current_price = self.get_current_price(product_id)
        if not current_price:
            return {"error": f"Could not get current price for {product_id}"}
        
        # Get product details for proper price precision
        product = self.client.get_product(product_id)
        price_increment = float(product.price_increment)
        
        # Calculate limit price (current price + offset)
        target_price = current_price * (1 + price_offset_percent / 100)
        
        # Round to price increment
        limit_price = round(target_price / price_increment) * price_increment
        limit_price_str = f"{limit_price:.3f}"  # FIL-USD uses 3 decimal places
        
        # If no size specified, check balance
        if not size:
            accounts = self.get_accounts()
            if accounts:
                for account in accounts.accounts:
                    if account.currency == "FIL":
                        available = float(account.available_balance.get('value', 0))
                        if available > 0:
                            size = str(available)
                            break
                else:
                    return {"error": "No FIL balance found"}
            else:
                return {"error": "Could not get account information"}
        
        print(f"Creating post-only limit sell order:")
        print(f"  Product: {product_id}")
        print(f"  Current Price: ${current_price:.4f}")
        print(f"  Limit Price: ${limit_price:.4f} (+{price_offset_percent}%)")
        print(f"  Size: {size} FIL")
        
        # Place the post-only order
        order = self.place_post_only_limit_sell(product_id, size, limit_price_str)
        
        if order and order.success:
            # Create details for logging
            order_details = {
                "product_id": product_id,
                "current_price": current_price,
                "limit_price": limit_price,
                "quantity": size,
                "offset_percent": price_offset_percent
            }
            
            # Log order placement with URL
            order_id = self.log_order_placement(order, product_id, order_details)
            
            return {
                "success": True,
                "order": order,
                "order_id": order_id,
                "details": order_details
            }
        elif order and order.error_response:
            return {"error": f"Order failed: {order.error_response.get('error', 'Unknown error')} - {order.error_response.get('message', '')}"}
        else:
            return {"error": "Failed to place order"}
    
    def load_trading_config(self, config_file: str):
        """Load trading configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            
            # Validate the configuration
            validation_result = self.validate_config(self.config)
            if not validation_result["valid"]:
                raise ValueError(f"Invalid configuration: {validation_result['errors']}")
            
            print(f"✅ Loaded configuration with {len(self.config['trading_pairs'])} trading pairs")
            return True
            
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            self.config = None
            return False
    
    def validate_config(self, config: dict):
        """Validate trading configuration structure and values"""
        errors = []
        
        # Check required top-level keys
        required_keys = ["default_settings", "trading_pairs"]
        for key in required_keys:
            if key not in config:
                errors.append(f"Missing required key: {key}")
        
        if errors:
            return {"valid": False, "errors": errors}
        
        # Validate default settings
        default_settings = config.get("default_settings", {})
        valid_order_types = ["post_only_limit", "limit", "market"]
        if default_settings.get("order_type") not in valid_order_types:
            errors.append(f"Invalid order_type. Must be one of: {valid_order_types}")
        
        # Validate trading pairs
        trading_pairs = config.get("trading_pairs", [])
        if not isinstance(trading_pairs, list):
            errors.append("trading_pairs must be a list")
        
        for i, pair in enumerate(trading_pairs):
            pair_errors = self._validate_trading_pair(pair, i)
            errors.extend(pair_errors)
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def _validate_trading_pair(self, pair: dict, index: int):
        """Validate individual trading pair configuration"""
        errors = []
        pair_prefix = f"trading_pairs[{index}]"
        
        # Required fields
        required_fields = ["symbol", "enabled", "quantity", "minimum_sell_price", "price_offset_percent"]
        for field in required_fields:
            if field not in pair:
                errors.append(f"{pair_prefix}.{field} is required")
        
        # Validate symbol format (should be like BTC-USD)
        symbol = pair.get("symbol", "")
        if symbol and "-" not in symbol:
            errors.append(f"{pair_prefix}.symbol should be in format 'BASE-QUOTE' (e.g., BTC-USD)")
        
        # Validate numeric fields
        try:
            quantity = float(pair.get("quantity", 0))
            if quantity <= 0:
                errors.append(f"{pair_prefix}.quantity must be greater than 0")
        except (ValueError, TypeError):
            errors.append(f"{pair_prefix}.quantity must be a valid number")
        
        try:
            min_price = float(pair.get("minimum_sell_price", 0))
            if min_price <= 0:
                errors.append(f"{pair_prefix}.minimum_sell_price must be greater than 0")
        except (ValueError, TypeError):
            errors.append(f"{pair_prefix}.minimum_sell_price must be a valid number")
        
        try:
            offset = float(pair.get("price_offset_percent", 0))
            if offset < 0 or offset > 100:
                errors.append(f"{pair_prefix}.price_offset_percent must be between 0 and 100")
        except (ValueError, TypeError):
            errors.append(f"{pair_prefix}.price_offset_percent must be a valid number")
        
        return errors
    
    def get_order_url(self, order_id: str):
        """
        Construct Coinbase orders URL with order ID query parameter
        
        Args:
            order_id (str): The order ID returned from successful order placement
        
        Returns:
            str: URL to Coinbase orders page with orderId query parameter for easy identification
        """
        # Use the correct Coinbase orders endpoint with order ID as query parameter
        # This makes it easy to search for the specific order
        base_url = "https://www.coinbase.com/orders"
        return f"{base_url}?orderId={order_id}"
    
    def log_order_placement(self, order_response, symbol: str, details: dict):
        """
        Log order placement details including order URL
        
        Args:
            order_response: The order response object from API
            symbol (str): Trading pair symbol
            details (dict): Order details dictionary
        """
        if order_response and order_response.success and hasattr(order_response, 'success_response'):
            success_resp = order_response.success_response
            order_id = success_resp.get('order_id')
            client_order_id = success_resp.get('client_order_id')
            
            print(f"✅ Order placed successfully!")
            print(f"   Order ID: {order_id}")
            print(f"   Client Order ID: {client_order_id}")
            print(f"   Product: {symbol}")
            print(f"   Size: {details.get('quantity')} {symbol.split('-')[0]}")
            print(f"   Limit Price: ${details.get('limit_price'):.4f}")
            print(f"   Expected Revenue: ${details.get('expected_revenue', 0):.2f}")
            
            # Log the order URL
            order_url = self.get_order_url(order_id)
            print(f"   📋 View Order: {order_url}")
            print(f"   🔍 Search for Order ID: {order_id}")
            
            return order_id
        
        return None
    
    def check_minimum_price_conditions(self, symbol: str, min_price: float):
        """Check if current market price meets minimum sell price condition"""
        current_price = self.get_current_price(symbol)
        if not current_price:
            return {"meets_condition": False, "error": f"Could not get current price for {symbol}"}
        
        meets_condition = current_price >= min_price
        return {
            "meets_condition": meets_condition,
            "current_price": current_price,
            "minimum_price": min_price,
            "difference": current_price - min_price,
            "percentage_above_min": ((current_price - min_price) / min_price * 100) if min_price > 0 else 0
        }
    
    def place_configured_order(self, pair_config: dict, dry_run: bool = False):
        """Place order based on trading pair configuration"""
        symbol = pair_config["symbol"]
        quantity = pair_config["quantity"]
        min_price = float(pair_config["minimum_sell_price"])
        offset_percent = pair_config["price_offset_percent"]
        
        print(f"\n=== Processing {symbol} ===")
        
        # Check minimum price condition
        price_check = self.check_minimum_price_conditions(symbol, min_price)
        if not price_check["meets_condition"]:
            return {
                "success": False,
                "error": f"Current price ${price_check.get('current_price', 'N/A'):.4f} is below minimum ${min_price:.4f}",
                "symbol": symbol
            }
        
        print(f"✅ Price check passed: ${price_check['current_price']:.4f} >= ${min_price:.4f}")
        
        # Get current price and calculate limit price
        current_price = price_check["current_price"]
        
        # Get product details for proper price precision
        try:
            product = self.client.get_product(symbol)
            price_increment = float(product.price_increment)
        except Exception as e:
            return {"success": False, "error": f"Could not get product details for {symbol}: {e}", "symbol": symbol}
        
        # Calculate limit price with proper precision
        target_price = current_price * (1 + offset_percent / 100)
        limit_price = round(target_price / price_increment) * price_increment
        limit_price_str = f"{limit_price:.{len(str(price_increment).split('.')[-1])}f}"
        
        print(f"📊 Order Details:")
        print(f"   Current Price: ${current_price:.4f}")
        print(f"   Target Price (+{offset_percent}%): ${target_price:.6f}")
        print(f"   Limit Price (rounded): ${limit_price_str}")
        print(f"   Quantity: {quantity}")
        
        if dry_run:
            print("🔍 DRY RUN - Order would be placed but not actually executed")
            return {
                "success": True,
                "dry_run": True,
                "symbol": symbol,
                "details": {
                    "current_price": current_price,
                    "limit_price": limit_price,
                    "quantity": quantity,
                    "offset_percent": offset_percent
                }
            }
        
        # Place the actual order
        try:
            order = self.place_post_only_limit_sell(symbol, quantity, limit_price_str)
            
            if order and order.success:
                # Create details for logging
                order_details = {
                    "current_price": current_price,
                    "limit_price": limit_price,
                    "quantity": quantity,
                    "offset_percent": offset_percent,
                    "expected_revenue": float(limit_price_str) * float(quantity)
                }
                
                # Log order placement with URL
                order_id = self.log_order_placement(order, symbol, order_details)
                
                return {
                    "success": True,
                    "order": order,
                    "order_id": order_id,
                    "symbol": symbol,
                    "details": order_details
                }
            elif order and order.error_response:
                error_msg = f"{order.error_response.get('error', 'Unknown error')} - {order.error_response.get('message', '')}"
                print(f"❌ Order failed: {error_msg}")
                return {"success": False, "error": error_msg, "symbol": symbol}
            else:
                print("❌ Order failed: Unknown error")
                return {"success": False, "error": "Unknown error", "symbol": symbol}
                
        except Exception as e:
            error_msg = f"Exception placing order: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg, "symbol": symbol}
    
    def get_order(self, order_id: str):
        """Get order details"""
        try:
            return self.client.get_order(order_id)
        except Exception as e:
            print(f"Error getting order: {e}")
            return None
    
    def cancel_order(self, order_id: str):
        """Cancel an order"""
        try:
            return self.client.cancel_orders([order_id])
        except Exception as e:
            print(f"Error canceling order: {e}")
            return None

if __name__ == "__main__":
    trader = CoinbaseTrader()
    
    # Test connection
    print("Testing Coinbase Advanced Trading API connection...")
    accounts = trader.get_accounts()
    
    if accounts:
        print("\n=== Connected Successfully! ===")
        print(f"Number of accounts: {len(accounts.accounts)}")
        
        # Show first few accounts
        print("\nYour accounts:")
        for account in accounts.accounts[:3]:
            balance = account.available_balance
            if isinstance(balance, dict):
                print(f"  {account.currency}: {balance.get('value', '0')} {balance.get('currency', account.currency)}")
            else:
                print(f"  {account.currency}: {balance}")
        
        # Show available products
        print("\nGetting available products...")
        products = trader.get_products()
        if products and hasattr(products, 'products'):
            print(f"Available products: {len(products.products)}")
            # Show first few products
            for product in products.products[:5]:
                print(f"  {product.product_id}")
        
        print("\nReady to trade! Example usage:")
        print("trader.place_limit_sell_order('BTC-USD', '0.001', '50000')")
    else:
        print("Failed to connect to Coinbase Advanced Trading API")
        print("Check your API credentials format - they should be in PEM format")