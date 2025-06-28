#!/usr/bin/env python3
"""
Direct script to place a post-only limit sell order for FIL at 0.1% above current price
"""

from coinbase_trader import CoinbaseTrader

def main():
    # Initialize trader
    trader = CoinbaseTrader()
    
    print("=== FIL Post-Only Limit Sell Order ===\n")
    
    # Place the order directly with a small test amount first
    print("Placing post-only limit sell order for FIL...")
    
    # Use a small test amount (1 FIL) for safety
    test_amount = "1.0"  # 1 FIL for testing
    
    result = trader.create_fil_sell_order(size=test_amount, price_offset_percent=0.1)
    
    if result.get("success"):
        order = result["order"]
        details = result["details"]
        
        print("✅ Order placed successfully!")
        print(f"Product: {details['product_id']}")
        print(f"Size: {details['quantity']} FIL")
        print(f"Limit Price: ${details['limit_price']:.3f}")
        print(f"Current Price: ${details['current_price']:.3f}")
        print(f"Price Offset: +{details['offset_percent']}%")
        
        # The order was successful, so it should be in your pending orders
        print(f"\n📋 Order Status:")
        print(f"✅ Post-only limit sell order placed successfully")
        print(f"💰 You'll receive ${float(details['limit_price']) * float(details['quantity']):.2f} when filled")
        
    else:
        error = result.get("error", "Unknown error")
        print(f"❌ Order failed: {error}")

if __name__ == "__main__":
    main()