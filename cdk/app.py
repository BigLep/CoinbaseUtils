#!/usr/bin/env python3
"""
AWS CDK App for Coinbase Trading Bot Infrastructure
"""
import aws_cdk as cdk
from stacks.trading_bot_stack import TradingBotStack

app = cdk.App()

# Get configuration from CDK context or environment
env = cdk.Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region") or "us-east-1"
)

# Create the trading bot stack
TradingBotStack(
    app, 
    "CoinbaseTradingBotStack",
    env=env,
    description="Infrastructure for automated Coinbase trading bot"
)

app.synth()