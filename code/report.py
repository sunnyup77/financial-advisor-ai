from code.data_loader import DataLoader

def run_report():
    print("Loading datasets...")
    loader = DataLoader()
    try:
        loader.load_all()
        print("Successfully loaded datasets.")
    except Exception as e:
        print(f"Error loading datasets: {e}")
        return

    print(f"\nData Quality Report:")
    print(f"Requests: {len(loader.requests)}")
    print(f"Sample Requests: {len(loader.sample_requests)}")
    print(f"Profiles: {len(loader.profiles)}")
    print(f"Events: {len(loader.events)}")
    print(f"Exchange Rates: {len(loader.rates)}")
    print(f"Payment Options: {len(loader.payment_options)}")
    print(f"Messages: {len(loader.messages)}")
    print(f"Images: {len(loader.images)}")

    print("\nValidating Relationships...")
    errors = loader.validate_relationships()
    if errors:
        print(f"Found {len(errors)} relationship errors:")
        for err in errors[:10]:
            print(f" - {err}")
        if len(errors) > 10:
            print(" ... (truncated)")
    else:
        print("All relationships validated successfully.")

if __name__ == "__main__":
    run_report()
