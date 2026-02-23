from __future__ import annotations

import secrets
from functools import wraps

from flask import abort, jsonify, redirect, request, session, url_for


def is_logged_in() -> bool:
    return bool(session.get("user_id"))


def current_user_data() -> dict | None:
    if not session.get("user_id"):
        return None
    return {
        "id": session.get("user_id"),
        "name": session.get("user_name"),
        "email": session.get("user_email"),
        "is_admin": bool(session.get("is_admin")),
    }


def get_or_create_csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def csrf_protect():
    unsafe = {"POST", "PUT", "PATCH", "DELETE"}
    if request.method not in unsafe or request.path.startswith("/static/"):
        return None

    expected = session.get("csrf_token")
    provided = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    if not expected or not provided or not secrets.compare_digest(expected, provided):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Token CSRF invalide."}), 400
        abort(400, description="Token CSRF invalide.")
    return None


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            if request.path.startswith("/api/"):
                return jsonify({"error": "Connexion requise."}), 401
            return redirect(url_for("user.auth_page", tab="login", next=request.path))
        return view(*args, **kwargs)

    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            if request.path.startswith("/api/"):
                return jsonify({"error": "Connexion requise."}), 401
            return redirect(url_for("user.auth_page", tab="login", next=request.path))
        if not session.get("is_admin"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Acces admin requis."}), 403
            abort(403, description="Acces admin requis.")
        return view(*args, **kwargs)

    return wrapper
