from code.data_loader import DataLoader
loader = DataLoader()
loader.load_all()
evs = [e for e in loader.events if e.user_id == 'user_04']
from collections import defaultdict
groups = defaultdict(list)
for ev in evs:
    groups[(ev.user_id, ev.category, ev.description, ev.direction, ev.currency)].append(ev)

for k, g in groups.items():
    if len(g) >= 2:
        print(f"{k[2]}: {len(g)} occurrences")
        d = sorted([e.event_date for e in g])
        diffs = [(d[i] - d[i-1]).days for i in range(1, len(d))]
        print(f"  Diffs: {diffs}")
