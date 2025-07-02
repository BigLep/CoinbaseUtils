"""
AWS CDK Stack for Coinbase Trading Bot
"""
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_secretsmanager as secretsmanager,
    aws_s3 as s3,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class TradingBotStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Configuration
        lambda_timeout = Duration.minutes(5)
        notification_email = self.node.try_get_context("notification_email") or "your-email@example.com"
        
        # S3 Bucket for trading configuration
        config_bucket = s3.Bucket(
            self, "TradingConfigBucket",
            bucket_name=f"coinbase-trading-config-{self.account}-{self.region}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.RETAIN
        )

        # Secrets Manager for API credentials
        coinbase_secrets = secretsmanager.Secret(
            self, "CoinbaseApiCredentials",
            description="Coinbase API credentials for trading bot",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"api_key": ""}',
                generate_string_key="private_key",
                password_length=2048,  # Large enough for PEM key
                exclude_characters=' \t\n\r'
            )
        )

        # SNS Topic for notifications
        notification_topic = sns.Topic(
            self, "TradingBotNotifications",
            display_name="Coinbase Trading Bot Notifications"
        )

        # Add email subscription
        notification_topic.add_subscription(
            subscriptions.EmailSubscription(notification_email)
        )

        # Lambda execution role
        lambda_role = iam.Role(
            self, "TradingBotLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # Grant permissions to Lambda role
        config_bucket.grant_read(lambda_role)
        coinbase_secrets.grant_read(lambda_role)
        notification_topic.grant_publish(lambda_role)

        # Lambda Layer for dependencies
        dependencies_layer = _lambda.LayerVersion(
            self, "TradingBotDependencies",
            code=_lambda.Code.from_asset("../lambda_layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            description="Dependencies for Coinbase trading bot"
        )

        # Lambda function
        trading_lambda = _lambda.Function(
            self, "TradingBotFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("../lambda"),
            role=lambda_role,
            timeout=lambda_timeout,
            memory_size=256,
            layers=[dependencies_layer],
            environment={
                "CONFIG_BUCKET": config_bucket.bucket_name,
                "SECRETS_ARN": coinbase_secrets.secret_arn,
                "NOTIFICATION_TOPIC_ARN": notification_topic.topic_arn,
                "LOG_LEVEL": "INFO"
            },
            log_retention=logs.RetentionDays.ONE_MONTH
        )

        # EventBridge rule for daily execution
        # Schedule for 6:15 AM UTC daily (avoids peak times)
        schedule_rule = events.Rule(
            self, "TradingBotSchedule",
            description="Daily execution of Coinbase trading bot",
            schedule=events.Schedule.cron(
                minute="15",
                hour="6",
                day="*",
                month="*",
                year="*"
            )
        )

        # Add Lambda as target
        schedule_rule.add_target(
            targets.LambdaFunction(trading_lambda)
        )

        # CloudWatch alarm for Lambda errors
        error_alarm = trading_lambda.metric_errors().create_alarm(
            self, "TradingBotErrorAlarm",
            threshold=1,
            evaluation_periods=1,
            alarm_description="Trading bot Lambda function errors"
        )

        # Send alarm notifications to SNS
        error_alarm.add_alarm_action(
            cdk.aws_cloudwatch_actions.SnsAction(notification_topic)
        )

        # Outputs
        cdk.CfnOutput(
            self, "ConfigBucketName",
            value=config_bucket.bucket_name,
            description="S3 bucket for trading configuration"
        )

        cdk.CfnOutput(
            self, "SecretsManagerArn",
            value=coinbase_secrets.secret_arn,
            description="Secrets Manager ARN for API credentials"
        )

        cdk.CfnOutput(
            self, "LambdaFunctionName",
            value=trading_lambda.function_name,
            description="Lambda function name"
        )

        cdk.CfnOutput(
            self, "NotificationTopicArn",
            value=notification_topic.topic_arn,
            description="SNS topic for notifications"
        )