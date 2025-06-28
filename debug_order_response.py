#!/usr/bin/env python3
"""
Debug script to examine order response structure
"""

from coinbase_trader import CoinbaseTrader
import json

def main():
    trader = CoinbaseTrader()
    
    print("=== Order Response Structure Analysis ===\n")
    
    # Create a very small test order to see the response structure
    print("Creating minimal test order to examine response...")
    
    result = trader.create_fil_sell_order(size="0.001", price_offset_percent=0.1)
    
    if result.get("success"):
        order = result["order"]
        print(f"Order object type: {type(order)}")
        print(f"Order success: {order.success}")
        
        if hasattr(order, '__dict__'):
            print(f"\nOrder attributes:")
            for key, value in order.__dict__.items():
                print(f"  {key}: {value}")
        
        # Check for order configuration details
        if hasattr(order, 'order_configuration'):
            print(f"\nOrder configuration:")
            print(f"  {order.order_configuration}")
            
        # Try to find any ID-like fields
        print(f"\nLooking for ID fields...")
        for attr in dir(order):
            if 'id' in attr.lower() and not attr.startswith('_'):
                try:
                    value = getattr(order, attr)
                    print(f"  {attr}: {value}")
                except:
                    print(f"  {attr}: <could not access>")
    
    else:
        print(f"Failed to create test order: {result.get('error', 'Unknown error')}")
        
        # Let's also check what a failed order response looks like
        order = result.get("order")
        if order:
            print(f"\nFailed order object type: {type(order)}")
            if hasattr(order, '__dict__'):
                print(f"Failed order attributes:")
                for key, value in order.__dict__.items():
                    print(f"  {key}: {value}")

if __name__ == "__main__":
    main()