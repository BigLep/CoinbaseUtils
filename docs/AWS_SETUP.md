# AWS Setup Guide for Coinbase Trading Bot

## Prerequisites

1. **AWS Account**: You need an AWS account with programmatic access
2. **AWS CLI**: Install and configure AWS CLI v2
3. **Python**: Python 3.11+ installed locally
4. **CDK**: AWS CDK v2 installed

## Initial Setup Steps

### 1. Install AWS CLI
```bash
# macOS
brew install awscli

# Or download from: https://aws.amazon.com/cli/
```

### 2. Install AWS CDK
```bash
npm install -g aws-cdk
# Verify installation
cdk --version
```

### 3. Configure AWS Credentials

You need to create an IAM user with appropriate permissions for deploying infrastructure.

#### Required IAM Permissions
Create an IAM user with these managed policies:
- `PowerUserAccess` (for development)
- Or create a custom policy with these specific permissions:
  - Lambda: Full access
  - S3: Full access
  - Secrets Manager: Full access
  - SNS: Full access
  - EventBridge: Full access
  - CloudWatch: Full access
  - CloudFormation: Full access
  - IAM: Create/update roles and policies

#### Configure Credentials
```bash
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Enter your preferred region (e.g., us-east-1)
# Enter output format (json)
```

Verify configuration:
```bash
aws sts get-caller-identity
```

### 4. Install Python Dependencies
```bash
# In the project root directory
pip install -r requirements.txt

# In the CDK directory
cd cdk
pip install -r requirements.txt
```

## Deployment Process

### 1. Make Scripts Executable
```bash
chmod +x scripts/*.sh
```

### 2. Deploy Infrastructure
```bash
# Deploy with your email for notifications
./scripts/deploy.sh "your-email@example.com" "us-east-1"
```

This script will:
- Build the Lambda layer with dependencies
- Prepare the Lambda deployment package
- Bootstrap CDK in your account/region
- Deploy the complete infrastructure stack

### 3. Post-Deployment Configuration

After deployment, you need to configure the secrets and upload your trading configuration.

#### A. Update Secrets Manager
1. Go to AWS Secrets Manager console
2. Find the secret named `CoinbaseTradingBotStack-CoinbaseApiCredentials-*`
3. Update the secret with your actual Coinbase API credentials:
   ```json
   {
     "api_key": "organizations/your-org-id/apiKeys/your-key-id",
     "private_key": "-----BEGIN EC PRIVATE KEY-----\nYour-Private-Key-Here\n-----END EC PRIVATE KEY-----"
   }
   ```

#### B. Upload Trading Configuration
1. Find the S3 bucket name from the CloudFormation outputs
2. Upload your `trading_config.json` file:
   ```bash
   aws s3 cp trading_config.json s3://your-config-bucket-name/trading_config.json
   ```

#### C. Confirm Email Subscription
Check your email for the SNS subscription confirmation and click the confirmation link.

## Verify Deployment

### 1. Check CloudFormation Stack
```bash
aws cloudformation describe-stacks --stack-name CoinbaseTradingBotStack --query 'Stacks[0].Outputs'
```

### 2. Test Lambda Function
```bash
# Get the function name from outputs, then invoke it
aws lambda invoke --function-name YourLambdaFunctionName --payload '{}' response.json
cat response.json
```

### 3. Check Logs
```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/CoinbaseTradingBotStack"
```

## Monitoring and Maintenance

### CloudWatch Logs
- Lambda execution logs: `/aws/lambda/CoinbaseTradingBotStack-TradingBotFunction-*`
- Set up log retention: 30 days (configured in CDK)

### CloudWatch Alarms
- Error alarm: Triggers on any Lambda errors
- Notifications sent to your email via SNS

### Cost Monitoring
Expected monthly costs:
- Lambda: ~$0.01 (minimal daily execution)
- Secrets Manager: ~$0.40 per secret
- S3: Negligible storage costs
- SNS: ~$0.50 for notifications
- Total: ~$1-2/month

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure your IAM user has sufficient permissions
   - Check AWS CLI configuration

2. **CDK Bootstrap Fails**
   - Make sure you have CloudFormation permissions
   - Try bootstrapping manually: `cdk bootstrap aws://ACCOUNT/REGION`

3. **Lambda Deployment Fails**
   - Check Lambda layer size (max 250MB unzipped)
   - Verify Python version compatibility

4. **Secrets Manager Access**
   - Ensure the secret name format matches the CDK output
   - Check IAM role permissions for Lambda

### Debug Commands
```bash
# Check CDK diff before deployment
cd cdk && cdk diff

# View CDK synthesized template
cd cdk && cdk synth

# Check Lambda function configuration
aws lambda get-function --function-name YourFunctionName
```

## Security Best Practices

1. **Least Privilege**: Grant minimal required permissions
2. **Secrets Rotation**: Consider rotating API keys regularly
3. **VPC**: For enhanced security, consider deploying Lambda in a VPC
4. **Encryption**: All resources use encryption at rest
5. **Monitoring**: Set up CloudTrail for audit logging

## Future CI/CD Integration

Once you move to GitHub:
1. Create GitHub secrets for AWS credentials
2. Add GitHub Actions workflow for automated deployment
3. Use GitHub environments for production controls
4. Implement automated testing before deployment