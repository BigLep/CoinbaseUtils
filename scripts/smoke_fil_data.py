#!/usr/bin/env python3
"""
Smoke test: FIL market data and balance.
Run from repo root with .cdp_api_key.json or COINBASE_* env set.
"""

from coinbase_trader import CoinbaseTrader

def main():
    trader = CoinbaseTrader()

    print("=== FIL market data ===\n")

    print("1. FIL price...")
    current_price = trader.get_current_price("FIL-USD")
    if current_price:
        print(f"   Current FIL: ${current_price:.4f}")
        print(f"   +0.1%:      ${current_price * 1.001:.4f}")
    else:
        print("   Could not get FIL price")
        return

    print("\n2. FIL balance...")
    accounts = trader.get_accounts()
    if accounts:
        for account in accounts.accounts:
            if account.currency == "FIL":
                balance = account.available_balance.get("value", "0")
                print(f"   Available FIL: {balance}")
                break
        else:
            print("   No FIL account (normal if you don't hold FIL)")

    print("\n3. FIL products...")
    products = trader.get_products()
    if products:
        fil = [p for p in products.products if "FIL" in p.product_id]
        for p in fil:
            print(f"   - {p.product_id}")

if __name__ == "__main__":
    main()
