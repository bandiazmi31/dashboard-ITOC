from flask import Blueprint, request, jsonify
from utils.auth_middleware import login_required
from utils.db import Session
from models import SocEvent
from sqlalchemy import func
from datetime import datetime, timedelta

bp = Blueprint('soc', __name__, url_prefix='/api/soc')

@bp.route('/events', methods=['GET'])
@login_required
def get_soc_events():
    """List SOC events with filtering and pagination"""
    severity = request.args.get('severity', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    offset = (page - 1) * limit
    
    session = Session()
    try:
        query = session.query(SocEvent)
        
        if severity:
            query = query.filter_by(severity=severity)
        
        events = query.order_by(SocEvent.date.desc()).offset(offset).limit(limit).all()
        data = [{
            'id': str(e.id),
            'date': e.date.isoformat() if e.date else None,
            'threat_name': e.threat_name,
            'category': e.category,
            'action': e.action,
            'severity': e.severity,
            'source_ip': e.source_ip,
            'destination_ip': e.destination_ip
        } for e in events]
        
        return jsonify({'success': True, 'data': data})
    finally:
        session.close()

@bp.route('/daily-trend', methods=['GET'])
@login_required
def get_daily_trend():
    """Get threat trend by severity for last 14 days"""
    session = Session()
    try:
        today = datetime.now()
        start_date = today - timedelta(days=14)
        
        # Group by date and severity
        trend_data = session.query(
            func.date(SocEvent.date).label('date'),
            SocEvent.severity,
            func.count(SocEvent.id).label('count')
        ).filter(SocEvent.date >= start_date).group_by(
            func.date(SocEvent.date),
            SocEvent.severity
        ).all()
        
        # Organize data for frontend chart
        date_map = {}
        for row in trend_data:
            date_str = row[0].isoformat()
            if date_str not in date_map:
                date_map[date_str] = {'date': date_str, 'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
            date_map[date_str][row[1]] = row[2]
        
        result = sorted(date_map.values(), key=lambda x: x['date'])
        return jsonify({'success': True, 'data': result})
    finally:
        session.close()

@bp.route('/blocked-urls', methods=['GET'])
@login_required
def get_blocked_urls():
    """Top blocked destination IPs"""
    limit = int(request.args.get('limit', 10))
    
    session = Session()
    try:
        blocked = session.query(
            SocEvent.destination_ip,
            func.count(SocEvent.id).label('count')
        ).filter(SocEvent.action == 'Blocked').group_by(
            SocEvent.destination_ip
        ).order_by(func.count(SocEvent.id).desc()).limit(limit).all()
        
        data = [{'destination_ip': b[0], 'count': b[1]} for b in blocked]
        return jsonify({'success': True, 'data': data})
    finally:
        session.close()

@bp.route('/infected-hosts', methods=['GET'])
@login_required
def get_infected_hosts():
    """Top infected source IPs"""
    limit = int(request.args.get('limit', 10))
    
    session = Session()
    try:
        infected = session.query(
            SocEvent.source_ip,
            func.count(SocEvent.id).label('count')
        ).filter(SocEvent.severity.in_(['Critical', 'High'])).group_by(
            SocEvent.source_ip
        ).order_by(func.count(SocEvent.id).desc()).limit(limit).all()
        
        data = [{'source_ip': h[0], 'count': h[1]} for h in infected]
        return jsonify({'success': True, 'data': data})
    finally:
        session.close()

@bp.route('/stats', methods=['GET'])
@login_required
def get_soc_stats():
    """Summary statistics for SOC events"""
    session = Session()
    try:
        total_events = session.query(func.count(SocEvent.id)).scalar()
        critical_count = session.query(func.count(SocEvent.id)).filter_by(severity='Critical').scalar()
        high_count = session.query(func.count(SocEvent.id)).filter_by(severity='High').scalar()
        
        result = {
            'total_events': total_events,
            'critical': critical_count,
            'high': high_count
        }
        return jsonify({'success': True, 'data': result})
    finally:
        session.close()
