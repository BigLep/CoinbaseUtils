#!/usr/bin/env python3
"""
Smoke test: post-order balance logging.
Run from repo root with .cdp_api_key.json or COINBASE_* env set.
"""

from coinbase_trader import CoinbaseTrader

def main():
    trader = CoinbaseTrader()

    print("=== Balance logging ===\n")

    print("1. FIL balance:")
    info = trader.get_asset_balance("FIL")
    if "error" in info:
        print(f"   Error: {info['error']}")
    else:
        print(f"   {info['formatted']}")
        if "note" in info:
            print(f"   {info['note']}")

    print("\n2. Post-order balance (simulated sizes):")
    for size in (0.1, 1.0, 10.0):
        trader.log_post_order_balance("FIL-USD", size)

if __name__ == "__main__":
    main()
