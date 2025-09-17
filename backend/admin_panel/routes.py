# backend/admin_panel/routes.py

import json
import os
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, current_app, g, jsonify, request
from flask_jwt_extended import get_jwt_identity
from loguru import logger
from sqlalchemy import and_, func, or_, text

from backend.auth.middlewares import admin_required as _admin_required
from backend.core.redis_manager import redis_manager
from backend.db.models import (
    ABHData,
    AdminSettings,
    AuditEvent,
    DBHData,
    PromoCode,
    PromotionCode,
    RateLimitHit,
    SubscriptionPlan,
    SubscriptionPlanModel,
    UsageLog,
    User,
    UserRole,
    db,
)
from backend.utils.audit import log_action
from backend.utils.decorators import requires_admin
from backend.utils.rbac import require_permission

from . import admin_bp

admin_console_bp = Blueprint("admin_console", __name__, url_prefix="/api/admin/console")


def admin_required(f):
    return _admin_required()(f)


# Kullanıcı Yönetimi
# Tüm kullanıcıları listeleme endpoint'i
@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    with current_app.app_context():
        users = User.query.all()
        user_list = [
            {
                "id": user.id,
                "username": user.username,
                "subscription_level": user.subscription_level.value,
                "role": user.role.value,
                "api_key": user.api_key,  # Üretimde doğrudan API key'i döndürmeyin!
                "is_active_subscriber": user.is_subscription_active(),
                "subscription_end": (
                    user.subscription_end.isoformat() if user.subscription_end else None
                ),
                "created_at": user.created_at.isoformat(),
                "custom_features": user.custom_features or "{}",
            }
            for user in users
        ]
        return jsonify(user_list), 200


@admin_bp.route("/users/<int:user_id>/custom-features", methods=["GET"])
@admin_required
def get_custom_features(user_id):
    """Belirli bir kullanıcının özel özelliklerini döndürür."""
    with current_app.app_context():
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Kullanıcı bulunamadı"}), 404

        try:
            custom_data = (
                json.loads(user.custom_features)
                if isinstance(user.custom_features, str)
                else user.custom_features or {}
            )
            db.session.commit()
            return jsonify({"custom_features": custom_data}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500


@admin_bp.route("/users/<int:user_id>/custom-features", methods=["POST"])
@admin_required
def update_custom_features(user_id):
    data = request.get_json()
    if not data or "custom_features" not in data:
        return jsonify({"error": "Eksik veri"}), 400

    try:
        parsed = json.loads(data["custom_features"])
    except json.JSONDecodeError:
        return jsonify({"error": "Geçersiz JSON"}), 400

    with current_app.app_context():
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Kullanıcı bulunamadı"}), 404

        user.custom_features = json.dumps(parsed)
        db.session.commit()

    return jsonify({"message": "Özel özellikler güncellendi."}), 200


# Kullanıcı detaylarını ve abonelik/rol güncelleme
@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user_details(user_id):
    data = request.get_json()
    new_level_str = data.get("subscription_level")
    new_role_str = data.get("role")

    with current_app.app_context():
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Kullanıcı bulunamadı."}), 404

        if new_level_str:
            try:
                selected_plan = SubscriptionPlan[new_level_str.upper()]
                user.subscription_level = selected_plan
                # Plan güncellendiğinde abonelik başlangıç/bitiş tarihlerini de yönetebilirsiniz
                # Ödeme entegrasyonu yoksa, manuel olarak bir süre belirleyebilirsiniz.
                if selected_plan not in [
                    SubscriptionPlan.TRIAL,
                    SubscriptionPlan.BASIC,
                ]:  # Trial ve Basic için süre uzatılmaz
                    user.subscription_start = datetime.utcnow()
                    user.subscription_end = datetime.utcnow() + timedelta(
                        days=30
                    )  # Örn: 30 günlük standart
                elif selected_plan == SubscriptionPlan.TRIAL:
                    user.subscription_start = (
                        datetime.utcnow()
                    )  # Deneme yeniden başlar gibi
                    user.subscription_end = datetime.utcnow() + timedelta(
                        days=7
                    )  # Yeni deneme süresi
                # Eğer Basic'e çekilirse subscription_end'i null yapabiliriz
                # veya mevcut süreyi koruyabiliriz.
                # user.subscription_end = None  # Eğer Basic'e çekiliyorsa süresiz yapma
            except KeyError:
                return jsonify({"error": "Geçersiz abonelik seviyesi."}), 400

        if new_role_str:
            try:
                user.role = UserRole[new_role_str.upper()]
            except KeyError:
                return jsonify({"error": "Geçersiz kullanıcı rolü."}), 400

        db.session.commit()
        logger.info(f"Kullanıcı {user.username} detayları güncellendi.")
        admin_id = get_jwt_identity()
        admin_user = User.query.get(admin_id) if admin_id else None
        log_action(
            admin_user,
            action="plan_update",
            details=f"Kullanıcı {user.username}, yeni plan: {user.subscription_level.value}",
        )
        return (
            jsonify(
                {
                    "message": "Kullanıcı başarıyla güncellendi.",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "subscription_level": user.subscription_level.value,
                        "role": user.role.value,
                        "is_active_subscriber": user.is_subscription_active(),
                        "subscription_end": (
                            user.subscription_end.isoformat()
                            if user.subscription_end
                            else None
                        ),
                    },
                }
            ),
            200,
        )


# İçerik ve Konfigürasyon Yönetimi


# Yeni coin ekleme endpoint'i (şimdilik basit bir simülasyon)
@admin_bp.route("/coins", methods=["POST"])
@admin_required
def add_coin():
    data = request.get_json()
    coin_id = data.get("id")
    coin_name = data.get("name")
    coin_symbol = data.get("symbol")

    if not all([coin_id, coin_name, coin_symbol]):
        return jsonify({"error": "Coin ID, ad ve sembol gerekli."}), 400

    # Gerçek implementasyonda, burada yeni coini veritabanına kaydedebilir
    # (yeni bir Coin modeli olabilir) ve backend'in veri toplama sürecini
    # bu yeni coin için başlatabilirsiniz.
    logger.info(f"Yeni coin ekleme talebi: {coin_name} ({coin_id})")
    return jsonify(
        {"message": f"Coin '{coin_name}' başarıyla eklendi (Simüle edildi)."}
    )


# Web sitesi arka planını alma/güncelleme
@admin_bp.route("/website_settings/background", methods=["GET", "POST"])
@admin_required
def manage_website_background():
    with current_app.app_context():
        if request.method == "GET":
            setting = AdminSettings.query.filter_by(
                setting_key="homepage_background_url"
            ).first()
            url = (
                setting.setting_value
                if setting
                else (
                    "https://www.coinkolik.com/wp-content/uploads/2023/12/"
                    "gunun-one-cikan-kripto-paralari-30-aralik-2023.jpg"
                )
            )  # Varsayılan URL
            return jsonify({"homepage_background_url": url}), 200
        elif request.method == "POST":
            data = request.get_json()
            new_url = data.get("url")
            if not new_url:
                return jsonify({"error": "URL eksik."}), 400

            setting = AdminSettings.query.filter_by(
                setting_key="homepage_background_url"
            ).first()
            if setting:
                setting.setting_value = new_url
            else:
                setting = AdminSettings(
                    setting_key="homepage_background_url", setting_value=new_url
                )
                db.session.add(setting)
            db.session.commit()
            logger.info(f"Anasayfa arka planı güncellendi: {new_url}")
            return (
                jsonify(
                    {"message": "Arka plan başarıyla güncellendi.", "new_url": new_url}
                ),
                200,
            )


# Abonelik fiyatlarını ve özelliklerini yönetme (GET ve POST)
@admin_bp.route("/subscription_plans", methods=["GET", "POST"])
@admin_required
def manage_subscription_plans():
    with current_app.app_context():
        if request.method == "GET":
            plans_config = {}
            for plan_enum in SubscriptionPlan:
                # Trial planı için statik veya dinamik değerler
                if plan_enum == SubscriptionPlan.TRIAL:
                    plans_config[plan_enum.value] = {
                        "price": "0.00",
                        "features": [
                            "7 Gün Ücretsiz Deneme",
                            "Temel Analiz Raporları",
                            "Popüler Coinlere Erişim",
                        ],
                        "limits": {
                            "analyze_calls_per_day": 5,
                            "llm_queries_per_day": 2,
                        },  # Örnek limitler
                    }
                    continue

                setting = AdminSettings.query.filter_by(
                    setting_key=f"plan_config_{plan_enum.value}"
                ).first()
                if setting:
                    plans_config[plan_enum.value] = json.loads(setting.setting_value)
                else:  # Varsayılan değerler
                    plans_config[plan_enum.value] = {
                        "price": (
                            "9.99"
                            if plan_enum == SubscriptionPlan.BASIC
                            else (
                                "14.99"
                                if plan_enum == SubscriptionPlan.ADVANCED
                                else "19.99"
                            )
                        ),
                        "features": [
                            f"{plan_enum.value.capitalize()} Plan Özelliği 1",
                            f"{plan_enum.value.capitalize()} Plan Özelliği 2",
                        ],
                        "limits": {
                            "analyze_calls_per_day": (
                                10
                                if plan_enum == SubscriptionPlan.BASIC
                                else (
                                    50
                                    if plan_enum == SubscriptionPlan.ADVANCED
                                    else 9999
                                )
                            ),
                            "llm_queries_per_day": (
                                5
                                if plan_enum == SubscriptionPlan.BASIC
                                else (
                                    20
                                    if plan_enum == SubscriptionPlan.ADVANCED
                                    else 9999
                                )
                            ),
                        },
                    }
            return jsonify(plans_config), 200

        elif request.method == "POST":
            data = request.get_json()
            plan_id = data.get("plan_id")  # "basic", "advanced", "premium"
            price = data.get("price")
            features = data.get("features")  # Liste
            limits = data.get(
                "limits"
            )  # Dictionary (örn: {"analyze_calls_per_day": 10})

            if not all([plan_id, price, features, limits]):
                return (
                    jsonify({"error": "Plan ID, fiyat, özellikler ve limitler eksik."}),
                    400,
                )

            if plan_id.upper() not in SubscriptionPlan._member_map_:
                return jsonify({"error": "Geçersiz plan ID."}), 400

            if SubscriptionPlan[plan_id.upper()] == SubscriptionPlan.TRIAL:
                return (
                    jsonify({"error": "Deneme planı doğrudan düzenlenemez."}),
                    400,
                )  # Trial'ı admin değiştirmez

            plan_config_value = json.dumps(
                {"price": str(price), "features": features, "limits": limits}
            )

            setting = AdminSettings.query.filter_by(
                setting_key=f"plan_config_{plan_id}"
            ).first()
            if setting:
                setting.setting_value = plan_config_value
            else:
                setting = AdminSettings(
                    setting_key=f"plan_config_{plan_id}",
                    setting_value=plan_config_value,
                )
                db.session.add(setting)
            db.session.commit()
            logger.info(f"Abonelik planı {plan_id} güncellendi.")
            return jsonify({"message": f"Plan {plan_id} başarıyla güncellendi."}), 200


# Abonelik kodları yönetimi
@admin_bp.route("/promo_codes", methods=["GET"])
@admin_required
def list_promo_codes():
    with current_app.app_context():
        codes = PromoCode.query.all()
        code_list = [
            {
                "id": code.id,
                "code": code.code,
                "plan": code.plan.value,
                "duration_days": code.duration_days,
                "max_uses": code.max_uses,
                "current_uses": code.current_uses,
                "is_active": code.is_active,
                "expires_at": code.expires_at.isoformat() if code.expires_at else None,
                "created_at": code.created_at.isoformat(),
            }
            for code in codes
        ]
        return jsonify(code_list), 200


@admin_bp.route("/promo_codes", methods=["POST"])
@admin_required
def generate_promo_code():
    data = request.get_json()
    plan_str = data.get("plan")
    duration_days = data.get(
        "duration_days"
    )  # Kodun sağladığı abonelik süresi (gün olarak)
    max_uses = data.get("max_uses", 1)
    expires_at_str = data.get("expires_at")  # Opsiyonel: Kodun bitiş tarihi

    if not all([plan_str, duration_days]):
        return jsonify({"error": "Plan ve süre bilgisi eksik."}), 400

    try:
        plan_enum = SubscriptionPlan[plan_str.upper()]
        code_value = str(uuid.uuid4())[:8].upper()  # Basit bir kod

        expires_at = None
        if expires_at_str:
            expires_at = datetime.fromisoformat(
                expires_at_str
            )  # ISO formatından datetime'a çevir
        else:  # Eğer son kullanma tarihi belirtilmezse, süresi duration_days'e göre hesapla
            expires_at = datetime.utcnow() + timedelta(days=duration_days)

        with current_app.app_context():
            new_code = PromoCode(
                code=code_value,
                plan=plan_enum,
                duration_days=duration_days,
                max_uses=max_uses,
                expires_at=expires_at,
            )
            db.session.add(new_code)
            db.session.commit()
            logger.info(
                f"Yeni promosyon kodu üretildi: {code_value} for plan {plan_str}."
            )
            return (
                jsonify(
                    {
                        "message": "Promosyon kodu başarıyla üretildi.",
                        "code": code_value,
                        "plan": plan_str,
                        "duration_days": duration_days,
                        "max_uses": max_uses,
                        "expires_at": expires_at.isoformat(),
                    }
                ),
                201,
            )
    except KeyError:
        return jsonify({"error": "Geçersiz plan adı."}), 400
    except Exception as e:
        logger.error(f"Promosyon kodu üretme hatası: {e}")
        return (
            jsonify({"error": f"Promosyon kodu üretilirken hata oluştu: {str(e)}"}),
            500,
        )


# Promosyon kodunu kullanma endpoint'i (Kullanıcı tarafı API'de de olabilir)
@admin_bp.route("/promo_codes/apply", methods=["POST"])
def apply_promo_code():
    api_key = request.headers.get("X-API-KEY")  # Kullanıcının API anahtarı
    data = request.get_json()
    promo_code = data.get("code")

    if not all([api_key, promo_code]):
        return jsonify({"error": "API anahtarı ve promosyon kodu gerekli."}), 400

    with current_app.app_context():
        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return jsonify({"error": "Geçersiz API anahtarı."}), 401

        code = PromoCode.query.filter_by(code=promo_code, is_active=True).first()

        if not code:
            return (
                jsonify({"error": "Geçersiz veya aktif olmayan promosyon kodu."}),
                400,
            )

        if code.expires_at and datetime.utcnow() > code.expires_at:
            code.is_active = False  # Süresi dolmuşsa pasif yap
            db.session.commit()
            return jsonify({"error": "Promosyon kodunun süresi dolmuş."}), 400

        if code.current_uses >= code.max_uses:
            code.is_active = False  # Kullanım limiti dolmuşsa pasif yap
            db.session.commit()
            return jsonify({"error": "Promosyon kodunun kullanım limiti dolmuş."}), 400

        # Kodu uygula: Kullanıcının abonelik seviyesini ve bitiş tarihini güncelle
        user.subscription_level = code.plan
        user.subscription_start = datetime.utcnow()
        user.subscription_end = datetime.utcnow() + timedelta(days=code.duration_days)
        code.current_uses += 1  # Kullanım sayısını artır

        # Eğer kodun tüm kullanımları bittiyse veya tek kullanımlıksa pasif yap
        if code.current_uses >= code.max_uses:
            code.is_active = False

        db.session.commit()
        # Loguru, {} yer tutucu ile formatlar (veya f-string kullanın)
        logger.info(
            "Promosyon kodu '{}' kullanıcı {} için uygulandı. Yeni plan: {}.",
            promo_code,
            user.username,
            user.subscription_level.value,
        )
        return (
            jsonify(
                {
                    "message": (
                        "Promosyon kodu başarıyla uygulandı. Yeni planınız: "
                        f"{user.subscription_level.value.upper()}."
                    ),
                    "new_plan": user.subscription_level.value,
                }
            ),
            200,
        )


# ── Abonelik Planları CRUD ─────────────────────────────────────────────


@admin_bp.route("/plans", methods=["GET", "POST"])
@admin_required
def plans():
    with current_app.app_context():
        if request.method == "GET":
            plans = SubscriptionPlanModel.query.all()
            return (
                jsonify(
                    [
                        {
                            "id": p.id,
                            "name": p.name,
                            "duration": p.duration_days,
                            "price": p.price,
                            "description": p.description,
                            "active": p.is_active,
                        }
                        for p in plans
                    ]
                ),
                200,
            )

        data = request.get_json() or {}
        name = data.get("name")
        duration = data.get("duration")
        price = data.get("price")
        description = data.get("description", "")
        is_active = bool(data.get("active", True))
        if not all([name, duration, price]):
            return jsonify({"error": "Plan adı, süre ve fiyat gerekli."}), 400
        if SubscriptionPlanModel.query.filter_by(name=name).first():
            return jsonify({"error": "Bu isimde bir plan zaten var."}), 400
        plan = SubscriptionPlanModel(
            name=name,
            duration_days=int(duration),
            price=float(price),
            description=description,
            is_active=is_active,
        )
        db.session.add(plan)
        db.session.commit()
        return jsonify({"id": plan.id}), 201


@admin_bp.route("/plans/<int:plan_id>", methods=["PATCH", "DELETE"])
@admin_required
def plan_detail(plan_id):
    with current_app.app_context():
        plan = SubscriptionPlanModel.query.get_or_404(plan_id)
        if request.method == "PATCH":
            data = request.get_json() or {}
            if "name" in data:
                if (
                    plan.name != data["name"]
                    and SubscriptionPlanModel.query.filter_by(name=data["name"]).first()
                ):
                    return jsonify({"error": "Bu isimde bir plan zaten var."}), 400
                if plan.name.upper() in ["TRIAL", "BASIC", "PREMIUM"]:
                    return jsonify({"error": "Bu plan değiştirilemez."}), 403
                plan.name = data["name"]
            if "duration" in data:
                plan.duration_days = int(data["duration"])
            if "price" in data:
                plan.price = float(data["price"])
            if "description" in data:
                plan.description = data["description"]
            if "is_active" in data or "active" in data:
                plan.is_active = bool(data.get("is_active", data.get("active")))
            db.session.commit()
            return jsonify({"message": "Plan güncellendi."}), 200

        # DELETE
        if plan.name.upper() in ["TRIAL", "BASIC", "PREMIUM"]:
            return jsonify({"error": "Bu plan silinemez."}), 403
        db.session.delete(plan)
        db.session.commit()
        return jsonify({"message": "Plan silindi."}), 200


@admin_bp.route("/plans/usage", methods=["GET"])
@admin_required
def plan_usage():
    with current_app.app_context():
        counts = (
            db.session.query(User.subscription_level, func.count(User.id))
            .group_by(User.subscription_level)
            .all()
        )
        return (
            jsonify(
                [{"plan": plan.name, "user_count": count} for plan, count in counts]
            ),
            200,
        )


@admin_bp.route("/limit-usage", methods=["GET"])
@admin_required
def limit_usage():
    with current_app.app_context():
        results = db.session.execute(
            text(
                """
                SELECT usage_log.user_id, users.username, usage_log.action, COUNT(*) AS count
                FROM usage_log
                JOIN users ON usage_log.user_id = users.id
                GROUP BY usage_log.user_id, users.username, usage_log.action
                ORDER BY count DESC
                LIMIT 100
                """
            )
        )
        stats = [dict(row) for row in results]
        return jsonify({"stats": stats}), 200


# ---------------------------------------------------------------------------
# Admin Console API (JWT protected endpoints under /api/admin/console)
# ---------------------------------------------------------------------------


def _ac_str(value, maxlen=200):
    if value is None:
        return None
    return str(value).strip()[:maxlen]


def _ac_int(value, default=None, minv=None, maxv=None):
    try:
        ivalue = int(value)
    except Exception:
        return default
    if minv is not None and ivalue < minv:
        return default
    if maxv is not None and ivalue > maxv:
        return default
    return ivalue


def _ac_bool(value, default=None):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    return default


def _ac_emit_audit(event_type, target_user_id=None, meta=None):
    admin_user = getattr(g, "user", None)
    try:
        event = AuditEvent(
            event_type=event_type,
            actor_user_id=getattr(admin_user, "id", None),
            target_user_id=target_user_id,
            ip=request.headers.get("X-Forwarded-For", request.remote_addr),
            user_agent=request.headers.get("User-Agent"),
            meta=meta or {},
        )
        db.session.add(event)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.warning("[admin-console] audit emit failed: %s", exc)


def _ac_plan_name(user: User) -> str:
    plan_attr = getattr(user, "subscription_level", None)
    if hasattr(plan_attr, "name"):
        return plan_attr.name.lower()
    if isinstance(plan_attr, str):
        return plan_attr.lower()
    return "trial"


def _ac_get_usage_for_user(user_id: int) -> int:
    try:
        start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return (
            UsageLog.query.filter(
                and_(UsageLog.user_id == user_id, UsageLog.timestamp >= start)
            ).count()
        )
    except Exception:
        return 0


def _ac_calc_thresholds(used, limit_value):
    if not limit_value or limit_value <= 0:
        return 0, None
    pct = int((used / float(limit_value)) * 100) if limit_value else 0
    if pct >= 100:
        return pct, "100"
    if pct >= 90:
        return pct, "90"
    if pct >= 75:
        return pct, "75"
    return pct, None


DEFAULT_LIMITS = {
    "trial": 100,
    "basic": 1000,
    "advanced": 5000,
    "premium": 20000,
}


@admin_console_bp.get("/users")
@requires_admin
def console_list_users():
    query = _ac_str(request.args.get("query"), 120)
    page = _ac_int(request.args.get("page"), default=1, minv=1)
    size = _ac_int(request.args.get("size"), default=20, minv=1, maxv=200)

    base_query = User.query
    if query:
        like = f"%{query}%"
        base_query = base_query.filter(
            or_(User.email.ilike(like), User.username.ilike(like))
        )

    items = base_query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=size, error_out=False
    )

    def _serialize(user: User) -> dict:
        plan = _ac_plan_name(user)
        created_at = getattr(user, "created_at", None)
        if created_at:
            created_str = created_at.isoformat()
        else:
            created_str = None
        return {
            "id": user.id,
            "email": getattr(user, "email", None),
            "name": getattr(user, "username", None),
            "role": (user.role.value if isinstance(user.role, UserRole) else str(user.role)),
            "plan": plan,
            "is_locked": not getattr(user, "is_active", True),
            "created_at": created_str,
        }

    return (
        jsonify(
            {
                "items": [_serialize(user) for user in items.items],
                "page": items.page,
                "pages": items.pages,
                "total": items.total,
            }
        ),
        200,
    )


@admin_console_bp.patch("/users/<int:user_id>/lock")
@requires_admin
def console_lock_user(user_id: int):
    payload = request.get_json(silent=True) or {}
    locked = _ac_bool(payload.get("locked"), None)
    if locked is None:
        return jsonify({"error": "locked must be boolean"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404

    try:
        user.is_active = not bool(locked)
        db.session.commit()
        _ac_emit_audit(
            "lock" if locked else "unlock",
            target_user_id=user.id,
            meta={"locked": bool(locked)},
        )
        return jsonify({"ok": True, "is_locked": bool(locked)}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "db_error", "detail": str(exc)}), 500


@admin_console_bp.delete("/users/<int:user_id>")
@requires_admin
def console_delete_user(user_id: int):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        _ac_emit_audit("user_delete", target_user_id=user_id)
        return jsonify({"ok": True}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "db_error", "detail": str(exc)}), 500


@admin_console_bp.patch("/users/<int:user_id>/role")
@requires_admin
def console_change_role(user_id: int):
    payload = request.get_json(silent=True) or {}
    role_value = (_ac_str(payload.get("role")) or "").upper()
    if role_value not in UserRole.__members__:
        return jsonify({"error": "invalid_role"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404

    try:
        user.role = UserRole[role_value]
        db.session.commit()
        _ac_emit_audit(
            "role_change",
            target_user_id=user.id,
            meta={
                "role": (
                    user.role.value
                    if isinstance(user.role, UserRole)
                    else role_value.lower()
                )
            },
        )
        return jsonify({"ok": True, "role": user.role.value}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "db_error", "detail": str(exc)}), 500


_PLAN_MAP = {
    "free": SubscriptionPlan.TRIAL,
    "trial": SubscriptionPlan.TRIAL,
    "basic": SubscriptionPlan.BASIC,
    "advanced": SubscriptionPlan.ADVANCED,
    "pro": SubscriptionPlan.ADVANCED,
    "premium": SubscriptionPlan.PREMIUM,
}


@admin_console_bp.patch("/users/<int:user_id>/plan")
@requires_admin
def console_change_plan(user_id: int):
    payload = request.get_json(silent=True) or {}
    plan_value = (_ac_str(payload.get("plan")) or "").lower()
    if plan_value not in _PLAN_MAP:
        return jsonify({"error": "invalid_plan"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404

    try:
        user.subscription_level = _PLAN_MAP[plan_value]
        db.session.commit()
        _ac_emit_audit(
            "plan_change",
            target_user_id=user.id,
            meta={"plan": user.subscription_level.name.lower()},
        )
        return jsonify({"ok": True, "plan": user.subscription_level.name.lower()}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "db_error", "detail": str(exc)}), 500


@admin_console_bp.get("/limits/status")
@requires_admin
def console_limit_status():
    user_id = _ac_int(request.args.get("user_id"), None, minv=1)
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404

    plan_name = _ac_plan_name(user)
    limit_value = DEFAULT_LIMITS.get(plan_name, DEFAULT_LIMITS["trial"])
    used = _ac_get_usage_for_user(user.id)
    pct, level = _ac_calc_thresholds(used, limit_value)
    return (
        jsonify(
            {
                "user_id": user.id,
                "plan": plan_name,
                "used": used,
                "limit": limit_value,
                "percent": pct,
                "alert_level": level,
            }
        ),
        200,
    )


@admin_console_bp.get("/limits/alerts")
@requires_admin
def console_limit_alerts():
    users = User.query.order_by(User.id.asc()).limit(1000).all()
    items = []
    for user in users:
        plan_name = _ac_plan_name(user)
        limit_value = DEFAULT_LIMITS.get(plan_name, DEFAULT_LIMITS["trial"])
        used = _ac_get_usage_for_user(user.id)
        pct, level = _ac_calc_thresholds(used, limit_value)
        if level:
            items.append(
                {
                    "user_id": user.id,
                    "email": getattr(user, "email", None),
                    "plan": plan_name,
                    "used": used,
                    "limit": limit_value,
                    "percent": pct,
                    "level": level,
                }
            )
    return jsonify({"items": items}), 200


def _ac_validate_promocode_payload(payload, partial=False):
    errors = []
    code_val = _ac_str(payload.get("code"))
    if not partial:
        if not code_val or len(code_val) < 3 or len(code_val) > 40:
            errors.append("code must be 3-40 characters long")
    discount = payload.get("discount_percent")
    if discount is not None:
        if _ac_int(discount, None, 0, 100) is None:
            errors.append("discount_percent must be between 0 and 100")
    bonus = payload.get("bonus_days")
    if bonus is not None:
        if _ac_int(bonus, None, 0, 3650) is None:
            errors.append("bonus_days must be 0..3650")
    max_uses = payload.get("max_uses")
    if max_uses is not None and _ac_int(max_uses, None, 1) is None:
        errors.append("max_uses must be >=1")
    active = payload.get("active")
    if active is not None and _ac_bool(active, None) is None:
        errors.append("active must be boolean")
    for key in ("valid_from", "valid_until"):
        if key in payload and payload.get(key):
            try:
                datetime.fromisoformat(str(payload[key]))
            except Exception:
                errors.append(f"{key} must be ISO8601 datetime")
    return errors


def _ac_promocode_to_dict(promo: PromotionCode) -> dict:
    return {
        "id": promo.id,
        "code": promo.code,
        "description": promo.description,
        "discount_percent": (
            int(promo.discount_amount)
            if promo.discount_type == "percent" and promo.discount_amount is not None
            else None
        ),
        "bonus_days": promo.active_days,
        "max_uses": promo.usage_limit,
        "used_count": promo.usage_count,
        "active": promo.is_active,
        "valid_from": promo.valid_from.isoformat() if promo.valid_from else None,
        "valid_until": promo.valid_until.isoformat() if promo.valid_until else None,
    }


@admin_console_bp.post("/promo-codes")
@requires_admin
def console_create_promocode():
    payload = request.get_json(silent=True) or {}
    errors = _ac_validate_promocode_payload(payload, partial=False)
    if errors:
        return jsonify({"error": "validation", "details": errors}), 400

    code = _ac_str(payload.get("code"), 40)
    if not code:
        return jsonify({"error": "validation", "details": ["code required"]}), 400
    code = code.upper()

    if PromotionCode.query.filter(func.upper(PromotionCode.code) == code).first():
        return jsonify({"error": "code_exists"}), 409

    promo = PromotionCode(
        code=code,
        description=_ac_str(payload.get("description"), 200),
        promo_type=payload.get("promo_type", "generic"),
        discount_type="percent"
        if payload.get("discount_percent") is not None
        else None,
        discount_amount=_ac_int(payload.get("discount_percent"), None, 0, 100),
        active_days=_ac_int(payload.get("bonus_days"), None, 0, 3650),
        usage_limit=_ac_int(payload.get("max_uses"), 1, 1),
        usage_count=0,
        is_active=_ac_bool(payload.get("active"), True),
    )

    valid_from = _ac_str(payload.get("valid_from"))
    valid_until = _ac_str(payload.get("valid_until"))
    try:
        if valid_from:
            promo.valid_from = datetime.fromisoformat(valid_from)
        if valid_until:
            promo.valid_until = datetime.fromisoformat(valid_until)
        db.session.add(promo)
        db.session.commit()
        _ac_emit_audit("promo_create", meta={"code": promo.code})
        return jsonify({"ok": True, "id": promo.id, "code": promo.code}), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "db_error", "detail": str(exc)}), 500


@admin_console_bp.get("/promo-codes")
@requires_admin
def console_list_promocodes():
    active_param = request.args.get("active")
    query = _ac_str(request.args.get("query"), 120)
    page = _ac_int(request.args.get("page"), default=1, minv=1)
    size = _ac_int(request.args.get("size"), default=20, minv=1, maxv=200)

    promo_query = PromotionCode.query
    if active_param is not None:
        active_val = _ac_bool(active_param, None)
        if active_val is None:
            return jsonify({"error": "active must be boolean"}), 400
        promo_query = promo_query.filter(PromotionCode.is_active == active_val)

    if query:
        like = f"%{query.upper()}%"
        promo_query = promo_query.filter(func.upper(PromotionCode.code).like(like))

    items = promo_query.order_by(PromotionCode.created_at.desc()).paginate(
        page=page, per_page=size, error_out=False
    )

    return (
        jsonify(
            {
                "items": [_ac_promocode_to_dict(promo) for promo in items.items],
                "page": items.page,
                "pages": items.pages,
                "total": items.total,
            }
        ),
        200,
    )


@admin_console_bp.patch("/promo-codes/<int:promo_id>")
@requires_admin
def console_update_promocode(promo_id: int):
    promo = PromotionCode.query.get(promo_id)
    if not promo:
        return jsonify({"error": "not_found"}), 404

    payload = request.get_json(silent=True) or {}
    errors = _ac_validate_promocode_payload(payload, partial=True)
    if errors:
        return jsonify({"error": "validation", "details": errors}), 400

    try:
        if "code" in payload:
            new_code = _ac_str(payload.get("code"), 40)
            if new_code:
                new_code = new_code.upper()
                existing = None
                if new_code != promo.code:
                    existing = (
                        PromotionCode.query.filter(
                            func.upper(PromotionCode.code) == new_code
                        ).first()
                    )
                if existing:
                    return jsonify({"error": "code_exists"}), 409
                promo.code = new_code
        if "description" in payload:
            promo.description = _ac_str(payload.get("description"), 200)
        if "discount_percent" in payload:
            promo.discount_type = (
                "percent" if payload.get("discount_percent") is not None else None
            )
            promo.discount_amount = _ac_int(payload.get("discount_percent"), None, 0, 100)
        if "bonus_days" in payload:
            promo.active_days = _ac_int(payload.get("bonus_days"), None, 0, 3650)
        if "max_uses" in payload:
            promo.usage_limit = _ac_int(payload.get("max_uses"), 1, 1)
        if "active" in payload:
            promo.is_active = _ac_bool(payload.get("active"), promo.is_active)
        if "valid_from" in payload:
            vf = _ac_str(payload.get("valid_from"))
            promo.valid_from = datetime.fromisoformat(vf) if vf else None
        if "valid_until" in payload:
            vu = _ac_str(payload.get("valid_until"))
            promo.valid_until = datetime.fromisoformat(vu) if vu else None
        db.session.commit()
        _ac_emit_audit("promo_update", meta={"id": promo_id})
        return jsonify({"ok": True}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "db_error", "detail": str(exc)}), 500


@admin_console_bp.post("/promo-codes/<int:promo_id>/activate")
@requires_admin
def console_activate_promocode(promo_id: int):
    payload = request.get_json(silent=True) or {}
    active_val = _ac_bool(payload.get("active"), None)
    if active_val is None:
        return jsonify({"error": "active must be boolean"}), 400

    promo = PromotionCode.query.get(promo_id)
    if not promo:
        return jsonify({"error": "not_found"}), 404

    try:
        promo.is_active = active_val
        db.session.commit()
        _ac_emit_audit("promo_activate", meta={"id": promo_id, "active": active_val})
        return jsonify({"ok": True, "active": active_val}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "db_error", "detail": str(exc)}), 500


@admin_console_bp.get("/health")
@requires_admin
def console_health():
    status = {"db": "unknown", "redis": "unknown", "celery": "unknown"}

    try:
        db.session.execute(text("SELECT 1"))
        status["db"] = "ok"
    except Exception:
        status["db"] = "fail"

    try:
        redis_client = getattr(redis_manager, "client", None)
        if redis_client and redis_client.ping():
            status["redis"] = "ok"
        else:
            status["redis"] = "unavailable"
    except Exception:
        status["redis"] = "unavailable"

    try:
        try:
            from backend.tasks import celery_app
        except Exception:
            from backend.celery_app import celery_app  # type: ignore

        if celery_app:
            insp = celery_app.control.inspect(timeout=1)
            active = insp.active() or {}
            status["celery"] = "ok" if isinstance(active, dict) else "fail"
        else:
            status["celery"] = "unavailable"
    except Exception:
        status["celery"] = "unavailable"

    return jsonify(status), 200


@admin_console_bp.get("/queue")
@requires_admin
def console_queue_state():
    response = {"active": 0, "reserved": 0, "scheduled": 0}
    try:
        try:
            from backend.tasks import celery_app
        except Exception:
            from backend.celery_app import celery_app  # type: ignore

        if celery_app:
            insp = celery_app.control.inspect(timeout=1)
            active = insp.active() or {}
            reserved = insp.reserved() or {}
            scheduled = insp.scheduled() or {}
            response["active"] = (
                sum(len(v) for v in active.values()) if isinstance(active, dict) else 0
            )
            response["reserved"] = (
                sum(len(v) for v in reserved.values())
                if isinstance(reserved, dict)
                else 0
            )
            response["scheduled"] = (
                sum(len(v) for v in scheduled.values())
                if isinstance(scheduled, dict)
                else 0
            )
        else:
            response["error"] = "unavailable"
    except Exception:
        response["error"] = "unavailable"

    return jsonify(response), 200


@admin_console_bp.get("/security/events")
@requires_admin
def console_security_events():
    event_type = _ac_str(request.args.get("type"))
    since_raw = _ac_str(request.args.get("since"))
    page = _ac_int(request.args.get("page"), default=1, minv=1)
    size = _ac_int(request.args.get("size"), default=50, minv=1, maxv=200)

    query = AuditEvent.query
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if since_raw:
        try:
            since_dt = datetime.fromisoformat(since_raw)
            query = query.filter(AuditEvent.occurred_at >= since_dt)
        except Exception:
            return jsonify({"error": "invalid_since"}), 400

    items = query.order_by(AuditEvent.occurred_at.desc()).paginate(
        page=page, per_page=size, error_out=False
    )

    results = []
    for event in items.items:
        results.append(
            {
                "id": event.id,
                "occurred_at": event.occurred_at.isoformat(),
                "event_type": event.event_type,
                "actor_user_id": event.actor_user_id,
                "target_user_id": event.target_user_id,
                "ip": event.ip,
                "user_agent": event.user_agent,
                "meta": event.meta,
            }
        )

    return (
        jsonify(
            {
                "items": results,
                "page": items.page,
                "pages": items.pages,
                "total": items.total,
            }
        ),
        200,
    )


@admin_console_bp.get("/security/ratelimit-hits")
@requires_admin
def console_security_rate_limits():
    days = _ac_int(request.args.get("days"), default=7, minv=1, maxv=90)
    since = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.session.query(
            func.date(RateLimitHit.occurred_at).label("day"),
            RateLimitHit.route,
            func.sum(RateLimitHit.count).label("hits"),
        )
        .filter(RateLimitHit.occurred_at >= since)
        .group_by(func.date(RateLimitHit.occurred_at), RateLimitHit.route)
        .order_by(func.date(RateLimitHit.occurred_at).desc())
        .all()
    )

    return (
        jsonify(
            {
                "items": [
                    {"day": str(row.day), "route": row.route, "hits": int(row.hits)}
                    for row in rows
                ],
                "since": since.isoformat(),
            }
        ),
        200,
    )
