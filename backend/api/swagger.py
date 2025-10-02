"""OpenAPI 3.0 specification and Swagger UI integration."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Mapping

from flask import Flask, jsonify

try:  # pragma: no cover - imported lazily for optional dependency
    from flasgger import Swagger
except Exception:  # pragma: no cover - fallback when flasgger is missing
    Swagger = None  # type: ignore[misc]


def _default_openapi_template() -> Dict[str, Any]:
    """Return the static OpenAPI template used by the documentation."""

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "OrcaQuant Public API",
            "version": "1.0.0",
            "description": (
                "Programmatic access to OrcaQuant authentication, analytics, "
                "decision engine and payment capabilities. All public endpoints "
                "are exposed under the `/api/v1` prefix. Unless noted otherwise, "
                "requests are governed by the global rate limits configured for the "
                "deployment (defaults: 200/day; 50/hour)."
            ),
            "contact": {
                "name": "OrcaQuant Platform Team",
                "email": "api-support@orcaquant.example",
                "url": "https://github.com/orcaquant/orcaquant",
            },
            "license": {
                "name": "Apache 2.0",
                "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
            },
        },
        "servers": [
            {
                "url": "http://localhost:5000",
                "description": "Local development server",
            }
        ],
        "tags": [
            {
                "name": "Authentication",
                "description": "User registration, session management and token handling.",
            },
            {
                "name": "Decision Engine",
                "description": "Consensus scoring endpoints for OrcaQuant trading engines.",
            },
            {
                "name": "Admin Analytics",
                "description": "Administrative metrics that require elevated privileges.",
            },
            {
                "name": "Payments",
                "description": "Payment initiation and IyziCo callback lifecycle hooks.",
            },
        ],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": (
                        "JWT access token issued by `/api/v1/auth/login` or `/api/v1/auth/refresh`.\n"
                        "Include the token in the `Authorization: Bearer <token>` header."
                    ),
                }
            },
            "schemas": {
                "ErrorResponse": {
                    "type": "object",
                    "required": ["error"],
                    "properties": {
                        "error": {
                            "type": "string",
                            "description": "Machine readable error identifier.",
                        },
                        "message": {
                            "type": "string",
                            "description": "Human readable explanation of the error.",
                        },
                        "detail": {
                            "type": "string",
                            "description": "Optional contextual information for debugging.",
                        },
                    },
                },
                "RegisterRequest": {
                    "type": "object",
                    "required": ["username", "password"],
                    "properties": {
                        "username": {
                            "type": "string",
                            "minLength": 3,
                            "maxLength": 150,
                            "description": "Unique username for the account.",
                        },
                        "password": {
                            "type": "string",
                            "format": "password",
                            "minLength": 8,
                            "description": "User password. Must satisfy the password policy.",
                        },
                    },
                    "example": {"username": "quantfan", "password": "S3curePass!"},
                },
                "RegisterResponse": {
                    "type": "object",
                    "required": ["message", "username", "api_key", "subscription_level"],
                    "properties": {
                        "message": {"type": "string"},
                        "username": {"type": "string"},
                        "api_key": {
                            "type": "string",
                            "description": "API key provisioned for legacy integrations.",
                        },
                        "subscription_level": {
                            "type": "string",
                            "description": "Initial plan assigned to the account (FREE by default).",
                        },
                    },
                    "example": {
                        "message": "Kayıt başarılı.",
                        "username": "quantfan",
                        "api_key": "okp_1c0a1ce8852b4f779ec6",
                        "subscription_level": "FREE",
                    },
                },
                "LoginRequest": {
                    "type": "object",
                    "required": ["username", "password"],
                    "properties": {
                        "username": {"type": "string"},
                        "password": {"type": "string", "format": "password"},
                    },
                    "example": {"username": "quantfan", "password": "S3curePass!"},
                },
                "LoginResponse": {
                    "type": "object",
                    "required": ["message", "username", "api_key", "subscription_level"],
                    "properties": {
                        "message": {"type": "string"},
                        "username": {"type": "string"},
                        "api_key": {"type": "string"},
                        "subscription_level": {"type": "string"},
                        "access_token": {
                            "type": "string",
                            "description": "JWT access token returned for SPA clients.",
                        },
                        "refresh_token": {
                            "type": "string",
                            "description": "JWT refresh token returned for SPA clients.",
                        },
                        "subscription_end": {
                            "type": "string",
                            "format": "date-time",
                            "description": "ISO timestamp describing when the current subscription expires, if available.",
                        },
                    },
                    "example": {
                        "message": "Giriş başarılı.",
                        "username": "quantfan",
                        "api_key": "okp_1c0a1ce8852b4f779ec6",
                        "subscription_level": "ADVANCED",
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    },
                },
                "RefreshRequest": {
                    "type": "object",
                    "required": ["refresh_token"],
                    "properties": {
                        "refresh_token": {
                            "type": "string",
                            "description": "Valid refresh token obtained during login.",
                        }
                    },
                    "example": {
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    },
                },
                "RefreshResponse": {
                    "type": "object",
                    "required": ["access_token", "refresh_token"],
                    "properties": {
                        "access_token": {"type": "string"},
                        "refresh_token": {"type": "string"},
                        "message": {"type": "string"},
                    },
                    "example": {
                        "message": "Tokens refreshed successfully",
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    },
                },
                "LogoutResponse": {
                    "type": "object",
                    "required": ["message"],
                    "properties": {
                        "message": {"type": "string"},
                        "revoked_sessions": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "Number of refresh sessions revoked for the user.",
                        },
                    },
                    "example": {
                        "message": "Logout successful",
                        "revoked_sessions": 1,
                    },
                },
                "OhlcvCandle": {
                    "type": "object",
                    "required": ["ts", "open", "high", "low", "close", "volume"],
                    "properties": {
                        "ts": {
                            "type": "string",
                            "format": "date-time",
                            "description": "ISO timestamp of the candle (UTC).",
                        },
                        "open": {"type": "number"},
                        "high": {"type": "number"},
                        "low": {"type": "number"},
                        "close": {"type": "number"},
                        "volume": {"type": "number"},
                    },
                },
                "ScoreMultiRequest": {
                    "type": "object",
                    "required": ["symbol", "timeframe", "ohlcv"],
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Ticker symbol (e.g. BTCUSDT).",
                        },
                        "timeframe": {
                            "type": "string",
                            "description": "Bar timeframe identifier (e.g. 1h, 4h).",
                        },
                        "engines": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of engine identifiers to run. Defaults to all registered engines.",
                        },
                        "params": {
                            "type": "object",
                            "additionalProperties": {"type": "object"},
                            "description": "Per-engine tuning parameters keyed by engine id.",
                        },
                        "account_value": {
                            "type": "number",
                            "format": "float",
                            "description": "Optional account valuation used to contextualise risk scoring.",
                        },
                        "ohlcv": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/OhlcvCandle"},
                            "description": "Chronologically ordered OHLCV candles (minimum 50 records).",
                        },
                    },
                    "example": {
                        "symbol": "BTCUSDT",
                        "timeframe": "1h",
                        "engines": ["ema_cross", "momentum", "volatility"],
                        "params": {"ema_cross": {"fast": 12, "slow": 26}},
                        "account_value": 12500.0,
                        "ohlcv": [
                            {
                                "ts": "2024-04-01T00:00:00Z",
                                "open": 68000.0,
                                "high": 68500.0,
                                "low": 67850.0,
                                "close": 68250.0,
                                "volume": 152.4,
                            }
                        ],
                    },
                },
                "EngineDecision": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "number", "format": "float"},
                        "confidence": {"type": "number", "format": "float"},
                        "decision": {
                            "type": "string",
                            "description": "One of BUY, SELL, HOLD or NEUTRAL depending on engine logic.",
                        },
                    },
                },
                "ScoreMultiResponse": {
                    "type": "object",
                    "required": ["symbol", "timeframe", "decision", "score", "engines"],
                    "properties": {
                        "symbol": {"type": "string"},
                        "timeframe": {"type": "string"},
                        "decision": {"type": "string"},
                        "score": {"type": "number", "format": "float"},
                        "confidence": {
                            "type": "number",
                            "format": "float",
                            "description": "Aggregated confidence derived from the consensus engine.",
                        },
                        "engines": {
                            "type": "object",
                            "additionalProperties": {
                                "$ref": "#/components/schemas/EngineDecision"
                            },
                        },
                    },
                    "example": {
                        "symbol": "BTCUSDT",
                        "timeframe": "1h",
                        "decision": "BUY",
                        "score": 0.76,
                        "confidence": 0.68,
                        "engines": {
                            "ema_cross": {"score": 0.81, "confidence": 0.7, "decision": "BUY"},
                            "momentum": {"score": 0.73, "confidence": 0.6, "decision": "BUY"},
                        },
                    },
                },
                "AdminSummaryResponse": {
                    "type": "object",
                    "properties": {
                        "active_users": {"type": "integer"},
                        "new_signups": {"type": "integer"},
                        "successful_payments": {"type": "integer"},
                        "churned_users": {"type": "integer"},
                    },
                    "example": {
                        "active_users": 128,
                        "new_signups": 34,
                        "successful_payments": 22,
                        "churned_users": 3,
                    },
                },
                "AdminPlanDistribution": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["plan", "count"],
                        "properties": {
                            "plan": {"type": "string"},
                            "count": {"type": "integer"},
                        },
                    },
                    "example": [
                        {"plan": "FREE", "count": 540},
                        {"plan": "BASIC", "count": 180},
                        {"plan": "ADVANCED", "count": 96},
                    ],
                },
                "AdminUsageResponse": {
                    "type": "object",
                    "properties": {
                        "predictions": {"type": "integer"},
                        "system_events": {"type": "integer"},
                    },
                    "example": {"predictions": 4521, "system_events": 982},
                },
                "PaymentInitiateRequest": {
                    "type": "object",
                    "required": ["plan"],
                    "properties": {
                        "plan": {
                            "type": "string",
                            "description": "Desired subscription plan (e.g. BASIC, ADVANCED, PREMIUM).",
                        },
                        "promo_code": {
                            "type": "string",
                            "description": "Optional promotional code to apply at checkout.",
                        },
                    },
                    "example": {
                        "plan": "ADVANCED",
                        "promo_code": "BLACKFRIDAY",
                    },
                },
                "PaymentInitiateResponse": {
                    "type": "object",
                    "required": ["status", "payment_page_url"],
                    "properties": {
                        "status": {"type": "string"},
                        "payment_page_url": {
                            "type": "string",
                            "format": "uri",
                            "description": "Hosted payment page URL returned by IyziCo.",
                        },
                        "token": {
                            "type": "string",
                            "description": "IyziCo token identifier for the session.",
                        },
                    },
                    "example": {
                        "status": "success",
                        "payment_page_url": "https://sandbox-iyzico.example/checkout/form",
                        "token": "8bc4ac16-8f7d-4c87-94a8-7c5f9a37d4b2",
                    },
                },
                "PaymentCallbackForm": {
                    "type": "object",
                    "required": ["token", "conversationId"],
                    "properties": {
                        "token": {"type": "string"},
                        "conversationId": {"type": "string"},
                        "paymentId": {"type": "string"},
                        "status": {"type": "string"},
                    },
                    "example": {
                        "token": "8bc4ac16-8f7d-4c87-94a8-7c5f9a37d4b2",
                        "conversationId": "1f5e5a77-3fc1-4cf2-9c22-77e3b9e76d8f",
                    },
                },
            },
        },
        "paths": {
            "/api/v1/auth/register": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Yeni kullanıcı kaydı",
                    "operationId": "registerUser",
                    "description": (
                        "Registers a new user. Rate limit: 5 requests per minute per originating IP."
                    ),
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/RegisterRequest"},
                                "examples": {
                                    "default": {
                                        "summary": "Yeni kullanıcı",
                                        "value": {
                                            "username": "quantfan",
                                            "password": "S3curePass!",
                                        },
                                    }
                                },
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Registration completed",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/RegisterResponse"},
                                }
                            },
                        },
                        "400": {
                            "description": "Missing username or password",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "error": "validation_error",
                                        "message": "Kullanıcı adı ve şifre gerekli.",
                                    },
                                }
                            },
                        },
                        "409": {
                            "description": "Username already exists",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "error": "conflict",
                                        "message": "Kullanıcı adı zaten mevcut.",
                                    },
                                }
                            },
                        },
                        "500": {
                            "description": "Unexpected server error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                }
                            },
                        },
                    },
                    "security": [],
                    "x-rateLimit": {
                        "limit": "5",
                        "period": "minute",
                        "scope": "per IP",
                    },
                }
            },
            "/api/v1/auth/login": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Kullanıcı girişi",
                    "operationId": "loginUser",
                    "description": (
                        "Authenticates a user using username and password. Rate limit: 10 requests per minute per IP."
                    ),
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/LoginRequest"},
                                "examples": {
                                    "default": {
                                        "summary": "Giriş",
                                        "value": {
                                            "username": "quantfan",
                                            "password": "S3curePass!",
                                        },
                                    }
                                },
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Login successful",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/LoginResponse"},
                                }
                            },
                        },
                        "400": {
                            "description": "Validation error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "error": "validation_error",
                                        "message": "Kullanıcı adı ve şifre gerekli.",
                                    },
                                }
                            },
                        },
                        "401": {
                            "description": "Invalid credentials",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "error": "unauthorized",
                                        "message": "Geçersiz kullanıcı adı veya şifre.",
                                    },
                                }
                            },
                        },
                        "429": {
                            "description": "Too many attempts",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "error": "rate_limited",
                                        "message": "Too Many Requests",
                                    },
                                }
                            },
                        },
                    },
                    "security": [],
                    "x-rateLimit": {
                        "limit": "10",
                        "period": "minute",
                        "scope": "per IP",
                    },
                }
            },
            "/api/v1/auth/refresh": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Erişim belirteçlerini yenile",
                    "operationId": "refreshTokens",
                    "description": (
                        "Issues a new access/refresh token pair using a valid refresh token. "
                        "Send the refresh token in the request body for SPA clients or rely on the HTTP-only cookie for legacy clients."
                    ),
                    "requestBody": {
                        "required": False,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/RefreshRequest"},
                                "examples": {
                                    "default": {
                                        "summary": "Token yenile",
                                        "value": {
                                            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                                        },
                                    }
                                },
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Tokens refreshed",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/RefreshResponse"},
                                }
                            },
                        },
                        "401": {
                            "description": "Missing or invalid refresh token",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "error": "invalid_token",
                                        "message": "Invalid token",
                                    },
                                }
                            },
                        },
                    },
                    "security": [],
                    "x-rateLimit": {
                        "limit": "Global",
                        "period": "per user session",
                        "scope": "Refresh tokens can be rotated as needed; abuse is protected by session checks.",
                    },
                }
            },
            "/api/v1/auth/logout": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Aktif oturumu kapat",
                    "operationId": "logoutUser",
                    "description": (
                        "Revokes all active refresh sessions for the authenticated user and clears legacy cookies."
                    ),
                    "responses": {
                        "200": {
                            "description": "Logout succeeded",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/LogoutResponse"},
                                }
                            },
                        },
                        "401": {
                            "description": "Authentication required",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                }
                            },
                        },
                        "500": {
                            "description": "Failed to revoke sessions",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                }
                            },
                        },
                    },
                    "security": [{"BearerAuth": []}],
                    "x-rateLimit": {
                        "limit": "Global",
                        "period": "per request",
                        "scope": "Subject to default API limits.",
                    },
                }
            },
            "/api/v1/decision/score-multi": {
                "post": {
                    "tags": ["Decision Engine"],
                    "summary": "Çoklu motor konsensüs skoru",
                    "operationId": "scoreMulti",
                    "description": (
                        "Runs one or more decision engines and returns the consensus recommendation. "
                        "Requires a valid JWT access token and sufficient subscription plan limits."
                    ),
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ScoreMultiRequest"},
                                "examples": {
                                    "default": {
                                        "summary": "Konsensüs isteği",
                                        "value": {
                                            "symbol": "BTCUSDT",
                                            "timeframe": "1h",
                                            "engines": ["ema_cross", "momentum"],
                                            "ohlcv": [
                                                {
                                                    "ts": "2024-04-01T00:00:00Z",
                                                    "open": 68000.0,
                                                    "high": 68500.0,
                                                    "low": 67850.0,
                                                    "close": 68250.0,
                                                    "volume": 152.4,
                                                }
                                            ],
                                        },
                                    }
                                },
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Consensus generated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ScoreMultiResponse"},
                                }
                            },
                        },
                        "400": {
                            "description": "Validation error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "error": "validation_error",
                                        "message": "symbol ve timeframe zorunludur",
                                    },
                                }
                            },
                        },
                        "403": {
                            "description": "Feature disabled or plan restriction",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "error": "forbidden",
                                        "message": "Özellik şu anda devre dışı.",
                                    },
                                }
                            },
                        },
                        "429": {
                            "description": "Plan or rate limit exceeded",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "error": "rate_limited",
                                        "message": "Too Many Requests",
                                    },
                                }
                            },
                        },
                        "500": {
                            "description": "Unexpected error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                }
                            },
                        },
                    },
                    "security": [{"BearerAuth": []}],
                    "x-rateLimit": {
                        "limit": "Plan based",
                        "period": "per day",
                        "scope": "Enforced by subscription usage quotas and global API limits.",
                    },
                }
            },
            "/api/v1/admin/analytics/summary": {
                "get": {
                    "tags": ["Admin Analytics"],
                    "summary": "Tarih aralığına göre yönetim özeti",
                    "operationId": "adminAnalyticsSummary",
                    "description": (
                        "Returns key user and payment metrics for administrators. Requires an admin JWT token."
                    ),
                    "parameters": [
                        {
                            "name": "from",
                            "in": "query",
                            "required": False,
                            "description": "ISO formatted start timestamp (inclusive). Defaults to start of current day.",
                            "schema": {"type": "string", "format": "date-time"},
                            "example": "2024-03-01T00:00:00Z",
                        },
                        {
                            "name": "to",
                            "in": "query",
                            "required": False,
                            "description": "ISO formatted end timestamp (exclusive). Defaults to now.",
                            "schema": {"type": "string", "format": "date-time"},
                            "example": "2024-03-31T23:59:59Z",
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Aggregated statistics",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AdminSummaryResponse"},
                                }
                            },
                        },
                        "400": {
                            "description": "Invalid date range",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "error": "validation_error",
                                        "message": "invalid from",
                                    },
                                }
                            },
                        },
                        "401": {
                            "description": "Missing or invalid token",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                }
                            },
                        },
                        "403": {
                            "description": "Admin privileges required",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                }
                            },
                        },
                    },
                    "security": [{"BearerAuth": []}],
                    "x-rateLimit": {
                        "limit": "Global",
                        "period": "per admin token",
                        "scope": "Subject to default API limits and admin tooling safeguards.",
                    },
                }
            },
            "/api/v1/admin/analytics/plans": {
                "get": {
                    "tags": ["Admin Analytics"],
                    "summary": "Abonelik dağılımı",
                    "operationId": "adminAnalyticsPlans",
                    "description": "Returns the distribution of users per subscription plan.",
                    "responses": {
                        "200": {
                            "description": "Plan distribution",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AdminPlanDistribution"},
                                }
                            },
                        },
                        "401": {
                            "description": "Missing or invalid token",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                }
                            },
                        },
                        "403": {
                            "description": "Admin privileges required",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                }
                            },
                        },
                    },
                    "security": [{"BearerAuth": []}],
                    "x-rateLimit": {
                        "limit": "Global",
                        "period": "per admin token",
                        "scope": "Subject to default API limits and admin tooling safeguards.",
                    },
                }
            },
            "/api/v1/admin/analytics/usage": {
                "get": {
                    "tags": ["Admin Analytics"],
                    "summary": "Sistem kullanım istatistikleri",
                    "operationId": "adminAnalyticsUsage",
                    "description": "Provides aggregate counts of prediction opportunities and system events.",
                    "responses": {
                        "200": {
                            "description": "Usage metrics",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AdminUsageResponse"},
                                }
                            },
                        },
                        "401": {
                            "description": "Missing or invalid token",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                }
                            },
                        },
                        "403": {
                            "description": "Admin privileges required",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                }
                            },
                        },
                    },
                    "security": [{"BearerAuth": []}],
                    "x-rateLimit": {
                        "limit": "Global",
                        "period": "per admin token",
                        "scope": "Subject to default API limits and admin tooling safeguards.",
                    },
                }
            },
            "/api/v1/payment/initiate": {
                "post": {
                    "tags": ["Payments"],
                    "summary": "IyziCo ödeme başlat",
                    "operationId": "paymentInitiate",
                    "description": (
                        "Initialises an IyziCo hosted payment session for the authenticated user. Requires at least a trial plan."
                    ),
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PaymentInitiateRequest"},
                                "examples": {
                                    "default": {
                                        "summary": "Ödeme başlat",
                                        "value": {
                                            "plan": "ADVANCED",
                                            "promo_code": "BLACKFRIDAY",
                                        },
                                    }
                                },
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "IyziCo session created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/PaymentInitiateResponse"},
                                }
                            },
                        },
                        "400": {
                            "description": "Invalid plan or promo code",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "error": "validation_error",
                                        "message": "Geçersiz abonelik planı.",
                                    },
                                }
                            },
                        },
                        "403": {
                            "description": "Subscription plan requirement not met",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                }
                            },
                        },
                        "500": {
                            "description": "IyziCo integration failure",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                }
                            },
                        },
                    },
                    "security": [{"BearerAuth": []}],
                    "x-rateLimit": {
                        "limit": "Plan based",
                        "period": "per account",
                        "scope": "Enforced via subscription guards and default API limits.",
                    },
                }
            },
            "/api/v1/payment/callback": {
                "post": {
                    "tags": ["Payments"],
                    "summary": "IyziCo ödeme callback",
                    "operationId": "paymentCallback",
                    "description": (
                        "Endpoint called by IyziCo to confirm a payment. Validates the IyziCo signature, reconciles the basket "
                        "information and upgrades the subscription when successful."
                    ),
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {"$ref": "#/components/schemas/PaymentCallbackForm"},
                                "examples": {
                                    "success": {
                                        "summary": "IyziCo bildirimi",
                                        "value": {
                                            "token": "8bc4ac16-8f7d-4c87-94a8-7c5f9a37d4b2",
                                            "conversationId": "1f5e5a77-3fc1-4cf2-9c22-77e3b9e76d8f",
                                        },
                                    }
                                },
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "IyziCo acknowledged",
                            "content": {
                                "text/plain": {
                                    "schema": {"type": "string"},
                                    "example": "OK",
                                }
                            },
                        },
                        "400": {
                            "description": "Validation error",
                            "content": {
                                "text/plain": {
                                    "schema": {"type": "string"},
                                    "example": "ERROR",
                                }
                            },
                        },
                        "500": {
                            "description": "Internal processing failure",
                            "content": {
                                "text/plain": {
                                    "schema": {"type": "string"},
                                    "example": "ERROR: Internal server error",
                                }
                            },
                        },
                    },
                    "security": [],
                    "x-rateLimit": {
                        "limit": "60",
                        "period": "hour",
                        "scope": "Per IyziCo IP address (enforced via Flask-Limiter).",
                    },
                }
            },
        },
    }


def _build_postman_collection(spec: Mapping[str, Any]) -> Dict[str, Any]:
    """Convert the OpenAPI specification into a Postman v2.1 collection."""

    base_url_variable = "{{baseUrl}}"
    versioned_items: Dict[str, List[Dict[str, Any]]] = {}

    paths: Mapping[str, Any] = spec.get("paths", {})  # type: ignore[assignment]
    for path, operations in paths.items():
        if not isinstance(operations, Mapping):
            continue
        for method, operation in operations.items():
            if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            op: Mapping[str, Any] = operation if isinstance(operation, Mapping) else {}
            tags: Iterable[str] = op.get("tags", ["General"])  # type: ignore[assignment]
            name = op.get("summary") or f"{method.upper()} {path}"
            description = op.get("description", "")
            raw_url = f"{base_url_variable}{path}"
            segments = [
                segment.replace("{", "{{").replace("}", "}}")
                for segment in path.strip("/").split("/")
                if segment
            ]

            request: Dict[str, Any] = {
                "method": method.upper(),
                "header": [],
                "url": {
                    "raw": raw_url,
                    "host": [base_url_variable],
                    "path": segments,
                },
                "description": description,
            }

            parameters = op.get("parameters") or []
            query_params: List[Dict[str, Any]] = []
            if isinstance(parameters, Iterable):
                for parameter in parameters:
                    if not isinstance(parameter, Mapping):
                        continue
                    if parameter.get("in") != "query":
                        continue
                    query_params.append(
                        {
                            "key": parameter.get("name"),
                            "value": parameter.get("example")
                            or parameter.get("schema", {}).get("example"),
                            "description": parameter.get("description", ""),
                            "disabled": not parameter.get("required", False),
                        }
                    )
            if query_params:
                request["url"]["query"] = query_params

            content = (
                op.get("requestBody", {})
                if isinstance(op.get("requestBody"), Mapping)
                else {}
            )
            content_types: Mapping[str, Any] = (
                content.get("content", {}) if isinstance(content.get("content"), Mapping) else {}
            )
            if "application/json" in content_types:
                json_content = content_types["application/json"]
                examples = json_content.get("examples", {}) if isinstance(json_content, Mapping) else {}
                example_value = None
                if isinstance(examples, Mapping) and examples:
                    first_example = next(iter(examples.values()))
                    if isinstance(first_example, Mapping):
                        example_value = first_example.get("value")
                if example_value is None and isinstance(json_content, Mapping):
                    example_value = json_content.get("example")
                if example_value is not None:
                    request["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(example_value, indent=2, ensure_ascii=False),
                        "options": {"raw": {"language": "json"}},
                    }
                    request["header"].append({
                        "key": "Content-Type",
                        "value": "application/json",
                    })
            elif "application/x-www-form-urlencoded" in content_types:
                form_content = content_types["application/x-www-form-urlencoded"]
                example_value = None
                if isinstance(form_content, Mapping):
                    examples = form_content.get("examples", {})
                    if isinstance(examples, Mapping) and examples:
                        first_example = next(iter(examples.values()))
                        if isinstance(first_example, Mapping):
                            example_value = first_example.get("value")
                if isinstance(example_value, Mapping):
                    request["body"] = {
                        "mode": "urlencoded",
                        "urlencoded": [
                            {"key": key, "value": str(value)}
                            for key, value in example_value.items()
                        ],
                    }

            security = op.get("security") or []
            if security:
                for requirement in security:
                    if not isinstance(requirement, Mapping):
                        continue
                    if "BearerAuth" in requirement:
                        request["auth"] = {
                            "type": "bearer",
                            "bearer": [
                                {
                                    "key": "token",
                                    "value": "{{bearerToken}}",
                                    "type": "string",
                                }
                            ],
                        }
                        break

            for tag in tags:
                versioned_items.setdefault(tag, []).append(
                    {
                        "name": name,
                        "request": request,
                    }
                )

    folder_items = [
        {"name": tag, "item": items}
        for tag, items in sorted(versioned_items.items(), key=lambda kv: kv[0])
    ]

    return {
        "info": {
            "name": "OrcaQuant API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": (
                "Imported from the OrcaQuant OpenAPI specification. Configure the `baseUrl` "
                "and `bearerToken` variables to match your environment."
            ),
            "version": spec.get("info", {}).get("version", "1.0.0"),
        },
        "item": folder_items,
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:5000"},
            {"key": "bearerToken", "value": ""},
        ],
    }


def init_swagger(app: Flask) -> Any:
    """Initialise Flasgger Swagger UI and OpenAPI JSON export."""

    if Swagger is None:  # pragma: no cover - defensive guard
        app.logger.warning("Flasgger is not installed; Swagger UI is disabled.")
        return None

    template = deepcopy(_default_openapi_template())
    template["info"]["version"] = app.config.get(
        "API_VERSION", template["info"].get("version", "1.0.0")
    )
    template["servers"][0]["url"] = app.config.get(
        "SWAGGER_SERVER_URL", template["servers"][0]["url"]
    )

    app.config.setdefault(
        "SWAGGER",
        {
            "title": template["info"]["title"],
            "openapi": "3.0.3",
            "uiversion": 3,
            "specs": [
                {
                    "endpoint": "openapi",
                    "route": "/api/docs/openapi.json",
                    "rule_filter": lambda _rule: False,
                    "model_filter": lambda _tag: True,
                }
            ],
            "specs_route": "/api/docs",
        },
    )

    swagger = Swagger(app, template=template)
    app.config["OPENAPI_SPEC"] = template

    @app.get("/api/docs/postman.json")
    def export_postman_collection() -> Any:  # pragma: no cover - simple serialization
        spec = app.config.get("OPENAPI_SPEC", template)
        return jsonify(_build_postman_collection(spec))

    return swagger


__all__ = ["init_swagger"]

