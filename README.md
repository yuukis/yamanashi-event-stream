# Yamanashi Tech Events Stream Producer

A serverless AWS Lambda application that fetches tech events from Yamanashi region and publishes them to EventBridge for event-driven processing.

## ✨ Features

- 🚀 **Serverless**: AWS Lambda with Python 3.12
- 📡 **Event-Driven**: EventBridge + multiple Consumer buses support  
- 🗄️ **Deduplication**: DynamoDB prevents duplicate events
- 🧪 **Testing**: Parameter-based test mode with dummy events
- 🔄 **CI/CD**: Automated GitHub Actions deployment

## 🏗️ Architecture

```
EventBridge Scheduler → Lambda Producer → Yamanashi Tech Events API
                             ↓
                      EventBridge Bus(es) + DynamoDB
```

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured
- Python 3.12+ 
- SAM CLI

```bash
# Setup
git clone <repository-url>
cd yamanashi-event-stream
pip install -r requirements.txt -r tests/requirements.txt

# Test
python -m pytest tests/ -v

# Deploy
sam build && sam deploy
```

## 🧪 Consumer Testing

Test Consumer applications with dummy events:

```bash
# Test mode - single execution
echo '{"test_mode": true}' | sam local invoke ProducerFunction

# Production deployment with Consumers
sam deploy --parameter-overrides ConsumerBusArns="arn:aws:events:region:account:event-bus/consumer-1,arn:aws:events:region:account:event-bus/consumer-2"
```

**Test Mode Behavior:**
- Generates 1 dummy event: "【テスト用】山梨Tech勉強会"
- Publishes to local bus + all configured Consumer buses
- No external API calls
- Automatic return to normal mode after execution

## � EventBridge Integration

**For Consumer Applications:**

| Environment | EventBus Name | Event Source | Detail Type |
|-------------|---------------|--------------|-------------|
| Development | `yamanashi-events-dev` | `yamanashi.tech.events` | `event.created` |
| Production | `yamanashi-events` | `yamanashi.tech.events` | `event.created` |

**Consumer Setup Example:**
```yaml
EventRule:
  Type: AWS::Events::Rule
  Properties:
    EventBusName: yamanashi-events  # or yamanashi-events-dev
    EventPattern:
      source: ["yamanashi.tech.events"]
      detail-type: ["event.created"]
    Targets:
      - Arn: !GetAtt YourConsumerFunction.Arn
        Id: "YamanashiEventConsumer"
```

## �📁 Project Structure

```
yamanashi-event-stream/
├── producer/app.py          # Main Lambda function
├── tests/test_app.py        # Test suite (38 tests)
├── template.yaml            # AWS SAM template
├── .github/workflows/       # CI/CD pipeline
└── samconfig.toml          # Deployment config
```

## 🔧 Environment Configuration

| Parameter | Description | Example |
|-----------|-------------|---------|
| `Stage` | Environment name | `dev`, `production` |
| `ConsumerBusArns` | External Consumer buses (comma-separated) | `arn:aws:events:...` |
| `LogLevel` | Logging level | `INFO`, `DEBUG` |

## 📊 Monitoring

```bash
# View logs
sam logs -n ProducerFunction --stack-name yamanashi-event-stream-dev --tail

# Check published events
aws dynamodb scan --table-name yamanashi-event-stream-dev-published-events
```

## 🚢 Deployment

- **`main` branch** → Production environment
- **`develop` branch** → Development environment  
- **Pull Requests** → Tests only

Deployment uses GitHub Actions with AWS OIDC authentication.

---

**License:** Apache 2.0