from __future__ import annotations

import secrets
from datetime import date, timedelta
from pathlib import Path

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import (
    Notification,
    Order,
    OrderItem,
    Product,
    Rating,
    SupportMessage,
    User,
)
from security import current_user_data, get_or_create_csrf_token, is_logged_in, login_required
from services import (
    create_invoice,
    create_qr_coupon,
    get_or_create_support_thread,
    message_to_dict,
    order_to_dict,
    product_to_dict,
    save_chat_attachment,
)

user_bp = Blueprint("user", __name__)


@user_bp.route("/")
def public_home():
    return render_template("public_home.html")


@user_bp.route("/auth", methods=["GET", "POST"])
def auth_page():
    tab = request.args.get("tab", "login")
    next_url = request.args.get("next", "/shop")
    error = None

    if request.method == "POST":
        mode = request.form.get("mode", "login")
        if mode == "register":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            phone = request.form.get("phone", "").strip()
            password = request.form.get("password", "")
            if not name or not email or len(password) < 6:
                error = "Veuillez renseigner un nom, un email valide et un mot de passe >= 6 caracteres."
                tab = "register"
            elif User.query.filter_by(email=email).first():
                error = "Cet email existe deja."
                tab = "register"
            else:
                user = User(
                    name=name,
                    email=email,
                    phone=phone,
                    password_hash=generate_password_hash(password),
                )
                db.session.add(user)
                db.session.commit()
                session["user_id"] = user.id
                session["user_name"] = user.name
                session["user_email"] = user.email
                session["is_admin"] = bool(user.is_admin)
                get_or_create_csrf_token()
                return redirect("/shop")
        else:
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()
            if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
                error = "Email ou mot de passe incorrect."
                tab = "login"
            else:
                session["user_id"] = user.id
                session["user_name"] = user.name
                session["user_email"] = user.email
                session["is_admin"] = bool(user.is_admin)
                get_or_create_csrf_token()
                return redirect(next_url)

    return render_template("auth.html", tab=tab, next_url=next_url, error=error)


@user_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")


@user_bp.route("/shop")
@login_required
def shop_home():
    return render_template("shop.html")


@user_bp.route("/nutrition")
@login_required
def nutrition_page():
    return render_template(
        "products.html",
        page_title="Produits Nutritionnels",
        page_subtitle="Tous les produits physiques nutritionnels disponibles.",
        category="physical",
    )


@user_bp.route("/fiches-techniques")
@login_required
def fiches_page():
    return render_template(
        "products.html",
        page_title="Fiches Techniques",
        page_subtitle="Ressources numeriques, eBooks et fiches de reference.",
        category="digital",
    )


@user_bp.route("/bibliographie")
def bibliography_page():
    return render_template("bibliography.html")


@user_bp.route("/mes-achats")
@login_required
def my_purchases_page():
    return render_template("my_purchases.html")


@user_bp.route("/api/me", methods=["GET"])
def api_me():
    return jsonify({"authenticated": is_logged_in(), "user": current_user_data()})


@user_bp.route("/api/products", methods=["GET"])
def get_products():
    category = request.args.get("category", "all")
    query = Product.query.filter_by(active=True)
    if category in {"digital", "physical"}:
        query = query.filter_by(category=category)
    products = [product_to_dict(p) for p in query.order_by(Product.id.desc()).all()]
    return jsonify(products)


@user_bp.route("/api/ratings", methods=["POST"])
@login_required
def add_rating():
    payload = request.get_json(force=True)
    stars = int(payload.get("stars", 0))
    if stars < 1 or stars > 5:
        return jsonify({"error": "Les etoiles doivent etre entre 1 et 5."}), 400

    rating = Rating(
        product_id=int(payload["product_id"]),
        user_name=current_user_data()["name"],
        stars=stars,
        comment=payload.get("comment", ""),
        verified=True,
    )
    db.session.add(rating)
    db.session.commit()
    return jsonify({"message": "Note enregistree."}), 201


@user_bp.route("/api/ratings/<int:product_id>", methods=["GET"])
def get_ratings(product_id: int):
    ratings = Rating.query.filter_by(product_id=product_id).order_by(Rating.created_at.desc()).limit(20).all()
    return jsonify(
        [
            {
                "id": r.id,
                "user_name": r.user_name,
                "stars": r.stars,
                "comment": r.comment,
                "verified": r.verified,
                "created_at": r.created_at.isoformat(),
            }
            for r in ratings
        ]
    )


@user_bp.route("/api/checkout", methods=["POST"])
@login_required
def checkout():
    payload = request.get_json(force=True)
    current = current_user_data()
    user = User.query.get(current["id"])
    payment_method = payload.get("payment_method", "Orange Money")
    items = payload.get("items", [])
    phone = (payload.get("phone") or user.phone or "").strip()

    if not items:
        return jsonify({"error": "Panier vide."}), 400

    order = Order(
        user_name=current["name"],
        email=current["email"],
        phone=phone,
        payment_method=payment_method,
        payment_status="Paid",
        status="En preparation",
        delivery_date=date.today() + timedelta(days=1),
    )
    db.session.add(order)
    db.session.flush()

    total = 0.0
    has_physical = False
    for item in items:
        product = Product.query.get(int(item.get("product_id")))
        if not product or not product.active:
            db.session.rollback()
            return jsonify({"error": "Produit invalide dans le panier."}), 400

        qty = max(1, int(item.get("qty", 1)))
        if product.category == "physical":
            has_physical = True
            if product.stock < qty:
                db.session.rollback()
                return jsonify({"error": f"Stock insuffisant pour {product.name}."}), 400
            product.stock -= qty

        unit_price = 0.0 if product.is_free else product.price
        total += unit_price * qty
        product.sales_count += qty
        download_token = secrets.token_urlsafe(20) if product.category == "digital" else None
        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                qty=qty,
                unit_price=unit_price,
                download_token=download_token,
            )
        )

    order.total = total
    if has_physical:
        create_qr_coupon(order.id, Path(current_app.config["QRCODE_DIR"]))
    invoice_rel_path = create_invoice(
        order,
        Path(current_app.config["INVOICE_DIR"]),
        Path(current_app.config["BASE_DIR"]),
    )
    db.session.add_all(
        [
            Notification(order_id=order.id, channel="email", message=f"Facture creee: {invoice_rel_path}"),
            Notification(
                order_id=order.id,
                channel="sms",
                message="Votre commande est en preparation. Vous serez notifie(e) quand elle sera prete.",
            ),
        ]
    )
    db.session.commit()
    return jsonify(order_to_dict(order)), 201


@user_bp.route("/api/my-purchases", methods=["GET"])
@login_required
def my_purchases():
    email = current_user_data()["email"]
    orders = Order.query.filter_by(email=email).order_by(Order.created_at.desc()).all()
    return jsonify([order_to_dict(o) for o in orders])


@user_bp.route("/download/<token>", methods=["GET"])
@login_required
def download_digital_product(token: str):
    item = OrderItem.query.filter_by(download_token=token).first_or_404()
    order = Order.query.get_or_404(item.order_id)
    if order.email != current_user_data()["email"]:
        return jsonify({"error": "Acces refuse."}), 403

    product = Product.query.get_or_404(item.product_id)
    filename_map = {
        "Guide Recettes Minceur": "ebook-recettes.pdf",
        "Fiches Techniques Nutritionnelles": "fiches-nutrition.pdf",
    }
    filename = filename_map.get(product.name, "ebook-recettes.pdf")
    return send_from_directory(Path(current_app.config["DOWNLOADS_DIR"]), filename, as_attachment=True)


@user_bp.route("/api/orders/<int:order_id>", methods=["GET"])
@login_required
def get_order(order_id: int):
    order = Order.query.get_or_404(order_id)
    if order.email != current_user_data()["email"]:
        return jsonify({"error": "Acces refuse."}), 403
    return jsonify(order_to_dict(order))


@user_bp.route("/api/chat/thread", methods=["GET"])
@login_required
def get_chat_thread():
    current = current_user_data()
    thread = get_or_create_support_thread(current["id"])

    messages = (
        SupportMessage.query.filter_by(thread_id=thread.id)
        .filter(SupportMessage.moderation_status == "visible")
        .order_by(SupportMessage.created_at.asc())
        .all()
    )
    for msg in messages:
        if msg.sender_role == "admin":
            msg.is_read_by_user = True
    db.session.commit()

    return jsonify({"thread_id": thread.id, "messages": [message_to_dict(m) for m in messages]})


@user_bp.route("/api/chat/messages", methods=["POST"])
@login_required
def send_chat_message():
    current = current_user_data()
    thread = get_or_create_support_thread(current["id"])
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

    msg = SupportMessage(
        thread_id=thread.id,
        sender_role="user",
        author=current["name"],
        message=text or None,
        attachment_url=attachment_url,
        attachment_name=attachment_name,
        attachment_kind=attachment_kind,
        mime_type=mime_type,
        size_bytes=size_bytes,
        moderation_status="visible",
        is_read_by_user=True,
        is_read_by_admin=False,
    )
    thread.last_message_at = msg.created_at
    db.session.add(msg)
    db.session.commit()
    return jsonify({"message": "Envoye", "item": message_to_dict(msg)}), 201
