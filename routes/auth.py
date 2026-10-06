import bcrypt
from flask import Blueprint, request, jsonify, session
from models import User
from utils.db import Session

bp = Blueprint("auth", __name__, url_prefix="/api")

def create_auth_routes():
    """Create and return auth routes"""
    bp = Blueprint("auth", __name__, url_prefix="/api")
    
    @bp.route("/login", methods=["POST"])
    def login():
        """Handle user login"""
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        
        if not username or not password:
            return jsonify({"success": False, "error": "Username and password required"}), 400
        
        session_db = Session()
        try:
            user = session_db.query(User).filter_by(username=username).first()
            
            if not user:
                return jsonify({"success": False, "error": "Invalid credentials"}), 401
            
            if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                return jsonify({"success": False, "error": "Invalid credentials"}), 401
            
            session["user_id"] = str(user.id)
            session["user_username"] = user.username
            session["user_name"] = user.name
            session["user_role"] = user.role
            session["user_unit"] = user.unit
            session["user_shift"] = user.group_shift or "-"
            
            return jsonify({
                "success": True,
                "data": {
                    "user": {
                        "id": str(user.id),
                        "name": user.name,
                        "username": user.username,
                        "role": user.role,
                        "unit": user.unit,
                        "group_shift": user.group_shift or "-"
                    }
                }
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            session_db.close()
    
    @bp.route("/logout", methods=["POST"])
    def logout():
        """Handle user logout"""
        session.clear()
        return jsonify({"success": True})
    
    @bp.route("/session", methods=["GET"])
    def check_session():
        """Check current session status"""
        if "user_id" not in session:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        
        return jsonify({
            "success": True,
            "data": {
                "user": {
                    "id": session["user_id"],
                    "name": session["user_name"],
                    "username": session["user_username"],
                    "role": session["user_role"],
                    "unit": session["user_unit"],
                    "group_shift": session["user_shift"]
                }
            }
        })
    
    return bp
