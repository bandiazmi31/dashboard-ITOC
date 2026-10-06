from flask import Blueprint, request, jsonify
from utils.auth_middleware import login_required
from utils.db import Session
from models import NetworkLink
from sqlalchemy import func, case, cast, Float

bp = Blueprint('links', __name__, url_prefix='/api/links')

def _serialize_link(link, availability):
    return {
        'id': str(link.id),
        'sensor_name': link.sensor_name,
        'device': link.device,
        'location': link.location,
        'isp': link.isp,
        'target_sla': float(link.target_sla) if link.target_sla else None,
        'up_time': link.up_time,
        'down_time': link.down_time,
        'availability': round(availability, 2) if availability is not None else None,
        'avg_traffic': float(link.avg_traffic) if link.avg_traffic else None,
        'volume': float(link.volume) if link.volume else None,
    }

@bp.route('/', methods=['GET'])
@login_required
def list_links():
    """List network links with optional sorting and pagination"""
    sort_by = request.args.get('sort_by', 'down_time')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    offset = (page - 1) * limit
    
    session = Session()
    try:
        # Calculate availability on the fly
        availability_expr = case(
            (NetworkLink.up_time + NetworkLink.down_time > 0,
             cast(NetworkLink.up_time, Float) / (NetworkLink.up_time + NetworkLink.down_time) * 100),
            else_=None
        )
        
        query = session.query(NetworkLink, availability_expr.label('availability'))
        
        if sort_by == 'down_time':
            query = query.order_by(NetworkLink.down_time.desc())
        elif sort_by == 'availability':
            query = query.order_by(availability_expr.desc().nullslast())
        elif sort_by == 'traffic':
            query = query.order_by(NetworkLink.volume.desc())
        else:
            query = query.order_by(NetworkLink.id)
        
        rows = query.offset(offset).limit(limit).all()
        data = [_serialize_link(row[0], row[1]) for row in rows]
        return jsonify({'success': True, 'data': data})
    finally:
        session.close()

@bp.route('/stats', methods=['GET'])
@login_required
def links_stats():
    """Aggregated statistics for all network links"""
    session = Session()
    try:
        total_links = session.query(func.count(NetworkLink.id)).scalar()
        # Average availability across all links
        availability_expr = case(
            (NetworkLink.up_time + NetworkLink.down_time > 0,
             cast(NetworkLink.up_time, Float) / (NetworkLink.up_time + NetworkLink.down_time) * 100),
            else_=None
        )
        avg_availability = session.query(func.avg(availability_expr)).scalar()
        total_traffic = session.query(func.sum(NetworkLink.volume)).scalar()
        
        result = {
            'total_links': total_links,
            'avg_availability': round(avg_availability or 0, 2),
            'total_traffic_tb': round((total_traffic or 0), 2)
        }
        return jsonify({'success': True, 'data': result})
    finally:
        session.close()
