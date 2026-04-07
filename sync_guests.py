#!/usr/bin/env python3
"""
Sync GuestDiary.com guests to Mailchimp audience.
Expects the following environment variables:
- GUESTDIARY_API_URL      # Full endpoint URL (property‑specific)
- GUESTDIARY_API_KEY      # API key / token for GuestDiary
- MAILCHIMP_API_KEY       # Mailchimp API key
- MAILCHIMP_SERVER_PREFIX # e.g., 'us19'
- MAILCHIMP_AUDIENCE_ID   # Mailchimp list/audience ID
- DAYS_BACK (optional)    # Number of past days to fetch (default 1)
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
GUESTDIARY_URL = os.environ.get("GUESTDIARY_API_URL")
GUESTDIARY_KEY = os.environ.get("GUESTDIARY_API_KEY")
MAILCHIMP_KEY = os.environ.get("MAILCHIMP_API_KEY")
MAILCHIMP_SERVER = os.environ.get("MAILCHIMP_SERVER_PREFIX")
MAILCHIMP_AUDIENCE_ID = os.environ.get("MAILCHIMP_AUDIENCE_ID")
DAYS_BACK = int(os.environ.get("DAYS_BACK", "1"))

# Temporary email domains to filter out
BLOCKED_DOMAINS = {"guest.booking.com", "expedia.com", "guest.expedia.com"}

if not all([GUESTDIARY_URL, GUESTDIARY_KEY, MAILCHIMP_KEY, MAILCHIMP_SERVER, MAILCHIMP_AUDIENCE_ID]):
    logger.error("Missing required environment variables. Please check your configuration.")
    sys.exit(1)


def fetch_guestdiary_guests() -> List[Dict[str, Any]]:
    """
    Fetch guests from GuestDiary API.
    Assumes the endpoint returns JSON with a list of reservation objects containing
    'email_address', 'first_name', 'last_name'.
    """
    headers = {
        "Authorization": f"Bearer {GUESTDIARY_KEY}",
        "Accept": "application/json"
    }

    # Calculate date range (e.g., last DAYS_BACK days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=DAYS_BACK)

    # This payload is hypothetical; adjust to match your actual GuestDiary API.
    # Many APIs use query parameters like ?from=YYYY-MM-DD&to=YYYY-MM-DD
    params = {
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "status": "checked_out"  # Or "completed"
    }

    all_guests = []
    page = 1
    while True:
        params["page"] = page
        try:
            response = requests.get(GUESTDIARY_URL, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Assume response contains a 'data' or 'reservations' list
            guests_batch = data.get("data") or data.get("reservations") or []
            if not guests_batch:
                break

            all_guests.extend(guests_batch)
            logger.info(f"Fetched page {page} with {len(guests_batch)} guests.")

            # Check for pagination metadata (e.g., 'next_page_url' or 'total_pages')
            if "next_page_url" not in data and page >= data.get("total_pages", 1):
                break

            page += 1
        except requests.exceptions.RequestException as e:
            logger.error(f"GuestDiary API request failed: {e}")
            raise

    logger.info(f"Total guests fetched: {len(all_guests)}")
    return all_guests


def filter_valid_emails(guests: List[Dict]) -> List[Dict]:
    """Filter out temporary/proxy email addresses and ensure required fields exist."""
    valid = []
    for guest in guests:
        email = guest.get("email_address")
        if not email or "@" not in email:
            continue

        domain = email.split("@")[-1].lower()
        if domain in BLOCKED_DOMAINS:
            logger.debug(f"Skipping temporary email: {email}")
            continue

        # Ensure we have at least first/last name (fallback to empty string)
        first_name = guest.get("first_name") or ""
        last_name = guest.get("last_name") or ""

        valid.append({
            "email_address": email.strip().lower(),
            "first_name": first_name.strip(),
            "last_name": last_name.strip()
        })
    logger.info(f"After filtering: {len(valid)} valid guest emails.")
    return valid


def create_mailchimp_batch(guests: List[Dict]) -> Dict:
    """
    Build a Mailchimp batch operation payload.
    Each operation is a PUT request to /lists/{audience_id}/members/{subscriber_hash}
    """
    operations = []
    audience_id = MAILCHIMP_AUDIENCE_ID

    for guest in guests:
        email = guest["email_address"]
        subscriber_hash = email  # Mailchimp accepts email or MD5 hash; using email is simpler

        merge_fields = {}
        if guest["first_name"]:
            merge_fields["FNAME"] = guest["first_name"]
        if guest["last_name"]:
            merge_fields["LNAME"] = guest["last_name"]

        payload = {
            "email_address": email,
            "status": "subscribed",  # or "transactional" if you only send automated emails
            "merge_fields": merge_fields
        }

        operation = {
            "method": "PUT",
            "path": f"/lists/{audience_id}/members/{subscriber_hash}",
            "body": json.dumps(payload)
        }
        operations.append(operation)

    batch_payload = {"operations": operations}
    logger.info(f"Prepared batch with {len(operations)} upsert operations.")
    return batch_payload


def submit_mailchimp_batch(batch_payload: Dict) -> Optional[str]:
    """Submit batch to Mailchimp and return the batch ID."""
    url = f"https://{MAILCHIMP_SERVER}.api.mailchimp.com/3.0/batches"
    auth = ("anystring", MAILCHIMP_KEY)

    try:
        response = requests.post(url, auth=auth, json=batch_payload, timeout=60)
        response.raise_for_status()
        batch_info = response.json()
        batch_id = batch_info.get("id")
        logger.info(f"Batch submitted successfully. Batch ID: {batch_id}")
        return batch_id
    except requests.exceptions.RequestException as e:
        logger.error(f"Mailchimp batch submission failed: {e}")
        if e.response is not None:
            logger.error(f"Response body: {e.response.text}")
        return None


def check_batch_status(batch_id: str) -> None:
    """Optionally poll batch status (runs async in Mailchimp)."""
    url = f"https://{MAILCHIMP_SERVER}.api.mailchimp.com/3.0/batches/{batch_id}"
    auth = ("anystring", MAILCHIMP_KEY)

    try:
        response = requests.get(url, auth=auth, timeout=30)
        response.raise_for_status()
        status = response.json()
        logger.info(f"Batch {batch_id} status: {status.get('status')} "
                    f"(processed: {status.get('processed_operations')}/{status.get('total_operations')})")
    except Exception as e:
        logger.warning(f"Could not check batch status: {e}")


def main():
    logger.info("Starting GuestDiary → Mailchimp sync")
    try:
        # 1. Fetch from GuestDiary
        raw_guests = fetch_guestdiary_guests()

        # 2. Filter temporary emails
        clean_guests = filter_valid_emails(raw_guests)

        if not clean_guests:
            logger.info("No new valid guests to sync.")
            return

        # 3. Prepare Mailchimp batch
        batch = create_mailchimp_batch(clean_guests)

        # 4. Submit batch
        batch_id = submit_mailchimp_batch(batch)
        if batch_id:
            # 5. (Optional) Check status
            check_batch_status(batch_id)

        logger.info("Sync completed successfully.")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()