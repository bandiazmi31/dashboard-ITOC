import os
from dotenv import load_dotenv
load_dotenv()
from utils.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='soc_events'::regclass;")).fetchall()
    print('All constraints on soc_events:')
    for row in result:
        print('  ' + row[0] + ': ' + row[1])
