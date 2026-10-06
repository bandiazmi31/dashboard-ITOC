import os
from dotenv import load_dotenv
load_dotenv()
from utils.db import Session
from sqlalchemy import text

session = Session()
try:
    result = session.execute(text("SELECT id FROM users WHERE role='Admin' LIMIT 1")).fetchone()
    admin_id = result[0] if result else None
    print('admin_id: ' + str(admin_id))
finally:
    session.close()
