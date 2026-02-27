import json
import boto3
import os
import logging
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _serializable_result(result):
    """Return a copy of result with only JSON-serializable values (no SDK objects)."""
    out = {}
    for key in ("success", "symbol", "error", "order_id", "dry_run", "mock", "details"):
        if key in result:
            val = result[key]
            if hasattr(val, "__dict__") and not isinstance(
                val, (dict, list, str, int, float, bool, type(None))
            ):
                continue
            out[key] = val
    if "pair_config" in result and isinstance(result["pair_config"], dict):
        out["pair_config"] = result["pair_config"]
    return out


def _run_strategy(config_data, trader, request_id="local"):
    """Run trading loop and return JSON-serializable summary."""
    results = []
    trading_pairs = config_data.get("trading_pairs", [])
    default_settings = config_data.get("default_settings", {})
    dry_run = default_settings.get("dry_run", False)
    for pair_config in trading_pairs:
        if not pair_config.get("enabled", False):
            continue
        try:
            result = trader.place_configured_order(pair_config, dry_run=dry_run)
            results.append(_serializable_result(result))
        except Exception as e:
            results.append({
                "success": False,
                "symbol": pair_config.get("symbol", "Unknown"),
                "error": str(e),
            })
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    return {
        "timestamp": request_id,
        "total_pairs": len(trading_pairs),
        "processed_pairs": len(results),
        "successful_orders": len(successful),
        "failed_orders": len(failed),
        "dry_run": dry_run,
        "results": results,
    }


def lambda_handler(event, context):
    """
    AWS Lambda handler for Coinbase trading bot
    """
    
    try:
        logger.info("Starting Coinbase trading bot execution")
        
        # Get environment variables
        config_bucket = os.environ.get('CONFIG_BUCKET')
        secrets_arn = os.environ.get('SECRETS_ARN')
        notification_topic_arn = os.environ.get('NOTIFICATION_TOPIC_ARN')
        
        if not all([config_bucket, secrets_arn, notification_topic_arn]):
            raise ValueError("Missing required environment variables")
        
        # Initialize AWS clients
        s3_client = boto3.client('s3')
        secrets_client = boto3.client('secretsmanager')
        sns_client = boto3.client('sns')
        
        # Retrieve API credentials from Secrets Manager
        logger.info("Retrieving API credentials from Secrets Manager")
        try:
            secret_response = secrets_client.get_secret_value(SecretId=secrets_arn)
            credentials = json.loads(secret_response['SecretString'])
            
            # Extract credentials (using correct field names from Secrets Manager)
            api_key = credentials.get('name')  # This maps to the 'name' field
            private_key = credentials.get('privateKey')  # This maps to the 'privateKey' field
            
            if not api_key or not private_key:
                raise ValueError("Missing API credentials in secrets")
                
        except Exception as e:
            error_msg = f"Failed to retrieve credentials: {str(e)}"
            logger.error(error_msg)
            send_notification(sns_client, notification_topic_arn, "Trading Bot Error", error_msg)
            return create_response(500, error_msg)
        
        # Download trading configuration from S3
        logger.info("Downloading trading configuration from S3")
        try:
            config_response = s3_client.get_object(
                Bucket=config_bucket,
                Key='trading_config.json'
            )
            config_data = json.loads(config_response['Body'].read())
            
        except Exception as e:
            error_msg = f"Failed to download trading config: {str(e)}"
            logger.error(error_msg)
            send_notification(sns_client, notification_topic_arn, "Trading Bot Error", error_msg)
            return create_response(500, error_msg)
        
        # Try to import and initialize the trader
        try:
            from coinbase_trader import CoinbaseTrader
            
            # Create temporary credentials file for the trader
            temp_creds = {
                "name": api_key,
                "privateKey": private_key
            }
            
            # Write temporary credentials file
            temp_creds_path = "/tmp/.cdp_api_key.json"
            with open(temp_creds_path, 'w') as f:
                json.dump(temp_creds, f)
            
            # Initialize trader
            trader = CoinbaseTrader(key_file=temp_creds_path)
            trader.config = config_data
            
            logger.info("CoinbaseTrader initialized successfully")
            
        except Exception as e:
            # Fallback to mock trader if import fails (e.g., cryptography built for wrong OS on Lambda)
            logger.warning(f"Failed to initialize CoinbaseTrader: {str(e)}", exc_info=True)
            logger.info("Using mock trader - no real orders will be placed")
            trader = MockTrader(init_error=str(e))
            trader.config = config_data
            # Notify that real trading is disabled so you can fix the deployment
            send_notification(
                sns_client, notification_topic_arn,
                "Trading Bot: Real trader failed - running in mock mode",
                f"CoinbaseTrader failed to initialize. No real orders were placed.\n\n"
                f"Error: {str(e)}\n\n"
                f"Common cause: Lambda package was built on Mac (cryptography incompatible with Linux).\n"
                f"Fix: Run ./scripts/prepare_lambda_package.sh (with Docker installed) then redeploy."
            )
        
        # Execute trading strategy (same logic as execute_trading_strategy.py locally)
        summary = _run_strategy(config_data, trader, request_id=context.aws_request_id)
        logger.info(f"Processing {summary['processed_pairs']} pairs (dry_run: {summary['dry_run']})")
        logger.info(f"Execution completed: {summary['successful_orders']} successful, {summary['failed_orders']} failed")

        # Gather balance and runout for each enabled pair (real trader only)
        balance_info = []
        if hasattr(trader, "get_asset_balance"):
            for pair_config in config_data.get("trading_pairs", []):
                if not pair_config.get("enabled", False):
                    continue
                symbol = pair_config.get("symbol", "")
                if "-" not in symbol:
                    continue
                base_asset = symbol.split("-")[0]
                qty_per_run = _safe_float(pair_config.get("quantity"), 0) or 0
                try:
                    bal = trader.get_asset_balance(base_asset)
                except Exception as e:
                    logger.warning(f"Balance check failed for {base_asset}: {e}")
                    bal = {"error": str(e)}
                available = None if "error" in bal else _safe_float(bal.get("available"))
                days_remaining = None
                if available is not None and qty_per_run > 0:
                    days_remaining = available / qty_per_run
                balance_info.append({
                    "symbol": symbol,
                    "currency": base_asset,
                    "available": available,
                    "quantity_per_run": qty_per_run,
                    "days_remaining": days_remaining,
                })
        summary["balance_info"] = balance_info

        # Send notification email
        notification_subject = f"Trading Bot Execution {'(DRY RUN)' if summary['dry_run'] else ''}"
        notification_message = format_execution_report(summary)
        
        send_notification(sns_client, notification_topic_arn, notification_subject, notification_message)
        
        logger.info(f"Execution completed: {summary['successful_orders']} successful, {summary['failed_orders']} failed")
        
        return create_response(200, summary)
        
    except Exception as e:
        error_msg = f"Unexpected error in lambda handler: {str(e)}"
        logger.error(error_msg)
        
        # Try to send error notification
        try:
            if 'sns_client' in locals() and 'notification_topic_arn' in locals():
                send_notification(sns_client, notification_topic_arn, "Trading Bot Critical Error", error_msg)
        except:
            logger.error("Failed to send error notification")
        
        return create_response(500, error_msg)


class MockTrader:
    """Mock trader for testing when actual trader cannot be initialized"""
    
    def __init__(self, init_error=None):
        self.config = None
        self.init_error = init_error or "cryptography/library not available in Lambda environment"
    
    def place_configured_order(self, pair_config, dry_run=False):
        """Mock order placement that always returns failure"""
        symbol = pair_config.get('symbol', 'Unknown')
        return {
            "success": False,
            "symbol": symbol,
            "error": f"Mock trader - real trader failed to load: {self.init_error}",
            "mock": True,
            "pair_config": pair_config
        }


def send_notification(sns_client, topic_arn, subject, message):
    """Send SNS notification"""
    try:
        sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        logger.info(f"Notification sent: {subject}")
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")


def _safe_float(val, default=None):
    """Coerce to float for report; return default if not possible."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def format_execution_report(summary):
    """Format execution summary for email notification. Emphasizes what was posted and at what price."""
    mode_label = "DRY RUN (simulated)" if summary["dry_run"] else "LIVE TRADING"
    report = f"""
Coinbase Trading Bot Execution Report
{'='*50}

Mode: {mode_label}
Timestamp: {summary['timestamp']}
"""

    # --- What was posted (quantity + price) ---
    posted = []
    total_revenue = 0.0
    for result in summary["results"]:
        if not result.get("success") or not result.get("details"):
            continue
        details = result["details"]
        symbol = result.get("symbol", "Unknown")
        qty = details.get("quantity")
        price = details.get("limit_price")
        rev = details.get("expected_revenue")
        if rev is None and qty is not None and price is not None:
            rev = _safe_float(qty) * _safe_float(price)
        if qty is not None and price is not None:
            price_f = _safe_float(price, 0)
            rev_f = rev if isinstance(rev, (int, float)) else _safe_float(rev, 0)
            if rev_f is not None:
                total_revenue += rev_f
            posted.append((symbol, qty, price_f, rev_f))

    if posted:
        report += "\n--- Posted (quantity @ price) ---\n"
        for symbol, qty, price_f, rev_f in posted:
            rev_str = f" ${rev_f:.2f}" if rev_f is not None else ""
            report += f"  {symbol}: {qty} @ ${price_f:.4f} →{rev_str} USD\n"
        if total_revenue > 0:
            report += f"  Total expected: ${total_revenue:.2f} USD\n"
        report += "\n"
    else:
        report += "\n--- No orders posted this run ---\n\n"

    # --- Balance & runout at current sell rate ---
    balance_info = summary.get("balance_info", [])
    if balance_info:
        report += "\n--- Balance & runout at current sell rate ---\n"
        for info in balance_info:
            symbol = info.get("symbol", "?")
            currency = info.get("currency", "?")
            available = info.get("available")
            qty_per_run = info.get("quantity_per_run")
            days_remaining = info.get("days_remaining")
            if available is not None:
                avail_str = f"{available} {currency}"
            else:
                avail_str = "unavailable"
            qty_str = f"{qty_per_run} {currency}/run" if qty_per_run is not None and qty_per_run > 0 else "—"
            if days_remaining is not None:
                days_str = f"~{int(round(days_remaining))} days" if days_remaining >= 0 else "0 days"
            else:
                days_str = "N/A"
            report += f"  {symbol}: {avail_str} | {qty_str} → {days_str} until run out\n"
        report += "\n"
    else:
        report += "\n--- Balance/runout: not available (mock mode or no enabled pairs) ---\n\n"

    # --- Summary and detailed results ---
    report += f"""Execution Summary:
- Processed: {summary['processed_pairs']} pairs | Success: {summary['successful_orders']} | Failed: {summary['failed_orders']}

Detailed Results:
"""
    for result in summary["results"]:
        symbol = result.get("symbol", "Unknown")
        success = result.get("success", False)
        status = "✅ SUCCESS" if success else "❌ FAILED"
        report += f"\n{symbol}: {status}"
        if success:
            if result.get("dry_run"):
                report += " (DRY RUN - no actual order placed)"
            elif result.get("order_id"):
                report += f" - Order ID: {result['order_id']}"
            if result.get("details"):
                details = result["details"]
                qty = details.get("quantity", "N/A")
                price = details.get("limit_price", "N/A")
                if isinstance(price, (int, float)):
                    report += f"\n  Posted: {qty} @ ${price:.4f}"
                    if details.get("expected_revenue") is not None:
                        report += f" → ${float(details['expected_revenue']):.2f} USD"
                else:
                    report += f"\n  Quantity: {qty} | Price: {price}"
        else:
            report += f"\n  Error: {result.get('error', 'Unknown error')}"
        report += "\n"

    report += "\n" + "="*50 + "\nGenerated by AWS Lambda Coinbase Trading Bot"
    return report


def create_response(status_code, body):
    """Create Lambda response"""
    return {
        'statusCode': status_code,
        'body': json.dumps(body) if isinstance(body, (dict, list)) else str(body)
    }