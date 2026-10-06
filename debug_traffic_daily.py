import os
from dotenv import load_dotenv
load_dotenv()

from routes.api_import import SOC_TEMPLATES, map_row_to_event
from datetime import datetime

row_sample = {
    'Day Received': datetime(2026, 9, 20, 0, 0, 0),
    'Bytes': 2827487531193,
    'Bytes Sent': 104741779391,
    'Bytes Received': 2722745751802,
    'Sessions': 19218013,
    'Source File': '20261002_1442_report_job_1455.csv'
}

print('Template config:')
config = SOC_TEMPLATES['traffic_daily']
print('  mapping: ' + str(config['mapping']))
print('  required_fields: ' + str(config['required_fields']))

mapped = map_row_to_event(row_sample, 'traffic_daily')
print('\nMapped result:')
for k, v in mapped.items():
    print('  ' + k + ': ' + str(v))

print('\nValidation:')
for field in config['required_fields']:
    val = mapped.get(field)
    print('  ' + field + ': ' + str(val) + ' (valid: ' + str(bool(val)) + ')')
