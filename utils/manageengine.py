import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import Config
from models import Ticket
from utils.db import Session
import time

class ManageEngineSync:
    def __init__(self):
        self.base_url = Config.MANAGEENGINE_BASE_URL
        self.api_key = Config.TECHNICIAN_KEY
        self.headers = {
            "TECHNICIAN_KEY": self.api_key,
            "Accept": "application/json"
        }

    def fetch_requests(self, from_date: str, to_date: str) -> List[Dict]:
        """
        Fetch requests from ManageEngine API v3 with pagination
        from_date and to_date format: YYYY-MM-DD
        """
        all_requests = []
        offset = 1
        limit = 100
        
        while True:
            try:
                url = f"{self.base_url}/requests"
                
                # ManageEngine SDP v3 requires input_data as JSON string
                input_data = {
                    "list_info": {
                        "row_count": limit,
                        "start_index": offset,
                        "sort_field": "created_time",
                        "sort_order": "desc"
                    }
                }
                
                params = {
                    "input_data": json.dumps(input_data)
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code != 200:
                    print(f"ManageEngine API status {response.status_code}: {response.text}")
                    break
                    
                data = response.json()
                
                # Check response status from SDP body
                response_status = data.get("response_status", {})
                if isinstance(response_status, dict) and response_status.get("status_code") not in [200, 2000, None]:
                    print(f"SDP Error: {response_status.get('messages')}")
                    break
                
                requests_data = data.get("requests", [])
                if not requests_data:
                    break
                    
                all_requests.extend(requests_data)
                
                list_info = data.get("list_info", {})
                has_more = list_info.get("has_more_rows", False)
                
                if not has_more or len(requests_data) < limit:
                    break
                    
                offset += limit
                time.sleep(0.3)
                
            except requests.exceptions.RequestException as e:
                print(f"ManageEngine API network error at offset {offset}: {e}")
                break
        
        return all_requests

    def map_request_to_ticket(self, req_data: Dict) -> Dict:
        """Map ManageEngine request fields to local ticket schema"""
        # Handle cases where item is directly in dict or wrapped in 'request'
        request_info = req_data.get("request", req_data) if isinstance(req_data, dict) else {}
        
        technician_info = request_info.get("technician")
        technician_name = technician_info.get("name", "") if isinstance(technician_info, dict) else ""
        
        requester_info = request_info.get("requester")
        requester_name = requester_info.get("name", "") if isinstance(requester_info, dict) else ""
        
        category_info = request_info.get("category")
        category_name = category_info.get("name", "") if isinstance(category_info, dict) else ""
        
        subcategory_info = request_info.get("subcategory")
        subcategory_name = subcategory_info.get("name", "") if isinstance(subcategory_info, dict) else ""
        
        priority_info = request_info.get("priority")
        priority_name = priority_info.get("name", "") if isinstance(priority_info, dict) else ""
        
        status_info = request_info.get("status")
        status_name = status_info.get("name", "") if isinstance(status_info, dict) else ""
        
        sla_info = request_info.get("sla")
        sla_name = sla_info.get("name", "") if isinstance(sla_info, dict) else ""
        
        mode_info = request_info.get("mode")
        mode_name = mode_info.get("name", "Web") if isinstance(mode_info, dict) else "Web"
        
        created_time_obj = request_info.get("created_time")
        created_time_ms = created_time_obj.get("value") if isinstance(created_time_obj, dict) else None
        created_time = datetime.fromtimestamp(int(created_time_ms) / 1000) if created_time_ms else None
        
        resolved_time_obj = request_info.get("resolved_time")
        resolved_time_ms = resolved_time_obj.get("value") if isinstance(resolved_time_obj, dict) else None
        resolved_time = datetime.fromtimestamp(int(resolved_time_ms) / 1000) if resolved_time_ms else None
        
        return {
            "req_id": str(request_info.get("id", "")),
            "mode": mode_name,
            "requester": requester_name,
            "category": category_name,
            "subcategory": subcategory_name,
            "subject": request_info.get("subject", ""),
            "technician": technician_name,
            "sla_name": sla_name,
            "priority": priority_name,
            "created_time": created_time,
            "resolved_time": resolved_time,
            "status": status_name
        }

    def upsert_tickets(self, tickets_data: List[Dict]) -> int:
        """Bulk upsert tickets to local database using batch operations"""
        session = Session()
        upserted_count = 0
        batch_size = 100
        
        try:
            req_ids = [t["req_id"] for t in tickets_data]
            existing_tickets = session.query(Ticket).filter(Ticket.req_id.in_(req_ids)).all()
            existing_map = {t.req_id: t for t in existing_tickets}
            
            to_insert = []
            to_update = []
            
            for ticket_data in tickets_data:
                if ticket_data["req_id"] in existing_map:
                    ticket = existing_map[ticket_data["req_id"]]
                    for key, value in ticket_data.items():
                        setattr(ticket, key, value)
                    ticket.updated_at = datetime.utcnow()
                    to_update.append(ticket)
                else:
                    to_insert.append(Ticket(**ticket_data))
                upserted_count += 1
            
            # Batch insert
            if to_insert:
                for i in range(0, len(to_insert), batch_size):
                    batch = to_insert[i:i+batch_size]
                    session.bulk_save_objects(batch)
                    session.commit()
            
            # Batch update
            if to_update:
                session.commit()
            
            return upserted_count
            
        except Exception as e:
            session.rollback()
            print(f"Upsert error: {e}")
            raise
        finally:
            session.close()

    def sync_tickets(self, days: int = 30) -> Dict:
        """
        Main sync function: fetch from ManageEngine and upsert to local DB
        Returns: {success: bool, synced_count: int, error: str}
        """
        try:
            to_date = datetime.now().strftime("%Y-%m-%d")
            from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            print(f"Syncing tickets from {from_date} to {to_date}...")
            
            raw_requests = self.fetch_requests(from_date, to_date)
            
            if not raw_requests:
                return {"success": True, "synced_count": 0, "error": None}
            
            tickets_data = [self.map_request_to_ticket(req) for req in raw_requests]
            
            synced_count = self.upsert_tickets(tickets_data)
            
            print(f"✓ Synced {synced_count} tickets")
            
            return {"success": True, "synced_count": synced_count, "error": None}
            
        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            print(f"✗ {error_msg}")
            return {"success": False, "synced_count": 0, "error": error_msg}
