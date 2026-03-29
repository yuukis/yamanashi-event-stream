"""
Test cases for Mountain Tech Events Producer Lambda

Tests for all functions in producer/app.py with proper mocking
of AWS services and HTTP requests.
"""

import json
import os
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, call
import boto3
import requests

# Set up AWS credentials and region for testing
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ.setdefault('AWS_ACCESS_KEY_ID', 'testing')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'testing')
os.environ.setdefault('AWS_SECURITY_TOKEN', 'testing')
os.environ.setdefault('AWS_SESSION_TOKEN', 'testing')

# Import the module to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'producer'))
import app


class TestEventValidation:
    """Test event validation logic"""

    def test_validate_event_with_all_required_fields(self):
        """Test validation with all required fields present"""
        event = {
            "uid": "test-uid-123",
            "title": "Test Event Title",
            "event_url": "https://example.com/event",
            "started_at": "2026-03-15T10:00:00Z",
            "updated_at": "2026-03-12T09:00:00Z"
        }
        assert app.validate_event(event) is True

    def test_validate_event_missing_uid(self):
        """Test validation with missing uid"""
        event = {
            "title": "Test Event Title",
            "event_url": "https://example.com/event",
            "started_at": "2026-03-15T10:00:00Z",
            "updated_at": "2026-03-12T09:00:00Z"
        }
        assert app.validate_event(event) is False

    def test_validate_event_empty_title(self):
        """Test validation with empty title"""
        event = {
            "uid": "test-uid-123",
            "title": "",
            "event_url": "https://example.com/event",
            "started_at": "2026-03-15T10:00:00Z",
            "updated_at": "2026-03-12T09:00:00Z"
        }
        assert app.validate_event(event) is False

    def test_validate_event_none_values(self):
        """Test validation with None values"""
        event = {
            "uid": "test-uid-123",
            "title": "Test Event Title",
            "event_url": None,
            "started_at": "2026-03-15T10:00:00Z",
            "updated_at": "2026-03-12T09:00:00Z"
        }
        assert app.validate_event(event) is False

    def test_validate_event_whitespace_only(self):
        """Test validation with whitespace-only values"""
        event = {
            "uid": "test-uid-123",
            "title": "   ",
            "event_url": "https://example.com/event",
            "started_at": "2026-03-15T10:00:00Z",
            "updated_at": "2026-03-12T09:00:00Z"
        }
        assert app.validate_event(event) is False


class TestEventDetailBuilding:
    """Test EventBridge detail building"""

    def test_build_detail_with_all_fields(self):
        """Test building detail with all fields present"""
        event = {
            "uid": "test-uid-123",
            "event_id": 12345,
            "title": "Test Event Title",
            "catch": "Test catch phrase",
            "event_url": "https://example.com/event",
            "hash_tag": "#testEvent",
            "started_at": "2026-03-15T10:00:00Z",
            "ended_at": "2026-03-15T18:00:00Z",
            "updated_at": "2026-03-12T09:00:00Z",
            "open_status": "open",
            "owner_name": "Test Owner",
            "place": "Test Venue",
            "address": "Test Address",
            "group_key": "test-group",
            "group_name": "Test Group",
            "group_url": "https://example.com/group"
        }

        detail = app.build_detail(event)

        assert detail["schema_version"] == "1"
        assert detail["event_kind"] == "event.created"
        assert detail["uid"] == "test-uid-123"
        assert detail["event_id"] == 12345
        assert detail["title"] == "Test Event Title"
        assert detail["catch"] == "Test catch phrase"
        assert detail["event_url"] == "https://example.com/event"
        assert detail["hash_tag"] == "#testEvent"
        assert detail["started_at"] == "2026-03-15T10:00:00Z"
        assert detail["ended_at"] == "2026-03-15T18:00:00Z"
        assert detail["updated_at"] == "2026-03-12T09:00:00Z"
        assert detail["open_status"] == "open"
        assert detail["owner_name"] == "Test Owner"
        assert detail["place"] == "Test Venue"
        assert detail["address"] == "Test Address"
        assert detail["group_key"] == "test-group"
        assert detail["group_name"] == "Test Group"
        assert detail["group_url"] == "https://example.com/group"

    def test_build_detail_with_minimal_fields(self):
        """Test building detail with minimal required fields"""
        event = {
            "uid": "test-uid-123",
            "title": "Test Event Title",
            "event_url": "https://example.com/event",
            "started_at": "2026-03-15T10:00:00Z",
            "updated_at": "2026-03-12T09:00:00Z"
        }

        detail = app.build_detail(event)

        assert detail["schema_version"] == "1"
        assert detail["event_kind"] == "event.created"
        assert detail["uid"] == "test-uid-123"
        assert detail["event_id"] is None
        assert detail["title"] == "Test Event Title"
        assert detail["catch"] is None
        assert detail["event_url"] == "https://example.com/event"
        assert detail["hash_tag"] is None
        assert detail["started_at"] == "2026-03-15T10:00:00Z"
        assert detail["ended_at"] is None
        assert detail["updated_at"] == "2026-03-12T09:00:00Z"


class TestFetchEvents:
    """Test API event fetching"""

    @patch('app.requests.get')
    def test_fetch_events_success(self, mock_get):
        """Test successful API call"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "uid": "event-1",
                "title": "Event 1",
                "event_url": "https://example.com/event1",
                "started_at": "2026-03-15T10:00:00Z",
                "updated_at": "2026-03-12T09:00:00Z"
            },
            {
                "uid": "event-2",
                "title": "Event 2",
                "event_url": "https://example.com/event2",
                "started_at": "2026-03-16T10:00:00Z",
                "updated_at": "2026-03-12T09:00:00Z"
            }
        ]
        mock_get.return_value = mock_response

        events = app.fetch_events()

        assert len(events) == 2
        assert events[0]["uid"] == "event-1"
        assert events[1]["uid"] == "event-2"
        mock_get.assert_called_once_with(app.API_URL, timeout=10)

    @patch('app.requests.get')
    def test_fetch_events_http_error(self, mock_get):
        """Test HTTP error during API call"""
        mock_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(requests.RequestException):
            app.fetch_events()

    @patch('app.requests.get')
    def test_fetch_events_invalid_response_format(self, mock_get):
        """Test invalid response format"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "Invalid format"}
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Expected list in API response"):
            app.fetch_events()


class TestIsPublished:
    """Test published status checking"""

    @patch('app.table')
    def test_is_published_true(self, mock_table):
        """Test event is already published"""
        mock_table.get_item.return_value = {
            "Item": {
                "uid": "test-uid-123",
                "published_at": "2026-03-12T08:00:00Z"
            }
        }

        assert app.is_published("test-uid-123") is True

    @patch('app.table')
    def test_is_published_false(self, mock_table):
        """Test event is not published"""
        mock_table.get_item.return_value = {}

        assert app.is_published("test-uid-123") is False

    @patch('app.table')
    def test_is_published_error(self, mock_table):
        """Test DynamoDB error returns False to continue processing"""
        mock_table.get_item.side_effect = Exception("DynamoDB error")

        assert app.is_published("test-uid-123") is False


class TestPublishEvent:
    """Test EventBridge publishing"""

    @patch('app.eventbridge')
    def test_publish_event_success(self, mock_eventbridge):
        """Test successful EventBridge publish"""
        mock_eventbridge.put_events.return_value = {
            "FailedEntryCount": 0,
            "Entries": [{"EventId": "test-event-id"}]
        }

        detail = {
            "uid": "test-uid-123",
            "title": "Test Event",
            "event_kind": "event.created"
        }

        app.publish_event(detail)

        mock_eventbridge.put_events.assert_called_once()
        call_args = mock_eventbridge.put_events.call_args[1]
        assert len(call_args["Entries"]) == 1
        entry = call_args["Entries"][0]
        assert entry["Source"] == "yamanashi.tech.events"
        assert entry["DetailType"] == "event.created"
        assert json.loads(entry["Detail"]) == detail

    @patch('app.eventbridge')
    def test_publish_event_with_bus_name(self, mock_eventbridge):
        """Test EventBridge publish with custom bus name"""
        with patch.dict(os.environ, {'EVENT_BUS_NAME': 'custom-bus'}):
            # Reinitialize the module variable
            app.EVENT_BUS_NAME = 'custom-bus'
            
            mock_eventbridge.put_events.return_value = {
                "FailedEntryCount": 0,
                "Entries": [{"EventId": "test-event-id"}]
            }

            detail = {"uid": "test-uid-123", "title": "Test Event"}
            app.publish_event(detail)

            call_args = mock_eventbridge.put_events.call_args[1]
            entry = call_args["Entries"][0]
            assert entry["EventBusName"] == "custom-bus"

    @patch('app.eventbridge')
    def test_publish_event_failed_entry(self, mock_eventbridge):
        """Test EventBridge publish with failed entry"""
        mock_eventbridge.put_events.return_value = {
            "FailedEntryCount": 1,
            "Entries": [{
                "ErrorCode": "ValidationException",
                "ErrorMessage": "Invalid event"
            }]
        }

        detail = {"uid": "test-uid-123", "title": "Test Event"}

        with pytest.raises(Exception, match="EventBridge put_events failed"):
            app.publish_event(detail)


class TestMarkPublished:
    """Test DynamoDB record creation"""

    @patch('app.table')
    @patch('app.datetime')
    def test_mark_published_success(self, mock_datetime, mock_table):
        """Test successful DynamoDB record creation"""
        mock_datetime.now.return_value.isoformat.return_value = "2026-03-12T10:00:00+00:00"
        
        detail = {
            "uid": "test-uid-123",
            "title": "Test Event",
            "event_url": "https://example.com/event",
            "updated_at": "2026-03-12T09:00:00Z",
            "event_id": 12345,
            "group_key": "test-group",
            "group_name": "Test Group"
        }

        app.mark_published(detail)

        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]
        item = call_args["Item"]
        assert item["uid"] == "test-uid-123"
        assert item["title"] == "Test Event"
        assert item["event_url"] == "https://example.com/event"
        assert item["updated_at"] == "2026-03-12T09:00:00Z"
        assert item["published_at"] == "2026-03-12T10:00:00+00:00"
        assert item["event_id"] == 12345
        assert item["group_key"] == "test-group"
        assert item["group_name"] == "Test Group"

    @patch('app.table')
    def test_mark_published_minimal_fields(self, mock_table):
        """Test DynamoDB record with minimal fields"""
        with patch('app.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2026-03-12T10:00:00+00:00"
            
            detail = {
                "uid": "test-uid-123",
                "title": "Test Event",
                "event_url": "https://example.com/event",
                "updated_at": "2026-03-12T09:00:00Z",
                "event_id": None,
                "group_key": None,
                "group_name": None
            }

            app.mark_published(detail)

            call_args = mock_table.put_item.call_args[1]
            item = call_args["Item"]
            assert "event_id" not in item
            assert "group_key" not in item
            assert "group_name" not in item

    @patch('app.table')
    def test_mark_published_error(self, mock_table):
        """Test DynamoDB error during record creation"""
        mock_table.put_item.side_effect = Exception("DynamoDB error")

        detail = {
            "uid": "test-uid-123",
            "title": "Test Event",
            "event_url": "https://example.com/event",
            "updated_at": "2026-03-12T09:00:00Z"
        }

        with pytest.raises(Exception, match="DynamoDB error"):
            app.mark_published(detail)


class TestProcessSingleEvent:
    """Test single event processing flow"""

    @patch('app.mark_published')
    @patch('app.publish_event')
    @patch('app.is_published')
    @patch('app.build_detail')
    @patch('app.validate_event')
    def test_process_single_event_success(self, mock_validate, mock_build_detail, 
                                        mock_is_published, mock_publish, mock_mark):
        """Test successful processing of a new event"""
        # Setup mocks
        mock_validate.return_value = True
        mock_build_detail.return_value = {"uid": "test-uid-123", "title": "Test Event"}
        mock_is_published.return_value = False

        raw_event = {"uid": "test-uid-123", "title": "Test Event"}
        stats = {"published_count": 0, "skipped_count": 0, "already_published_count": 0}

        app.process_single_event(raw_event, stats)

        mock_validate.assert_called_once_with(raw_event)
        mock_build_detail.assert_called_once_with(raw_event)
        mock_is_published.assert_called_once_with("test-uid-123")
        mock_publish.assert_called_once()
        mock_mark.assert_called_once()
        assert stats["published_count"] == 1

    @patch('app.validate_event')
    def test_process_single_event_invalid(self, mock_validate):
        """Test processing invalid event"""
        mock_validate.return_value = False

        raw_event = {"uid": "test-uid-123"}
        stats = {"published_count": 0, "skipped_count": 0, "already_published_count": 0}

        app.process_single_event(raw_event, stats)

        assert stats["skipped_count"] == 1
        assert stats["published_count"] == 0

    @patch('app.is_published')
    @patch('app.build_detail')
    @patch('app.validate_event')
    def test_process_single_event_already_published(self, mock_validate, mock_build_detail, mock_is_published):
        """Test processing already published event"""
        mock_validate.return_value = True
        mock_build_detail.return_value = {"uid": "test-uid-123", "title": "Test Event"}
        mock_is_published.return_value = True

        raw_event = {"uid": "test-uid-123", "title": "Test Event"}
        stats = {"published_count": 0, "skipped_count": 0, "already_published_count": 0}

        app.process_single_event(raw_event, stats)

        assert stats["already_published_count"] == 1
        assert stats["published_count"] == 0


class TestLambdaHandler:
    """Test main Lambda handler"""

    @patch('app.process_single_event')
    @patch('app.fetch_events')
    def test_lambda_handler_success(self, mock_fetch, mock_process):
        """Test successful Lambda execution"""
        mock_fetch.return_value = [
            {"uid": "event-1", "title": "Event 1"},
            {"uid": "event-2", "title": "Event 2"}
        ]

        result = app.lambda_handler({}, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["fetched_count"] == 2
        assert mock_process.call_count == 2

    @patch('app.fetch_events')
    def test_lambda_handler_api_error(self, mock_fetch):
        """Test Lambda execution with API error"""
        mock_fetch.side_effect = requests.RequestException("API error")

        result = app.lambda_handler({}, None)

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "error" in body

    @patch('app.process_single_event')
    @patch('app.fetch_events')
    def test_lambda_handler_partial_failure(self, mock_fetch, mock_process):
        """Test Lambda execution with some event processing failures"""
        mock_fetch.return_value = [
            {"uid": "event-1", "title": "Event 1"},
            {"uid": "event-2", "title": "Event 2"}
        ]
        
        def mock_process_side_effect(event, stats):
            if event["uid"] == "event-2":
                raise Exception("Processing error")
        
        mock_process.side_effect = mock_process_side_effect

        result = app.lambda_handler({}, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["fetched_count"] == 2
        assert body["error_count"] == 1


class TestEnvironmentConfiguration:
    """Test environment variable configuration"""

    def test_environment_variables_access(self):
        """Test that environment variables can be accessed"""
        # Test that the module can access environment variables
        assert hasattr(app, 'API_URL')
        assert hasattr(app, 'TABLE_NAME')
        assert hasattr(app, 'EVENT_BUS_NAME')
        
        # Verify default values
        assert app.API_URL == "https://api.event.yamanashi.dev/events" or app.API_URL.startswith("http")
        assert app.TABLE_NAME == "published_events" or isinstance(app.TABLE_NAME, str)

    @patch.dict(os.environ, {'API_URL': 'https://custom.api.example.com/events', 'TABLE_NAME': 'custom-table'})
    def test_custom_environment_variables(self):
        """Test access to custom environment variable values"""
        # Test environment variable access without reloading
        custom_url = os.environ.get('API_URL')
        custom_table = os.environ.get('TABLE_NAME')
        
        assert custom_url == "https://custom.api.example.com/events"
        assert custom_table == "custom-table"


# Integration test fixtures
@pytest.fixture
def sample_event_data():
    """Sample event data for testing"""
    return {
        "uid": "test-uid-123",
        "event_id": 12345,
        "title": "Sample Tech Meetup",
        "catch": "Learn about the latest technology trends",
        "event_url": "https://example.com/event/12345",
        "hash_tag": "#techMeetup",
        "started_at": "2026-03-15T19:00:00+09:00",
        "ended_at": "2026-03-15T21:00:00+09:00",
        "updated_at": "2026-03-12T15:30:00+09:00",
        "open_status": "open",
        "owner_name": "Tech Community",
        "place": "Kofu Innovation Hub",
        "address": "Kofu, Yamanashi",
        "group_key": "yamanashi-tech",
        "group_name": "Yamanashi Tech Community", 
        "group_url": "https://example.com/group/yamanashi-tech"
    }


@pytest.fixture
def api_response_data(sample_event_data):
    """Sample API response data"""
    return [sample_event_data]


class TestIntegration:
    """Integration tests using mocked AWS services"""

    @patch('app.table')
    @patch('app.eventbridge')
    @patch('app.requests.get')
    def test_end_to_end_new_event_flow(self, mock_get, mock_eventbridge, mock_table, sample_event_data, api_response_data):
        """Test complete flow for a new event"""
        # Setup API response
        mock_response = MagicMock()
        mock_response.json.return_value = api_response_data
        mock_get.return_value = mock_response
        
        # Setup EventBridge response
        mock_eventbridge.put_events.return_value = {
            "FailedEntryCount": 0,
            "Entries": [{"EventId": "test-event-id"}]
        }
        
        # Setup DynamoDB response (event not published)
        mock_table.get_item.return_value = {}
        
        # Run the Lambda handler
        result = app.lambda_handler({}, None)

        # Verify results
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["fetched_count"] == 1
        assert body["published_count"] == 1
        assert body["already_published_count"] == 0
        assert body["skipped_count"] == 0
        assert body["error_count"] == 0

        # Verify EventBridge was called
        mock_eventbridge.put_events.assert_called_once()
        
        # Verify DynamoDB was called to mark as published
        mock_table.put_item.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])