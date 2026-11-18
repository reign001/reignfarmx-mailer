
from datetime import datetime, timezone
from collections import Counter
from pprint import pprint
import time
import requests

from app import create_app
from app.services.hostinger_delivery_service import (
    HostingerDeliveryService
)


app = create_app()

with app.app_context():

    all_logs = []
    page = 1
    per_page = 20

    while True:
        print(f"Fetching page {page}...")

        success = False

        for attempt in range(3):
            try:
                result = HostingerDeliveryService.get_outbound_logs(
                    from_date=datetime(
                        2026, 11, 1,
                        tzinfo=timezone.utc
                    ),
                    page=page,
                    per_page=per_page
                )

                batch = result.get("data", [])
                all_logs.extend(batch)

                print(f"Retrieved {len(batch)} records.")

                success = True
                break

            except requests.exceptions.RequestException as e:
                print(
                    f"Attempt {attempt + 1} failed: {e}"
                )
                time.sleep(3)

        if not success:
            print(f"Could not retrieve page {page}. Stopping.")
            break

        if len(batch) < per_page:
            break

        page += 1
        time.sleep(1)

    status_counts = Counter()
    failure_reasons = Counter()

    for item in all_logs:
        status = item.get("status", "Unknown")
        status_counts[status] += 1

        if status != "Delivered":
            events = item.get("relay_events", [])

            if not events:
                failure_reasons["No relay event recorded"] += 1

            for event in events:
                reason = (
                    event.get("response")
                    or "No response recorded"
                )
                failure_reasons[reason] += 1

    print("\nTOTAL RECORDS:", len(all_logs))

    print("\nSTATUS SUMMARY:")
    pprint(dict(status_counts))

    print("\nFAILURE REASONS:")
    pprint(dict(failure_reasons))
