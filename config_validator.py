#!/usr/bin/env python3
"""
Configuration validation utility for trading system

This script validates trading configuration files and provides detailed
feedback about any issues found.
"""

import sys
import json
import argparse
from coinbase_trader import CoinbaseTrader

def validate_config_file(config_file: str, verbose: bool = False):
    """Validate a configuration file and return results"""
    
    print(f"🔍 Validating configuration file: {config_file}")
    
    # Check if file exists
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        return {"valid": False, "errors": [f"Configuration file not found: {config_file}"]}
    except json.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON format: {e}"]}
    except Exception as e:
        return {"valid": False, "errors": [f"Error reading file: {e}"]}
    
    # Create trader instance for validation (without loading config)
    try:
        # We'll validate without actually initializing the API client
        trader = CoinbaseTrader.__new__(CoinbaseTrader)
        trader.config = None
        trader.client = None
        
        # Use the validation method
        result = trader.validate_config(config)
        
        if verbose:
            print(f"\n📋 Configuration Structure:")
            print(f"   Default Settings: {config.get('default_settings', {})}")
            print(f"   Number of Trading Pairs: {len(config.get('trading_pairs', []))}")
            
            trading_pairs = config.get('trading_pairs', [])
            for i, pair in enumerate(trading_pairs):
                print(f"\n   Trading Pair {i+1}:")
                print(f"     Symbol: {pair.get('symbol', 'N/A')}")
                print(f"     Enabled: {pair.get('enabled', False)}")
                print(f"     Quantity: {pair.get('quantity', 'N/A')}")
                print(f"     Min Price: ${pair.get('minimum_sell_price', 'N/A')}")
                print(f"     Price Offset: {pair.get('price_offset_percent', 'N/A')}%")
                print(f"     Description: {pair.get('description', 'None')}")
        
        return result
        
    except Exception as e:
        return {"valid": False, "errors": [f"Validation error: {e}"]}

def check_market_data_access(config_file: str):
    """Check if we can access market data for configured trading pairs"""
    
    print(f"\n🌐 Checking market data access...")
    
    try:
        # Initialize trader with API access
        trader = CoinbaseTrader(config_file=config_file)
        
        if not trader.config:
            print("❌ Could not load configuration")
            return False
        
        # Test market data for each trading pair
        trading_pairs = trader.config.get('trading_pairs', [])
        accessible_pairs = 0
        
        for pair in trading_pairs:
            symbol = pair.get('symbol')
            if not symbol:
                continue
                
            try:
                current_price = trader.get_current_price(symbol)
                if current_price:
                    print(f"   ✅ {symbol}: ${current_price:.4f}")
                    accessible_pairs += 1
                else:
                    print(f"   ❌ {symbol}: Could not get price")
            except Exception as e:
                print(f"   ❌ {symbol}: Error - {e}")
        
        print(f"\n📊 Market Data Summary: {accessible_pairs}/{len(trading_pairs)} pairs accessible")
        return accessible_pairs == len(trading_pairs)
        
    except Exception as e:
        print(f"❌ Error accessing market data: {e}")
        return False

def check_account_balances(config_file: str):
    """Check account balances for configured trading pairs"""
    
    print(f"\n💰 Checking account balances...")
    
    try:
        trader = CoinbaseTrader(config_file=config_file)
        
        if not trader.config:
            print("❌ Could not load configuration")
            return False
        
        # Get account information
        accounts = trader.get_accounts()
        if not accounts:
            print("❌ Could not get account information")
            return False
        
        # Create lookup for account balances by currency
        balance_lookup = {}
        for account in accounts.accounts:
            currency = account.currency
            balance = float(account.available_balance.get('value', 0))
            balance_lookup[currency] = balance
        
        # Check balances for each configured trading pair
        trading_pairs = trader.config.get('trading_pairs', [])
        sufficient_balance = True
        
        for pair in trading_pairs:
            if not pair.get('enabled'):
                continue
                
            symbol = pair.get('symbol', '')
            quantity = float(pair.get('quantity', 0))
            
            # Extract base currency from symbol (e.g., FIL from FIL-USD)
            if '-' in symbol:
                base_currency = symbol.split('-')[0]
                available = balance_lookup.get(base_currency, 0)
                
                if available >= quantity:
                    print(f"   ✅ {base_currency}: {available} available (need {quantity})")
                else:
                    print(f"   ❌ {base_currency}: {available} available (need {quantity}) - INSUFFICIENT")
                    sufficient_balance = False
            else:
                print(f"   ⚠️  {symbol}: Invalid symbol format")
                sufficient_balance = False
        
        return sufficient_balance
        
    except Exception as e:
        print(f"❌ Error checking balances: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Validate trading configuration")
    parser.add_argument("config_file", nargs="?", default="trading_config.json", 
                       help="Configuration file to validate")
    parser.add_argument("--verbose", action="store_true", help="Show detailed configuration info")
    parser.add_argument("--check-market-data", action="store_true", 
                       help="Test market data access for configured pairs")
    parser.add_argument("--check-balances", action="store_true", 
                       help="Check account balances for configured pairs")
    parser.add_argument("--full-check", action="store_true", 
                       help="Run all validation checks")
    
    args = parser.parse_args()
    
    print("=== Trading Configuration Validator ===\n")
    
    # Validate configuration structure
    result = validate_config_file(args.config_file, args.verbose)
    
    if result["valid"]:
        print("✅ Configuration file is valid!")
    else:
        print("❌ Configuration validation failed:")
        for error in result["errors"]:
            print(f"   • {error}")
        return 1
    
    # Additional checks if requested
    if args.check_market_data or args.full_check:
        market_data_ok = check_market_data_access(args.config_file)
        if not market_data_ok:
            print("⚠️  Market data access issues detected")
    
    if args.check_balances or args.full_check:
        balances_ok = check_account_balances(args.config_file)
        if not balances_ok:
            print("⚠️  Insufficient balances detected")
    
    if args.full_check:
        print(f"\n{'='*50}")
        print("📋 FULL VALIDATION SUMMARY")
        print(f"{'='*50}")
        print(f"Configuration Structure: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
        
        if 'market_data_ok' in locals():
            print(f"Market Data Access: {'✅ OK' if market_data_ok else '❌ Issues'}")
        
        if 'balances_ok' in locals():
            print(f"Account Balances: {'✅ Sufficient' if balances_ok else '❌ Insufficient'}")
        
        all_good = result["valid"]
        if 'market_data_ok' in locals():
            all_good = all_good and market_data_ok
        if 'balances_ok' in locals():
            all_good = all_good and balances_ok
            
        if all_good:
            print("\n🎉 All checks passed! Configuration is ready for trading.")
        else:
            print("\n⚠️  Some issues detected. Please review before trading.")
            return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)