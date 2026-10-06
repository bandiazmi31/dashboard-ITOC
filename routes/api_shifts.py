from flask import Blueprint, jsonify
from utils.auth_middleware import login_required
from datetime import datetime, timedelta

bp = Blueprint("shifts", __name__, url_prefix="/api/shifts")

@bp.route("/calendar", methods=["GET"])
@login_required
def get_shift_calendar():
    """Get 14-day shift rotation calendar"""
    patterns = ["Pagi", "Sore", "Malam", "Off"]
    teams = ["Team 1", "Team 2", "Team 3", "Team 4"]
    
    calendar = []
    today = datetime.now()
    
    for day in range(14):
        date = today + timedelta(days=day)
        day_schedule = {"date": date.strftime("%Y-%m-%d")}
        for idx, team in enumerate(teams):
            # Calculate rotation per team
            shift_idx = (day + idx) % 4
            day_schedule[team] = patterns[shift_idx]
        calendar.append(day_schedule)
        
    return jsonify({"success": True, "data": calendar})
