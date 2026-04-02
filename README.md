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

## 🤝 Consumer Development Guide

**For External Developers:** Build applications that consume Yamanashi tech events

### 📦 Event Schema

Each event contains the following structure:

```json
{
  "source": "yamanashi.tech.events",
  "detail-type": "event.created",
  "detail": {
    "schema_version": "1",
    "event_kind": "event.created",
    "uid": "event-12345",
    "event_id": 67890,
    "title": "山梨Tech勉強会 #42",
    "catch": "Pythonでサーバーレス開発を学ぼう",
    "event_url": "https://yamanashi.tech/events/67890",
    "hash_tag": "#山梨Tech",
    "started_at": "2026-04-15T19:00:00+09:00",
    "ended_at": "2026-04-15T21:00:00+09:00",
    "updated_at": "2026-04-01T10:30:00+00:00",
    "open_status": "open",
    "owner_name": "山梨Tech Community",
    "place": "甲府市市民会館",
    "address": "山梨県甲府市青沼3-5-44",
    "group_key": "yamanashi-tech",
    "group_name": "山梨Tech Community",
    "group_url": "https://yamanashi.tech"
  }
}
```

### 🔧 Quick Consumer Setup

1. **Create EventBridge Rule**:
```yaml
Resources:
  YamanashiEventsRule:
    Type: AWS::Events::Rule
    Properties:
      EventBusName: yamanashi-events
      EventPattern:
        source: ["yamanashi.tech.events"]
        detail-type: ["event.created"]
      Targets:
        - Arn: !GetAtt MyConsumerLambda.Arn
          Id: "EventConsumer"
          
  LambdaInvokePermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref MyConsumerLambda
      Action: lambda:InvokeFunction
      Principal: events.amazonaws.com
      SourceArn: !GetAtt YamanashiEventsRule.Arn
```

2. **Lambda Handler Example** (Python):
```python
def lambda_handler(event, context):
    # Extract event details
    detail = event["detail"]
    event_title = detail["title"]
    event_url = detail["event_url"]
    start_time = detail["started_at"]
    
    print(f"New event: {event_title}")
    print(f"URL: {event_url}")
    print(f"Starts: {start_time}")
    
    # Your processing logic here
    # - Send to Slack/Discord
    # - Store in database
    # - Trigger workflows
    
    return {"statusCode": 200}
```

3. **Cross-Account Setup**:
```yaml
# Add consumer bus ARNs to Producer deployment
ConsumerBusArns: "arn:aws:events:ap-northeast-1:YOUR-ACCOUNT:event-bus/your-consumer-bus"
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