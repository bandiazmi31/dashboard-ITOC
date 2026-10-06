from flask import Blueprint, request, jsonify
from utils.auth_middleware import login_required
from utils.db import Session
from models import Handover

bp = Blueprint("handovers", __name__, url_prefix="/api/handovers")

@bp.route("/", methods=["GET"])
@login_required
def get_handovers():
    """Get list of handovers"""
    session_db = Session()
    try:
        handovers = session_db.query(Handover).order_by(Handover.created_at.desc()).limit(50).all()
        data = [{
            "id": str(h.id),
            "text": h.text,
            "site": h.site,
            "priority": h.priority,
            "date": h.date.isoformat() if h.date else None,
            "shift": h.shift,
            "open": h.open
        } for h in handovers]
        
        return jsonify({"success": True, "data": data})
    finally:
        session_db.close()
