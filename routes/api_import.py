from flask import Blueprint, request, jsonify, session
from utils.auth_middleware import login_required
from utils.db import Session
from models import SocEvent
from sqlalchemy import text
from datetime import datetime
import uuid
import json

bp = Blueprint('import', __name__, url_prefix='/api/import')

SOC_TEMPLATES = {
    "threat_hc": {
        "detect_headers": ["threat_name", "severity", "source address", "destination address", "action"],
        "required_fields": ["source_ip", "severity"],
        "mapping": {
            "Source address": "source_ip",
            "Source": "source_ip",
            "Destination address": "destination_ip",
            "Destination": "destination_ip",
            "Threat Name": "threat_name",
            "threat_name": "threat_name",
            "Severity": "severity",
            "Action": "action",
            "Category": "category",
            "Threat Category": "category",
            "threat-type": "threat_type"
        },
        "jsonb_fields": ["threat_name", "threat_type", "action", "category", "application", "source_user"]
    },
    "url_blocked": {
        "detect_headers": ["url", "category", "source address", "destination address"],
        "required_fields": ["source_ip", "destination_ip"],
        "mapping": {
            "Source address": "source_ip",
            "Source": "source_ip",
            "Destination address": "destination_ip",
            "Destination": "destination_ip",
            "URL": "url",
            "url": "url",
            "Category": "category",
            "category": "category",
            "Action": "action",
            "Rule": "rule",
            "Application": "application"
        },
        "jsonb_fields": ["url", "category", "rule", "application", "source_user", "destination_user"]
    },
    "traffic_rule": {
        "detect_headers": ["source zone", "destination zone", "bytes", "rule"],
        "required_fields": ["bytes"],
        "mapping": {
            "Source Zone": "source_zone",
            "Destination Zone": "dest_zone",
            "Rule": "rule_name",
            "Bytes": "bytes",
            "Bytes Sent": "bytes_sent",
            "Bytes Received": "bytes_received",
            "Sessions": "sessions"
        },
        "jsonb_fields": ["source_zone", "dest_zone", "rule_name"]
    },
    "traffic_daily": {
        "detect_headers": ["day received", "bytes", "sessions"],
        "required_fields": ["event_date", "bytes"],
        "mapping": {
            "Day Received": "event_date",
            "Bytes": "bytes",
            "Sessions": "sessions",
            "Bytes Sent": "bytes_sent",
            "Bytes Received": "bytes_received"
        },
        "jsonb_fields": ["bytes_sent", "bytes_received"]
    }
}

def normalize_header(header):
    """Normalize column header for matching"""
    return str(header).strip().lower()

def detect_template_type(headers):
    """Auto-detect SOC template type from column headers"""
    normalized = [normalize_header(h) for h in headers]
    
    scores = {}
    for template_name, config in SOC_TEMPLATES.items():
        detect_headers = [normalize_header(h) for h in config["detect_headers"]]
        matches = sum(1 for dh in detect_headers if any(dh in nh for nh in normalized))
        scores[template_name] = matches / len(detect_headers)
    
    best_match = max(scores, key=scores.get)
    confidence = scores[best_match]
    
    return {"template_type": best_match if confidence > 0.5 else "unknown", "confidence": confidence}

def map_row_to_event(row, template_type):
    """Map Excel/CSV row to soc_events schema based on template mappings"""
    config = SOC_TEMPLATES.get(template_type)
    if not config:
        return None
    
    mapped = {
        "event_type": template_type,
        "source_ip": None,
        "destination_ip": None,
        "bytes": None,
        "sessions": None,
        "severity": None,
        "event_date": None,
        "payload_data": {}
    }
    
    for col_name, value in row.items():
        normalized_col = str(col_name).strip()
        target_field = config["mapping"].get(normalized_col)
        if not target_field:
            continue
        
        if isinstance(value, str):
            value = value.strip().strip('"')
        
        if target_field in ["bytes", "sessions"]:
            try:
                mapped[target_field] = int(float(value)) if value else None
            except:
                mapped[target_field] = None
        elif target_field == "event_date":
            try:
                if isinstance(value, datetime):
                    mapped["event_date"] = value
                else:
                    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%d-%m-%Y"):
                        try:
                            mapped["event_date"] = datetime.strptime(str(value), fmt)
                            break
                        except:
                            continue
            except:
                mapped["event_date"] = None
        elif target_field == "severity":
            severity_val = str(value).strip().lower() if value else None
            severity_map = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low"}
            mapped["severity"] = severity_map.get(severity_val, severity_val)
        else:
            mapped[target_field] = str(value) if value else None
        
        if target_field in config["jsonb_fields"]:
            mapped["payload_data"][target_field] = str(value) if value else None
    
    return mapped


@bp.route('/soc/detect', methods=['POST'])
@login_required
def detect_soc_template():
    """Auto-detect SOC template type from headers"""
    data = request.get_json()
    headers = data.get('headers', [])
    
    result = detect_template_type(headers)
    return jsonify({'success': True, 'data': result})

@bp.route('/soc/preview', methods=['POST'])
@login_required
def preview_soc_data():
    """Preview first 5 rows with validation"""
    data = request.get_json()
    rows = data.get('data', [])
    template_type = data.get('template_type')
    
    if not template_type or template_type not in SOC_TEMPLATES:
        return jsonify({'success': False, 'error': 'Template type tidak valid'}), 400
    
    config = SOC_TEMPLATES[template_type]
    preview_rows = []
    validation_errors = []
    
    for i, row in enumerate(rows[:5]):
        mapped = map_row_to_event(row, template_type)
        if mapped:
            missing = [f for f in config["required_fields"] if not mapped.get(f)]
            if missing:
                validation_errors.append(f"Baris {i+1}: Field wajib kosong: {', '.join(missing)}")
            preview_rows.append(mapped)
    
    return jsonify({
        'success': True,
        'data': {
            'preview': preview_rows,
            'validation': {
                'valid': len(validation_errors) == 0,
                'errors': validation_errors
            }
        }
    })

@bp.route('/soc/check-existing', methods=['POST'])
@login_required
def check_existing_soc_data():
    """Check if data for this period already exists"""
    data = request.get_json()
    template_type = data.get('template_type')
    period_start = data.get('period_start')
    period_end = data.get('period_end')
    
    session_db = Session()
    try:
        count = session_db.execute(
            text("""
                SELECT COUNT(*) FROM soc_upload_batch 
                WHERE template_type = :template 
                AND period_start = :start 
                AND period_end = :end
            """),
            {"template": template_type, "start": period_start, "end": period_end}
        ).scalar()
        
        last_upload = None
        if count > 0:
            result = session_db.execute(
                text("""
                    SELECT upload_date, total_records 
                    FROM soc_upload_batch 
                    WHERE template_type = :template 
                    AND period_start = :start 
                    AND period_end = :end
                    ORDER BY upload_date DESC LIMIT 1
                """),
                {"template": template_type, "start": period_start, "end": period_end}
            ).fetchone()
            
            if result:
                last_upload = result[0].isoformat()
                count = result[1]
        
        return jsonify({
            'success': True,
            'data': {
                'exists': count > 0,
                'record_count': count if count > 0 else 0,
                'last_upload': last_upload
            }
        })
    finally:
        session_db.close()

@bp.route('/soc/summary', methods=['GET'])
@login_required
def get_soc_summary():
    """Get aggregated summary of imported SOC events for dashboard/charts"""
    session_db = Session()
    try:
        # Total events count
        total_events = session_db.execute(text("SELECT COUNT(*) FROM soc_events")).scalar() or 0
        
        # Events by type
        by_type_res = session_db.execute(text("SELECT event_type, COUNT(*) as count FROM soc_events GROUP BY event_type")).fetchall()
        by_type = {row[0]: row[1] for row in by_type_res if row[0]}
        
        # Top threats (if threat_hc exists)
        threats_sub = text("""
            SELECT payload_data->>'threat_name' AS threat_name
            FROM soc_events
            WHERE event_type = 'threat_hc' AND payload_data->>'threat_name' IS NOT NULL
        """)
        threats_res = session_db.execute(text("""
            SELECT threat_name, COUNT(*) as count FROM (
                SELECT payload_data->>'threat_name' AS threat_name
                FROM soc_events
                WHERE event_type = 'threat_hc' AND payload_data->>'threat_name' IS NOT NULL
            ) sub
            GROUP BY threat_name
            ORDER BY count DESC
            LIMIT 5
        """)).fetchall()
        top_threats = [{"threat": row[0], "count": row[1]} for row in threats_res]
        
        # Traffic daily trend (sum of bytes per day)
        traffic_res = session_db.execute(text("""
            SELECT DATE(event_date) as day, SUM(bytes) as total_bytes, SUM(sessions) as total_sessions
            FROM soc_events
            WHERE event_type = 'traffic_daily' AND event_date IS NOT NULL
            GROUP BY day
            ORDER BY day ASC
            LIMIT 30
        """)).fetchall()
        traffic_trend = [{"date": row[0].isoformat() if row[0] else None, "bytes": int(row[1] or 0), "sessions": int(row[2] or 0)} for row in traffic_res]
        
        return jsonify({
            'success': True,
            'data': {
                'total_events': total_events,
                'by_type': by_type,
                'top_threats': top_threats,
                'traffic_trend': traffic_trend
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session_db.close()

@bp.route('/soc/execute', methods=['POST'])
@login_required
def execute_soc_import():
    """Execute SOC data import with batch delete-insert"""
    data = request.get_json()
    rows = data.get('data', [])
    template_type = data.get('template_type')
    replace_existing = data.get('replace_existing', False)
    period_start = data.get('period_start')
    period_end = data.get('period_end')
    
    if not template_type or template_type not in SOC_TEMPLATES:
        return jsonify({'success': False, 'error': 'Template type tidak valid'}), 400
    
    session_db = Session()
    try:
        user_id = session.get('user_id')
        batch_id = str(uuid.uuid4())
        
        if replace_existing and period_start and period_end:
            session_db.execute(
                text("""
                    DELETE FROM soc_events 
                    WHERE event_type = :template 
                    AND event_date >= :start 
                    AND event_date <= :end
                """),
                {"template": template_type, "start": period_start, "end": period_end}
            )
        
        # Insert batch record FIRST (before events, for FK constraint)
        session_db.execute(
            text("""
                INSERT INTO soc_upload_batch 
                (id, template_type, period_start, period_end, created_by)
                VALUES (:id, :template, :start, :end, :user_id)
            """),
            {
                "id": batch_id,
                "template": template_type,
                "start": period_start,
                "end": period_end,
                "user_id": user_id
            }
        )
        
        inserted_count = 0
        skipped_count = 0
        
        for row in rows:
            mapped = map_row_to_event(row, template_type)
            if not mapped:
                skipped_count += 1
                continue
            
            config = SOC_TEMPLATES[template_type]
            # Validate required fields properly
            is_valid = True
            for f in config["required_fields"]:
                if mapped.get(f) is None:
                    is_valid = False
                    break
            if not is_valid:
                skipped_count += 1
                continue
            
            session_db.execute(
                text("""
                    INSERT INTO soc_events 
                    (event_date, event_type, source_ip, destination_ip, bytes, sessions, severity, payload_data, upload_batch_id, created_at)
                    VALUES (:event_date, :event_type, :source_ip, :destination_ip, :bytes, :sessions, :severity, :payload_data, :batch_id, CURRENT_TIMESTAMP)
                """),
                {
                    "event_date": mapped.get("event_date") or datetime.now(),
                    "event_type": template_type,
                    "source_ip": mapped.get("source_ip"),
                    "destination_ip": mapped.get("destination_ip"),
                    "bytes": mapped.get("bytes"),
                    "sessions": mapped.get("sessions"),
                    "severity": mapped.get("severity"),
                    "payload_data": json.dumps(mapped["payload_data"]),
                    "batch_id": batch_id
                }
            )
            inserted_count += 1
        
        # Update batch with final counts
        session_db.execute(
            text("""
                UPDATE soc_upload_batch 
                SET total_records = :total, skipped_records = :skipped
                WHERE id = :batch_id
            """),
            {
                "total": inserted_count,
                "skipped": skipped_count,
                "batch_id": batch_id
            }
        )
        
        session_db.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'inserted': inserted_count,
                'skipped': skipped_count,
                'batch_id': batch_id
            }
        })
    except Exception as e:
        session_db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session_db.close()
