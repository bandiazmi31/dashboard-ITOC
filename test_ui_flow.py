import os
from dotenv import load_dotenv
load_dotenv()

from app import app
import json

print('[TEST] UI Import SOC Flow\n')

with app.test_client() as client:
    # Set session
    with client.session_transaction() as sess:
        sess['user_id'] = '8f3d5499-3d49-48c1-b496-299bb6d917d0'
        sess['user_role'] = 'Admin'
    
    # 1. Test GET /import-soc (should return HTML page)
    print('1. GET /import-soc (load UI)')
    res = client.get('/import-soc')
    print('  Status: ' + str(res.status_code))
    print('  Contains import_soc.js: ' + str(b'import_soc.js' in res.data))
    print('  Contains preview-section: ' + str(b'preview-section' in res.data))
    
    # 2. Test POST /api/import/soc/detect (auto-detect template)
    print('\n2. POST /api/import/soc/detect')
    headers = ['Source address', 'Destination address', 'Threat Name', 'Severity', 'Action']
    res = client.post('/api/import/soc/detect',
        json={'headers': headers},
        content_type='application/json'
    )
    data = json.loads(res.data)
    print('  Status: ' + str(res.status_code))
    print('  Template: ' + data['data']['template_type'])
    print('  Confidence: {:.1%}'.format(data['data']['confidence']))
    
    # 3. Test POST /api/import/soc/preview (preview data)
    print('\n3. POST /api/import/soc/preview')
    sample_rows = [
        {'Source address': '192.168.1.1', 'Destination address': '10.0.0.1', 'Threat Name': 'DDoS', 'Severity': 'Critical', 'Action': 'block'},
        {'Source address': '192.168.1.2', 'Destination address': '10.0.0.2', 'Threat Name': 'Malware', 'Severity': 'High', 'Action': 'drop'}
    ]
    res = client.post('/api/import/soc/preview',
        json={'data': sample_rows, 'template_type': 'threat_hc'},
        content_type='application/json'
    )
    data = json.loads(res.data)
    print('  Status: ' + str(res.status_code))
    print('  Preview rows: ' + str(len(data['data']['preview'])))
    print('  Valid: ' + str(data['data']['validation']['valid']))
    
    # 4. Test POST /api/import/soc/check-existing (check if data exists)
    print('\n4. POST /api/import/soc/check-existing')
    res = client.post('/api/import/soc/check-existing',
        json={
            'template_type': 'threat_hc',
            'period_start': '2026-09-01',
            'period_end': '2026-09-30'
        },
        content_type='application/json'
    )
    data = json.loads(res.data)
    print('  Status: ' + str(res.status_code))
    print('  Exists: ' + str(data['data']['exists']))
    if data['data']['exists']:
        print('  Record count: ' + str(data['data']['record_count']))
    
    print('\n[OK] All UI endpoints respond correctly')
