# Yamanashi Event Stream Producer

A serverless AWS Lambda application that fetches tech events from Yamanashi region and publishes them to EventBridge for event-driven processing.

## Features

- 🚀 **Serverless**: AWS Lambda with Python 3.12
- 📡 **Event-Driven**: Publishes to EventBridge custom bus
- 🗄️ **Deduplication**: DynamoDB tracks published events
- ⏰ **Scheduled**: Runs automatically via EventBridge Scheduler  
- 🧪 **Tested**: Comprehensive test suite (28 tests)
- 🔄 **CI/CD**: GitHub Actions deployment pipeline

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│  EventBridge    │    │    Lambda    │    │   Yamanashi     │
│   Scheduler     ├───►│   Producer   ├───►│   Events API    │
└─────────────────┘    └──────┬───────┘    └─────────────────┘
                              │
                              ▼
                      ┌───────────────┐    ┌─────────────────┐
                      │  EventBridge  │    │    DynamoDB     │
                      │  Custom Bus   │    │ Published Events│
                      └───────────────┘    └─────────────────┘
```

## Project Structure

```
yamanashi-event-stream/
├── .github/workflows/
│   └── deploy.yml         # CI/CD pipeline
├── producer/
│   ├── app.py             # Lambda function
│   └── requirements.txt   # Lambda dependencies
├── tests/
│   ├── test_app.py        # Test suite  
│   └── requirements.txt   # Test dependencies
├── template.yaml          # SAM template
├── samconfig.toml         # SAM configuration
└── requirements.txt       # Development dependencies
```

## Quick Start

### Prerequisites

- AWS CLI configured
- Python 3.12+
- SAM CLI

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd yamanashi-event-stream

# Install dependencies
pip install -r requirements.txt -r tests/requirements.txt

# Run tests
python -m pytest tests/ -v
```

### Local Testing

```bash
# Build Lambda
sam build

# Invoke locally
sam local invoke ProducerFunction

# View logs
sam logs -n ProducerFunction --stack-name yamanashi-event-stream-dev --tail
```

### Deploy

```bash
# Development environment
sam build
sam deploy --no-fail-on-empty-changeset

# Production environment  
sam deploy --config-env production --no-fail-on-empty-changeset
```

## GitHub Actions Deployment

### Setup AWS Credentials

**Option 1: IAM User (Simple)**
```bash
# Create IAM user with deployment permissions
aws iam create-user --user-name github-actions-deployer

# Set GitHub Secrets:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
```

**Option 2: OIDC (Recommended)**
```bash
# Create OIDC provider and IAM role
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com

# Set GitHub Secret:
# - AWS_ROLE_TO_ASSUME
```

### Deployment Workflow

- **`main` branch** → Production environment
- **`develop` branch** → Development environment
- **Pull Requests** → Run tests only

## AWS Resources

| Environment | Stack Name | Resources |
|-------------|------------|-----------|
| Development | `yamanashi-event-stream-dev` | Lambda, EventBridge, DynamoDB |
| Production | `yamanashi-event-stream-prod` | Lambda, EventBridge, DynamoDB |

## Monitoring

```bash
# View CloudWatch logs
sam logs -n ProducerFunction --stack-name <stack-name> --tail

# Check DynamoDB records
aws dynamodb scan --table-name <stack-name>-published-events --max-items 10

# List EventBridge buses
aws events list-event-buses --query 'EventBuses[?contains(Name, `yamanashi`)]'
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

Apache 2.0 License - see [LICENSE](LICENSE) file for details.