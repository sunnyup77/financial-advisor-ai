import sys
import os
import csv
from datetime import datetime, timedelta

events = []
with open("INFO/dataset/financial_events.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["user_id"] == "user_04":
            events.append(row)

print(f"User 04 events: {len(events)}")
for e in events:
    print(f"  {e['event_id']}: {e['event_type']} | {e['amount']} | {e['date']} | recurring: {e['is_recurring']} | flexible: {e['flexibility']}")

profile = None
with open("INFO/dataset/financial_profiles.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["user_id"] == "user_04":
            profile = row
            break
print(f"Profile: {profile['current_balance']}, min_balance: {profile['minimum_balance']}")
