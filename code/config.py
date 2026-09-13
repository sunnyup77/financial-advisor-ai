import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "INFO", "dataset")

REQUESTS_CSV = os.path.join(DATASET_DIR, "requests.csv")
SAMPLE_REQUESTS_CSV = os.path.join(DATASET_DIR, "sample_requests.csv")
PROFILES_CSV = os.path.join(DATASET_DIR, "financial_profiles.csv")
EVENTS_CSV = os.path.join(DATASET_DIR, "financial_events.csv")
EXCHANGE_RATES_CSV = os.path.join(DATASET_DIR, "exchange_rates.csv")
PAYMENT_OPTIONS_CSV = os.path.join(DATASET_DIR, "request_payment_options.csv")
MESSAGES_CSV = os.path.join(DATASET_DIR, "messages.csv")
IMAGES_CSV = os.path.join(DATASET_DIR, "images.csv")
IMAGES_MEDIA_DIR = os.path.join(DATASET_DIR, "media", "images")
