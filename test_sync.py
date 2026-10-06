#!/usr/bin/env python
import sys
from datetime import datetime, timedelta
from utils.manageengine import ManageEngineSync

me = ManageEngineSync()

to_date = datetime.now().strftime("%Y-%m-%d")
from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

print(f"Fetching requests from {from_date} to {to_date}...")
requests_data = me.fetch_requests(from_date, to_date)

print(f"Got {len(requests_data)} requests")

if requests_data:
    print("\nFirst request structure:")
    import json
    sample = requests_data[0]
    print(json.dumps(sample, indent=2, default=str)[:800])
    
    print("\n\nMapping first request...")
    mapped = me.map_request_to_ticket(requests_data[0])
    print(json.dumps(mapped, indent=2, default=str))
    
    print(f"\n\nUpserting {len(requests_data)} tickets...")
    count = me.upsert_tickets([me.map_request_to_ticket(r) for r in requests_data])
    print(f"✓ Upserted {count} tickets")
else:
    print("No requests fetched")
