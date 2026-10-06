import os
import json
from dotenv import load_dotenv
load_dotenv()
from app import app

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_id'] = '8f3d5499-3d49-48c1-b496-299bb6d917d0'
        sess['user_role'] = 'Admin'
    
    res = client.get('/api/import/soc/summary')
    data = json.loads(res.data)
    print('Status:', res.status_code)
    print('Success:', data.get('success'))
    if data.get('success'):
        print('Total events:', data['data']['total_events'])
        print('By type:', data['data']['by_type'])
        print('Top threats:', data['data']['top_threats'])
        print('Traffic trend entries:', len(data['data']['traffic_trend']))
    else:
        print('Error:', data.get('error'))
