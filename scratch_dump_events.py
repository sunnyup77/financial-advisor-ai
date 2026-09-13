import sys
import os
import csv

events = []
with open("INFO/dataset/financial_events.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["user_id"] == "user_04":
            events.append(row)

print("All events:")
for e in sorted(events, key=lambda x: x["event_date"]):
    print(f"  {e['event_date']}: {e['event_type']} {e['category']} - {e['description']} | {e['amount']} | {e['direction']}")
