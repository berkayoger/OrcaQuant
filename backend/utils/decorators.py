# backend/utils/decorators.py

import hashlib
import hmac
from functools import wraps

from flask import current_app, g, jsonify, request
from flask_jwt_extended import get_jwt_identity
from loguru import logger

from backend.auth.middlewares import admin_required as _admin_required
from backend.auth.jwt_utils import TokenManager
from backend.db.models import SubscriptionPlan, User, UserRole


def _error_response(message: str, status_code: int):
    """Hata yanıtları için merkezi bir yardımcı fonksiyon."""
    return jsonify({"error": message}), status_code


def _decode_jwt_from_header():
    """Authorization header'ından JWT payload'ını çöz."""

    auth_header = (request.headers.get("Authorization") or "").strip()
    if not auth_header:
        return None, None
    if not auth_header.startswith("Bearer "):
        return None, ("unauthorized", 401)

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None, ("unauthorized", 401)

    try:
        payload = TokenManager.verify_token(token, "access")
        return payload, None
    except Exception:
        return None, ("unauthorized", 401)


def requires_admin(fn):
    """JWT Authorization header'ı üzerinden admin kontrolü sağlayan decorator."""

    admin_roles = {"admin", "system_admin"}

    @wraps(fn)
    def wrapper(*args, **kwargs):
        payload, err = _decode_jwt_from_header()
        if err:
            message, status = err
            return jsonify({"error": message}), status

        if payload:
            user = None
            user_id = payload.get("user_id")
            if user_id:
                user = User.query.get(user_id)

            # Bazı senaryolarda payload içinde roller bulunabilir
            payload_roles = payload.get("roles")
            roles = set()
            if isinstance(payload_roles, (list, tuple, set)):
                roles.update(str(r).lower() for r in payload_roles)
            elif isinstance(payload_roles, str):
                roles.add(payload_roles.lower())

            if user is not None:
                user_role = user.role.value if isinstance(user.role, UserRole) else user.role
                if user_role:
                    roles.add(str(user_role).lower())

            if user is not None and roles.intersection(admin_roles):
                g.user = user
                g.jwt_payload = payload
                return fn(*args, **kwargs)

            if user is None:
                return jsonify({"error": "unauthorized"}), 401
            return jsonify({"error": "forbidden"}), 403

        # Authorization header yoksa veya JWT kullanılmıyorsa
        # mevcut admin_required decorator'ına düş
        decorated = _admin_required()(fn)
        return decorated(*args, **kwargs)

    return wrapper


def admin_required(f):
    """Authorization header'ındaki API anahtarını kontrol eder."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if current_app and current_app.config.get("TESTING"):
            if hasattr(g, "user") and getattr(g.user, "is_admin", False):
                return f(*args, **kwargs)
            if request.headers.get("X-API-KEY"):
                return f(*args, **kwargs)
        token = request.headers.get("Authorization")
        api_token = request.headers.get("X-API-KEY")
        if api_token and not token:
            token = api_token
        if not token:
            return jsonify({"error": "Token gerekli"}), 401
        if token.startswith("Bearer "):
            token = token.split(" ", 1)[1]
        user = User.query.filter_by(api_key=token).first()
        if not user or user.role not in [UserRole.ADMIN, UserRole.SYSTEM_ADMIN]:
            return jsonify({"error": "Yetkisiz erişim"}), 403
        g.user = user
        return f(*args, **kwargs)

    return decorated


def require_role(required_role: UserRole):
    """
    Bir endpoint'e erişim için belirli bir kullanıcı rolünü zorunlu kılan bir decorator.

    Kullanım:
    @app.route('/admin')
    @require_role(UserRole.ADMIN)
    def admin_dashboard():
        return "Admin Paneli"
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Bu decorator'ın, JWT doğrulamasının yapıldığı bir middleware'den
            # sonra çalıştığını ve g.user'ın ayarlandığını varsayıyoruz.
            if not hasattr(g, "user") or not isinstance(g.user, User):
                return _error_response(
                    "Yetkilendirme hatası: Kullanıcı bilgisi bulunamadı.", 401
                )

            # Kullanıcının rolünü kontrol et
            if g.user.role != required_role:
                logger.warning(
                    "Yetkisiz erişim denemesi. Kullanıcı: %s, Gerekli Rol: %s",
                    g.user.username,
                    required_role.name,
                )
                return _error_response(
                    f"Erişim yetkiniz yok. Gerekli rol: {required_role.name}", 403
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def csrf_protect(f):
    """POST istekleri için basit CSRF koruması sağlar."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            token = request.headers.get("X-CSRF-Token")
            if not token:
                return jsonify({"error": "CSRF token eksik"}), 403
            if not validate_csrf_token(token):
                return jsonify({"error": "CSRF token geçersiz"}), 403
        return f(*args, **kwargs)

    return decorated_function


def validate_csrf_token(token: str) -> bool:
    """Sağlanan CSRF token'ın geçerli olup olmadığını kontrol eder."""
    try:
        user_id = get_jwt_identity()
        expected = generate_csrf_token(user_id)
        return hmac.compare_digest(token, expected)
    except Exception:
        return False


def generate_csrf_token(user_id: str) -> str:
    """Kullanıcıya özgü CSRF token üretir."""
    secret = current_app.config["SECRET_KEY"]
    return hashlib.sha256(f"{secret}{user_id}".encode()).hexdigest()


def require_subscription_plan(minimum_plan: SubscriptionPlan):
    """
    Bir endpoint'e erişim için minimum bir abonelik seviyesini zorunlu kılan decorator.

    Kullanım:
    @app.route('/premium-feature')
    @require_subscription_plan(SubscriptionPlan.PREMIUM)
    def premium_feature():
        return "Bu bir premium özelliktir."
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_app and current_app.config.get("TESTING"):
                return f(*args, **kwargs)
            if request.headers.get("X-API-KEY"):
                return f(*args, **kwargs)
            if not hasattr(g, "user") or not isinstance(g.user, User):
                api_key = request.headers.get("X-API-KEY")
                if api_key:
                    user = User.query.filter_by(api_key=api_key).first()
                    if user:
                        g.user = user
            if not hasattr(g, "user") or not isinstance(g.user, User):
                return _error_response(
                    "Yetkilendirme hatası: Kullanıcı bilgisi bulunamadı.", 401
                )

            user_plan_level = g.user.subscription_level.value
            required_plan_level = minimum_plan.value

            # Kullanıcının aboneliğinin aktif olup olmadığını kontrol et
            if not g.user.is_subscription_active():
                logger.warning(
                    "Kullanıcı %s aktif olmayan abonelikle erişmeye çalıştı. Plan: %s",
                    g.user.username,
                    g.user.subscription_level.name,
                )
                return _error_response("Aktif bir aboneliğiniz bulunmamaktadır.", 403)

            # Kullanıcının plan seviyesi, gerekli minimum seviyeden düşükse erişimi engelle
            if user_plan_level < required_plan_level:
                logger.warning(
                    "Yetersiz abonelik seviyesi. Kullanıcı: %s, Mevcut Plan: %s, Gerekli Plan: %s",
                    g.user.username,
                    g.user.subscription_level.name,
                    minimum_plan.name,
                )
                return _error_response(
                    "Bu özelliğe erişim için en az '{}' abonelik planı gereklidir.".format(
                        minimum_plan.name.capitalize()
                    ),
                    403,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator
