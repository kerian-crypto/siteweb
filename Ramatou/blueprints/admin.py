from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request

from extensions import db
from models import Order, Product, SupportMessage, SupportThread, User
from security import admin_required, current_user_data
from services import (
    message_to_dict,
    order_to_dict,
    product_to_dict,
    save_chat_attachment,
)

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin.html")


@admin_bp.route("/api/products", methods=["POST"])
@admin_required
def create_product():
    payload = request.get_json(force=True)
    product = Product(
        name=payload["name"],
        description=payload.get("description", ""),
        price=float(payload.get("price", 0)),
        category=payload.get("category", "digital"),
        image_url=payload.get("image_url", "https://picsum.photos/600/400"),
        is_free=bool(payload.get("is_free", False)),
        stock=int(payload.get("stock", 0)),
        min_stock=int(payload.get("min_stock", 0)),
        active=True,
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product_to_dict(product)), 201


@admin_bp.route("/api/products/<int:product_id>", methods=["PUT"])
@admin_required
def update_product(product_id: int):
    product = Product.query.get_or_404(product_id)
    payload = request.get_json(force=True)
    for field in ["name", "description", "image_url", "category"]:
        if field in payload:
            setattr(product, field, payload[field])
    for field in ["price", "stock", "min_stock"]:
        if field in payload:
            setattr(product, field, float(payload[field]) if field == "price" else int(payload[field]))
    if "is_free" in payload:
        product.is_free = bool(payload["is_free"])
    if "active" in payload:
        product.active = bool(payload["active"])
    db.session.commit()
    return jsonify(product_to_dict(product))


@admin_bp.route("/api/admin/kpis", methods=["GET"])
@admin_required
def admin_kpis():
    from sqlalchemy import func

    revenue = db.session.query(func.sum(Order.total)).scalar() or 0
    order_count = db.session.query(func.count(Order.id)).scalar() or 0
    avg_basket = float(revenue) / order_count if order_count else 0
    top_products = Product.query.order_by(Product.sales_count.desc()).limit(5).all()
    low_stock = Product.query.filter(
        Product.category == "physical", Product.stock <= Product.min_stock
    ).all()
    return jsonify(
        {
            "revenue": round(float(revenue), 2),
            "order_count": int(order_count),
            "avg_basket": round(avg_basket, 2),
            "top_products": [
                {"name": p.name, "sales_count": p.sales_count, "stock": p.stock} for p in top_products
            ],
            "low_stock": [product_to_dict(p) for p in low_stock],
        }
    )


@admin_bp.route("/api/admin/orders", methods=["GET"])
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([order_to_dict(o) for o in orders])


@admin_bp.route("/api/admin/orders/<int:order_id>", methods=["PATCH"])
@admin_required
def update_order(order_id: int):
    from datetime import datetime

    from models import Notification

    order = Order.query.get_or_404(order_id)
    payload = request.get_json(force=True)
    if "status" in payload:
        order.status = payload["status"]
    if "delivery_date" in payload and payload["delivery_date"]:
        order.delivery_date = datetime.strptime(payload["delivery_date"], "%Y-%m-%d").date()

    if order.status == "Prete":
        db.session.add(
            Notification(
                order_id=order.id,
                channel="push",
                message="Votre commande est prete au kiosque.",
            )
        )
    db.session.commit()
    return jsonify(order_to_dict(order))


@admin_bp.route("/api/admin/customers", methods=["GET"])
@admin_required
def admin_customers():
    from sqlalchemy import func

    customer_rows = (
        db.session.query(
            Order.email,
            Order.user_name,
            func.count(Order.id).label("nb_orders"),
            func.sum(Order.total).label("revenue_generated"),
            func.max(Order.created_at).label("last_order"),
        )
        .group_by(Order.email, Order.user_name)
        .order_by(func.sum(Order.total).desc())
        .all()
    )
    return jsonify(
        [
            {
                "email": row.email,
                "user_name": row.user_name,
                "nb_orders": int(row.nb_orders or 0),
                "revenue_generated": round(float(row.revenue_generated or 0), 2),
                "last_order": row.last_order.isoformat() if row.last_order else None,
            }
            for row in customer_rows
        ]
    )


@admin_bp.route("/api/admin/validate-coupon", methods=["POST"])
@admin_required
def validate_coupon():
    from datetime import datetime

    from models import Coupon

    payload = request.get_json(force=True)
    code = payload.get("code", "").strip().upper()
    coupon = Coupon.query.filter_by(code=code).first()
    if not coupon:
        return jsonify({"valid": False, "message": "Coupon introuvable."}), 404
    if coupon.is_used:
        return jsonify({"valid": False, "message": "Coupon deja utilise."}), 400

    coupon.is_used = True
    coupon.used_at = datetime.utcnow()
    order = Order.query.get(coupon.order_id)
    if order:
        order.status = "Livree"
    db.session.commit()
    return jsonify(
        {
            "valid": True,
            "message": "Coupon valide. Retrait autorise.",
            "used_at": coupon.used_at.isoformat(),
        }
    )


@admin_bp.route("/api/admin/chat/threads", methods=["GET"])
@admin_required
def list_chat_threads():
    from sqlalchemy import func

    unread_subquery = (
        db.session.query(
            SupportMessage.thread_id,
            func.count(SupportMessage.id).label("unread_count"),
        )
        .filter(
            SupportMessage.sender_role == "user",
            SupportMessage.is_read_by_admin.is_(False),
            SupportMessage.moderation_status == "visible",
        )
        .group_by(SupportMessage.thread_id)
        .subquery()
    )

    rows = (
        db.session.query(SupportThread, User, unread_subquery.c.unread_count)
        .join(User, User.id == SupportThread.user_id)
        .outerjoin(unread_subquery, unread_subquery.c.thread_id == SupportThread.id)
        .order_by(SupportThread.last_message_at.desc())
        .all()
    )

    payload = []
    for thread, user, unread_count in rows:
        last_msg = (
            SupportMessage.query.filter_by(thread_id=thread.id)
            .order_by(SupportMessage.created_at.desc())
            .first()
        )
        payload.append(
            {
                "id": thread.id,
                "user_id": user.id,
                "user_name": user.name,
                "user_email": user.email,
                "last_message_at": thread.last_message_at.isoformat() if thread.last_message_at else None,
                "last_message_preview": (last_msg.message or last_msg.attachment_name or "")[:70] if last_msg else "",
                "unread_count": int(unread_count or 0),
                "is_closed": thread.is_closed,
            }
        )
    return jsonify(payload)


@admin_bp.route("/api/admin/chat/threads/<int:thread_id>/messages", methods=["GET"])
@admin_required
def get_thread_messages(thread_id: int):
    thread = SupportThread.query.get_or_404(thread_id)
    messages = SupportMessage.query.filter_by(thread_id=thread.id).order_by(SupportMessage.created_at.asc()).all()
    for msg in messages:
        if msg.sender_role == "user":
            msg.is_read_by_admin = True
    db.session.commit()
    return jsonify({"thread_id": thread.id, "messages": [message_to_dict(m) for m in messages]})


@admin_bp.route("/api/admin/chat/threads/<int:thread_id>/messages", methods=["POST"])
@admin_required
def send_admin_message(thread_id: int):
    thread = SupportThread.query.get_or_404(thread_id)
    text = (request.form.get("message") or "").strip()
    file = request.files.get("attachment")
    if not text and not file:
        return jsonify({"error": "Message ou piece jointe requis."}), 400

    attachment_url = None
    attachment_name = None
    attachment_kind = None
    mime_type = None
    size_bytes = None
    if file and file.filename:
        try:
            attachment_url, attachment_name, attachment_kind, mime_type, size_bytes = save_chat_attachment(
                file, Path(current_app.config["CHAT_UPLOAD_DIR"])
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    current = current_user_data()
    msg = SupportMessage(
        thread_id=thread.id,
        sender_role="admin",
        author=current["name"],
        message=text or None,
        attachment_url=attachment_url,
        attachment_name=attachment_name,
        attachment_kind=attachment_kind,
        mime_type=mime_type,
        size_bytes=size_bytes,
        moderation_status="visible",
        is_read_by_admin=True,
        is_read_by_user=False,
    )
    thread.last_message_at = msg.created_at
    db.session.add(msg)
    db.session.commit()
    return jsonify({"message": "Envoye", "item": message_to_dict(msg)}), 201


@admin_bp.route("/api/admin/chat/messages/<int:message_id>/moderate", methods=["PATCH"])
@admin_required
def moderate_message(message_id: int):
    msg = SupportMessage.query.get_or_404(message_id)
    payload = request.get_json(force=True)
    status = payload.get("moderation_status", "").strip().lower()
    if status not in {"visible", "hidden"}:
        return jsonify({"error": "Statut de moderation invalide."}), 400
    msg.moderation_status = status
    db.session.commit()
    return jsonify({"message": "Moderation mise a jour.", "item": message_to_dict(msg)})
