"""
AWS Lambda handler for Coinbase Trading Bot
"""
import json
import logging
import os
import boto3
from botocore.exceptions import ClientError
import sys

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(__file__))

# Import our trading bot (will be packaged with Lambda)
from coinbase_trader import CoinbaseTrader

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')
s3_client = boto3.client('s3')
sns_client = boto3.client('sns')


def get_secret(secret_arn):
    """Retrieve secret from AWS Secrets Manager"""
    try:
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        return json.loads(response['SecretString'])
    except ClientError as e:
        logger.error(f"Error retrieving secret: {e}")
        raise


def get_trading_config(bucket_name):
    """Download trading configuration from S3"""
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key='trading_config.json')
        return json.loads(response['Body'].read().decode('utf-8'))
    except ClientError as e:
        logger.error(f"Error downloading config from S3: {e}")
        raise


def send_notification(topic_arn, subject, message):
    """Send notification via SNS"""
    try:
        sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        logger.info(f"Notification sent: {subject}")
    except ClientError as e:
        logger.error(f"Error sending notification: {e}")


def format_execution_report(results, execution_time):
    """Format execution results into a readable report"""
    successful_orders = sum(1 for r in results if r.get('success'))
    failed_orders = len(results) - successful_orders
    
    total_revenue = sum(
        r['details']['expected_revenue'] 
        for r in results 
        if r.get('success') and 'details' in r
    )
    
    report = [
        "=== Coinbase Trading Bot Execution Report ===",
        f"Execution Time: {execution_time:.2f} seconds",
        f"Total Orders Processed: {len(results)}",
        f"Successful Orders: {successful_orders}",
        f"Failed Orders: {failed_orders}",
        f"Expected Revenue: ${total_revenue:.2f}",
        "",
        "=== Order Details ==="
    ]
    
    for i, result in enumerate(results, 1):
        symbol = result.get('symbol', 'Unknown')
        if result.get('success'):
            details = result.get('details', {})
            report.extend([
                f"{i}. {symbol} - ✅ SUCCESS",
                f"   Current Price: ${details.get('current_price', 0):.4f}",
                f"   Limit Price: ${details.get('limit_price', 0):.4f}",
                f"   Quantity: {details.get('quantity', 0)}",
                f"   Expected Revenue: ${details.get('expected_revenue', 0):.2f}"
            ])
            if 'order_id' in result:
                report.append(f"   Order ID: {result['order_id']}")
        else:
            report.extend([
                f"{i}. {symbol} - ❌ FAILED",
                f"   Error: {result.get('error', 'Unknown error')}"
            ])
        report.append("")
    
    return "\n".join(report)


def lambda_handler(event, context):
    """Main Lambda handler"""
    import time
    start_time = time.time()
    
    logger.info("Starting Coinbase trading bot execution")
    
    # Get environment variables
    config_bucket = os.environ['CONFIG_BUCKET']
    secrets_arn = os.environ['SECRETS_ARN']
    notification_topic_arn = os.environ['NOTIFICATION_TOPIC_ARN']
    
    results = []
    execution_success = False
    
    try:
        # Get API credentials from Secrets Manager
        logger.info("Retrieving API credentials")
        secrets = get_secret(secrets_arn)
        api_key = secrets['api_key']
        private_key = secrets['private_key']
        
        # Get trading configuration from S3
        logger.info("Downloading trading configuration")
        trading_config = get_trading_config(config_bucket)
        
        # Create temporary config file for CoinbaseTrader
        config_path = '/tmp/trading_config.json'
        with open(config_path, 'w') as f:
            json.dump(trading_config, f)
        
        # Create temporary credentials file
        credentials_path = '/tmp/.cdp_api_key.json'
        with open(credentials_path, 'w') as f:
            json.dump({
                'name': api_key,  # This should be the full name format
                'privateKey': private_key
            }, f)
        
        # Initialize trader
        logger.info("Initializing Coinbase trader")
        trader = CoinbaseTrader(
            key_file=credentials_path,
            config_file=config_path
        )
        
        if not trader.config:
            raise Exception("Failed to load trading configuration")
        
        # Get enabled trading pairs
        enabled_pairs = [pair for pair in trader.config["trading_pairs"] if pair.get("enabled", False)]
        logger.info(f"Found {len(enabled_pairs)} enabled trading pairs")
        
        if not enabled_pairs:
            logger.info("No enabled trading pairs found")
            execution_success = True
        else:
            # Execute trading strategy for each enabled pair
            for pair in enabled_pairs:
                try:
                    logger.info(f"Processing {pair['symbol']}")
                    result = trader.place_configured_order(pair, dry_run=False)
                    results.append(result)
                    
                    if result.get('success'):
                        logger.info(f"Successfully placed order for {pair['symbol']}")
                    else:
                        logger.warning(f"Failed to place order for {pair['symbol']}: {result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Exception processing {pair['symbol']}: {e}")
                    results.append({
                        'success': False,
                        'error': str(e),
                        'symbol': pair['symbol']
                    })
            
            execution_success = True
        
    except Exception as e:
        logger.error(f"Critical error in Lambda execution: {e}")
        execution_success = False
        results.append({
            'success': False,
            'error': f"Critical execution error: {str(e)}",
            'symbol': 'SYSTEM'
        })
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Send notification
    successful_orders = sum(1 for r in results if r.get('success'))
    failed_orders = len(results) - successful_orders
    
    if execution_success and failed_orders == 0:
        subject = f"✅ Trading Bot Success - {successful_orders} orders placed"
    elif execution_success and successful_orders > 0:
        subject = f"⚠️ Trading Bot Partial Success - {successful_orders} success, {failed_orders} failed"
    else:
        subject = f"❌ Trading Bot Failed - {failed_orders} errors"
    
    report = format_execution_report(results, execution_time)
    
    try:
        send_notification(notification_topic_arn, subject, report)
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
    
    # Return response
    return {
        'statusCode': 200 if execution_success else 500,
        'body': json.dumps({
            'success': execution_success,
            'orders_processed': len(results),
            'successful_orders': successful_orders,
            'failed_orders': failed_orders,
            'execution_time': execution_time
        })
    }