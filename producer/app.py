"""
Yamanashi Tech Events Stream Lambda

Fetches event list from Yamanashi Tech Events API,
publishes only new events to EventBridge,
and saves published status to DynamoDB.
"""

import json
import logging
import os
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
import requests

# Logging configuration
logger = logging.getLogger()
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.setLevel(getattr(logging, log_level))

# AWS service clients
dynamodb = boto3.resource("dynamodb")
eventbridge = boto3.client("events")

# Environment variables
API_URL = os.environ.get("API_URL", "https://api.event.yamanashi.dev/events")
EVENT_BUS_NAME = os.environ.get("EVENT_BUS_NAME")
TABLE_NAME = os.environ.get("TABLE_NAME", "published_events")

# DynamoDB table
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda entry point
    
    Args:
        event: Event from EventBridge Scheduler
        context: Lambda context
        
    Returns:
        Processing result summary
    """
    logger.info("Starting Yamanashi Tech Events Stream")
    
    # Statistics counters
    stats = {
        "fetched_count": 0,
        "published_count": 0,
        "skipped_count": 0,
        "already_published_count": 0,
        "error_count": 0
    }
    
    try:
        # 1. Fetch event list
        events = fetch_events()
        stats["fetched_count"] = len(events)
        logger.info(f"Fetched {len(events)} events from API")
        
        # 2. Process each event
        for raw_event in events:
            try:
                process_single_event(raw_event, stats)
            except Exception as e:
                logger.error(f"Failed to process event {raw_event.get('uid', 'unknown')}: {e}")
                stats["error_count"] += 1
        
        # 3. Output result summary
        logger.info(
            f"Producer execution completed - "
            f"fetched: {stats['fetched_count']}, "
            f"published: {stats['published_count']}, "
            f"already_published: {stats['already_published_count']}, "
            f"skipped: {stats['skipped_count']}, "
            f"errors: {stats['error_count']}"
        )
        
        return {
            "statusCode": 200,
            "body": json.dumps(stats)
        }
        
    except Exception as e:
        logger.error(f"Producer execution failed: {e}")
        logger.error(traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


def process_single_event(raw_event: Dict[str, Any], stats: Dict[str, int]) -> None:
    """
    Process a single event
    
    Args:
        raw_event: Raw event data from API
        stats: Statistics counters
    """
    uid = raw_event.get("uid")
    
    # 1. Validate input data
    if not validate_event(raw_event):
        logger.warning(f"Invalid event skipped: uid={uid}")
        stats["skipped_count"] += 1
        return
    
    # 2. Build EventBridge detail
    detail = build_detail(raw_event)
    
    # 3. Check if new event
    if is_published(uid):
        logger.debug(f"Event already published: uid={uid}")
        stats["already_published_count"] += 1
        return
    
    # 4. Publish to EventBridge
    try:
        publish_event(detail)
        logger.info(f"Event published: uid={uid}, title={detail.get('title', 'N/A')}")
    except Exception as e:
        logger.error(f"Failed to publish event to EventBridge: uid={uid}, error={e}")
        raise
    
    # 5. Mark as published (only after successful EventBridge publish)
    try:
        mark_published(detail)
        stats["published_count"] += 1
    except Exception as e:
        logger.error(f"Failed to mark event as published in DynamoDB: uid={uid}, error={e}")
        raise


def fetch_events() -> List[Dict[str, Any]]:
    """
    Fetch event list from Yamanashi Tech Events API
    
    Returns:
        Event list
        
    Raises:
        requests.RequestException: When API request fails
    """
    logger.info(f"Fetching events from {API_URL}")
    
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        
        events = response.json()
        
        if not isinstance(events, list):
            raise ValueError(f"Expected list in API response, got {type(events)}")
            
        return events
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch events from API: {e}")
        raise


def validate_event(event: Dict[str, Any]) -> bool:
    """
    Validate required fields in event data
    
    Args:
        event: Event to validate
        
    Returns:
        True: valid, False: invalid
    """
    required_fields = ["uid", "title", "event_url", "started_at", "updated_at"]
    
    for field in required_fields:
        value = event.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            logger.warning(f"Missing or empty required field '{field}' in event: uid={event.get('uid')}")
            return False
    
    return True


def build_detail(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build EventBridge detail JSON
    
    Args:
        event: Original event data
        
    Returns:
        EventBridge detail
    """
    detail = {
        "schema_version": "1",
        "event_kind": "event.created",
        "uid": event["uid"],
        "event_id": event.get("event_id"),
        "title": event["title"],
        "catch": event.get("catch"),
        "event_url": event["event_url"],
        "hash_tag": event.get("hash_tag"),
        "started_at": event["started_at"],
        "ended_at": event.get("ended_at"),
        "updated_at": event["updated_at"],
        "open_status": event.get("open_status"),
        "owner_name": event.get("owner_name"),
        "place": event.get("place"),
        "address": event.get("address"),
        "group_key": event.get("group_key"),
        "group_name": event.get("group_name"),
        "group_url": event.get("group_url")
    }
    
    return detail


def is_published(uid: str) -> bool:
    """
    Check if event is already published
    
    Args:
        uid: Event UID
        
    Returns:
        True: published, False: not published
    """
    try:
        response = table.get_item(Key={"uid": uid})
        return "Item" in response
        
    except Exception as e:
        logger.error(f"Failed to check if event is published: uid={uid}, error={e}")
        # Treat as not published on error, continue processing
        return False


def publish_event(detail: Dict[str, Any]) -> None:
    """
    Send event to EventBridge
    
    Args:
        detail: EventBridge detail
        
    Raises:
        Exception: When EventBridge publish fails
    """
    entry = {
        "Source": "yamanashi.tech.events",
        "DetailType": "event.created",
        "Detail": json.dumps(detail)
    }
    
    if EVENT_BUS_NAME:
        entry["EventBusName"] = EVENT_BUS_NAME
    
    try:
        response = eventbridge.put_events(Entries=[entry])
        
        # Check EventBridge API response
        if response.get("FailedEntryCount", 0) > 0:
            failed_entries = response.get("Entries", [])
            for idx, entry_result in enumerate(failed_entries):
                if "ErrorCode" in entry_result:
                    error_msg = f"EventBridge put_events failed: {entry_result.get('ErrorCode')} - {entry_result.get('ErrorMessage')}"
                    raise Exception(error_msg)
        
        logger.debug(f"Successfully published event to EventBridge: uid={detail['uid']}")
        
    except Exception as e:
        logger.error(f"Failed to publish event to EventBridge: {e}")
        raise


def mark_published(detail: Dict[str, Any]) -> None:
    """
    Record event as published in DynamoDB
    
    Args:
        detail: EventBridge detail
        
    Raises:
        Exception: When DynamoDB save fails
    """
    current_time = datetime.now(timezone.utc).isoformat()
    
    item = {
        "uid": detail["uid"],
        "updated_at": detail["updated_at"],
        "published_at": current_time,
        "title": detail["title"],
        "event_url": detail["event_url"]
    }
    
    # Optional fields addition
    if detail.get("event_id") is not None:
        item["event_id"] = detail["event_id"]
    if detail.get("group_key") is not None:
        item["group_key"] = detail["group_key"]
    if detail.get("group_name") is not None:
        item["group_name"] = detail["group_name"]
    
    try:
        table.put_item(Item=item)
        logger.debug(f"Successfully marked event as published in DynamoDB: uid={detail['uid']}")
        
    except Exception as e:
        logger.error(f"Failed to mark event as published in DynamoDB: {e}")
        raise


# For local execution
if __name__ == "__main__":
    # Local execution test
    result = lambda_handler({}, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))