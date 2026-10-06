from flask import Blueprint, request, jsonify
from utils.auth_middleware import login_required
from utils.db import Session
from utils.manageengine import ManageEngineSync
from models import Ticket
from sqlalchemy import func, case, cast, Float
from datetime import datetime, timedelta

bp = Blueprint("tickets", __name__, url_prefix="/api/tickets")

@bp.route("/", methods=["GET"])
@login_required
def get_tickets():
    """List tickets with pagination"""
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))
    offset = (page - 1) * limit
    
    session_db = Session()
    try:
        tickets = session_db.query(Ticket).order_by(Ticket.created_time.desc()).offset(offset).limit(limit).all()
        data = [{
            "id": str(t.id),
            "req_id": t.req_id,
            "subject": t.subject,
            "status": t.status,
            "priority": t.priority,
            "created_time": t.created_time.isoformat() if t.created_time else None
        } for t in tickets]
        
        return jsonify({"success": True, "data": data})
    finally:
        session_db.close()

@bp.route("/stats", methods=["GET"])
@login_required
def get_ticket_stats():
    """Get aggregate ticket statistics"""
    session_db = Session()
    try:
        total_count = session_db.query(func.count(Ticket.id)).scalar()
        
        resolved_count = session_db.query(func.count(Ticket.id)).filter(
            Ticket.status.in_(['Resolved', 'Closed'])
        ).scalar()
        
        # Calculate average resolution time in hours
        tickets_with_resolution = session_db.query(Ticket).filter(
            Ticket.resolved_time.isnot(None),
            Ticket.created_time.isnot(None)
        ).all()
        
        if tickets_with_resolution:
            total_hours = sum([
                (t.resolved_time - t.created_time).total_seconds() / 3600
                for t in tickets_with_resolution
            ])
            avg_resolution_hours = total_hours / len(tickets_with_resolution)
        else:
            avg_resolution_hours = 0
        
        # SLA met percentage (simplified - assuming resolved within reasonable time)
        sla_met_count = session_db.query(func.count(Ticket.id)).filter(
            Ticket.status.in_(['Resolved', 'Closed']),
            Ticket.sla_name.isnot(None)
        ).scalar()
        
        sla_met_percent = (sla_met_count / total_count * 100) if total_count > 0 else 0
        
        result = {
            "total_count": total_count,
            "resolved_count": resolved_count,
            "avg_resolution_hours": round(avg_resolution_hours, 1),
            "sla_met_percent": round(sla_met_percent, 1)
        }
        
        return jsonify({"success": True, "data": result})
    finally:
        session_db.close()

@bp.route("/sync", methods=["POST"])
@login_required
def sync_tickets():
    """Trigger manual sync with ManageEngine"""
    me_sync = ManageEngineSync()
    result = me_sync.sync_tickets(days=7)
    
    if result["success"]:
        return jsonify({"success": True, "data": {"synced": result["synced_count"]}})
    else:
        return jsonify({"success": False, "error": result["error"]}), 500
