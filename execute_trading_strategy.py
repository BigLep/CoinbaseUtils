#!/usr/bin/env python3
"""
Execute trading strategy based on configuration file

This script will:
1. Load trading configuration from JSON file
2. Check market conditions for each enabled trading pair
3. Place orders based on configuration parameters
4. Provide detailed execution reports
"""

import sys
import argparse
from coinbase_trader import CoinbaseTrader

def main():
    parser = argparse.ArgumentParser(description="Execute configured trading strategy")
    parser.add_argument("--config", default="trading_config.json", help="Configuration file path")
    parser.add_argument("--dry-run", action="store_true", help="Simulate orders without actually placing them")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    print("=== Coinbase Trading Strategy Execution ===\n")
    
    # Initialize trader
    try:
        trader = CoinbaseTrader(config_file=args.config)
    except Exception as e:
        print(f"❌ Failed to initialize trader: {e}")
        return 1
    
    if not trader.config:
        print(f"❌ No configuration loaded from {args.config}")
        return 1
    
    # Check if dry run mode is enabled in config or command line
    dry_run = args.dry_run or trader.config.get("default_settings", {}).get("dry_run", False)
    if dry_run:
        print("🔍 Running in DRY RUN mode - no actual orders will be placed\n")
    
    # Get enabled trading pairs
    enabled_pairs = [pair for pair in trader.config["trading_pairs"] if pair.get("enabled", False)]
    
    if not enabled_pairs:
        print("ℹ️  No enabled trading pairs found in configuration")
        return 0
    
    print(f"📋 Found {len(enabled_pairs)} enabled trading pairs:")
    for pair in enabled_pairs:
        print(f"   • {pair['symbol']} - {pair.get('description', 'No description')}")
    
    print(f"\n{'='*50}")
    
    # Execute trading strategy for each enabled pair
    results = []
    successful_orders = 0
    failed_orders = 0
    
    for pair in enabled_pairs:
        try:
            result = trader.place_configured_order(pair, dry_run=dry_run)
            results.append(result)
            
            if result.get("success"):
                successful_orders += 1
                if not dry_run and 'order_id' in result:
                    order_id = result['order_id']
                    print(f"💰 Expected revenue: ${result['details']['expected_revenue']:.2f}")
                    print(f"📋 Order ID: {order_id}")
            else:
                failed_orders += 1
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception processing {pair['symbol']}: {e}")
            failed_orders += 1
            results.append({
                "success": False,
                "error": str(e),
                "symbol": pair['symbol']
            })
    
    # Summary report
    print(f"\n{'='*50}")
    print("📊 EXECUTION SUMMARY")
    print(f"{'='*50}")
    print(f"Total trading pairs processed: {len(enabled_pairs)}")
    print(f"Successful orders: {successful_orders}")
    print(f"Failed orders: {failed_orders}")
    
    if dry_run:
        print(f"Mode: DRY RUN (no actual orders placed)")
    else:
        print(f"Mode: LIVE TRADING")
        
        # Calculate total expected revenue for successful orders
        total_revenue = sum(
            result['details']['expected_revenue'] 
            for result in results 
            if result.get('success') and 'details' in result
        )
        
        if total_revenue > 0:
            print(f"Total expected revenue: ${total_revenue:.2f}")
    
    # Detailed results if verbose
    if args.verbose:
        print(f"\n📋 DETAILED RESULTS:")
        for i, result in enumerate(results):
            pair = enabled_pairs[i]
            print(f"\n{i+1}. {pair['symbol']}:")
            if result.get('success'):
                if result.get('dry_run'):
                    print("   Status: ✅ DRY RUN SUCCESS")
                else:
                    print("   Status: ✅ ORDER PLACED")
                    
                details = result.get('details', {})
                print(f"   Current Price: ${details.get('current_price', 0):.4f}")
                print(f"   Limit Price: ${details.get('limit_price', 0):.4f}")
                print(f"   Quantity: {details.get('quantity', 0)}")
                print(f"   Price Offset: +{details.get('offset_percent', 0)}%")
            else:
                print(f"   Status: ❌ FAILED")
                print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Exit with appropriate code
    return 0 if failed_orders == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)