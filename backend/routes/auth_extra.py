from flask import Blueprint, jsonify, session
import secrets

bp_auth_extra = Blueprint("auth_extra", __name__)

@bp_auth_extra.route("/auth/csrf-token", methods=["GET"])
def csrf_token():
    """CSRF token endpoint - optional security enhancement"""
    if not hasattr(session, 'csrf_token'):
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    else:
        token = session.get("csrf_token")
    
    return jsonify({
        "csrf_token": token,
        "status": "success"
    })

@bp_auth_extra.route("/auth/status", methods=["GET"])
def auth_status():
    """Auth status check endpoint"""
    return jsonify({
        "authenticated": bool(session.get('user_id')),
        "user": session.get('user_info') if session.get('user_id') else None
    })
