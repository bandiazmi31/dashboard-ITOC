import os
from dotenv import load_dotenv
load_dotenv()

from routes.api_import import SOC_TEMPLATES, map_row_to_event
from datetime import datetime

# Debug import for traffic_daily only
row = {
    'Day Received': datetime(2026, 9, 20, 0, 0, 0),
    'Bytes': 2827487531193,
    'Bytes Sent': 104741779391,
    'Bytes Received': 2722745751802,
    'Sessions': 19218013,
    'Source File': '20261002_1442_report_job_1455.csv'
}

mapped = map_row_to_event(row, 'traffic_daily')
print('Mapped:', mapped)
config = SOC_TEMPLATES['traffic_daily']
print('Required fields:', config['required_fields'])
for f in config['required_fields']:
    print(f, mapped.get(f), mapped.get(f) is None)
