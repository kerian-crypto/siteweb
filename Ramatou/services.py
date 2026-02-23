from __future__ import annotations

import mimetypes
import secrets
from datetime import datetime
from pathlib import Path

import qrcode
from flask import url_for
from sqlalchemy import func, text
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

from extensions import db
from models import (
    Coupon,
    Notification,
    Order,
    OrderItem,
    Product,
    Rating,
    SupportMessage,
    SupportThread,
    User,
)

ALLOWED_EXTENSIONS = {
    "image": {"jpg", "jpeg", "png", "gif", "webp"},
    "video": {"mp4", "mov", "webm", "mkv"},
    "document": {"pdf", "doc", "docx", "txt", "xls", "xlsx", "ppt", "pptx"},
}
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024


def product_to_dict(product: Product) -> dict:
    avg_stars = db.session.query(func.avg(Rating.stars)).filter(Rating.product_id == product.id).scalar()
    rating_count = db.session.query(func.count(Rating.id)).filter(Rating.product_id == product.id).scalar()
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "category": product.category,
        "image_url": product.image_url,
        "is_free": product.is_free,
        "stock": product.stock,
        "min_stock": product.min_stock,
        "active": product.active,
        "sales_count": product.sales_count,
        "avg_stars": round(float(avg_stars), 2) if avg_stars else 0,
        "rating_count": int(rating_count or 0),
    }


def order_to_dict(order: Order) -> dict:
    items = (
        db.session.query(OrderItem, Product)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(OrderItem.order_id == order.id)
        .all()
    )
    coupon = Coupon.query.filter_by(order_id=order.id).first()

    item_payload = []
    downloads = []
    for item, product in items:
        item_payload.append(
            {
                "product_id": product.id,
                "name": product.name,
                "qty": item.qty,
                "unit_price": item.unit_price,
                "category": product.category,
            }
        )
        if item.download_token:
            downloads.append(
                {
                    "product": product.name,
                    "url": url_for("user.download_digital_product", token=item.download_token),
                }
            )

    return {
        "id": order.id,
        "user_name": order.user_name,
        "email": order.email,
        "phone": order.phone,
        "status": order.status,
        "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
        "created_at": order.created_at.isoformat(),
        "total": order.total,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "items": item_payload,
        "downloads": downloads,
        "coupon": {
            "code": coupon.code,
            "qr_path": coupon.qr_path,
            "is_used": coupon.is_used,
            "used_at": coupon.used_at.isoformat() if coupon.used_at else None,
        }
        if coupon
        else None,
    }


def create_invoice(order: Order, invoice_dir: Path, base_dir: Path) -> str:
    invoice_dir.mkdir(parents=True, exist_ok=True)
    invoice_path = invoice_dir / f"invoice_{order.id}.html"
    rows = []
    items = (
        db.session.query(OrderItem, Product)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(OrderItem.order_id == order.id)
        .all()
    )
    for item, product in items:
        rows.append(f"<tr><td>{product.name}</td><td>{item.qty}</td><td>{item.unit_price:.2f} FCFA</td></tr>")

    invoice_html = f"""
    <html>
      <head><meta charset='utf-8'><title>Facture #{order.id}</title></head>
      <body>
        <h1>Facture GrieeLive #{order.id}</h1>
        <p>Client: {order.user_name} ({order.email})</p>
        <p>Date: {order.created_at.strftime('%d/%m/%Y %H:%M')}</p>
        <table border='1' cellpadding='8' cellspacing='0'>
          <thead><tr><th>Produit</th><th>Qte</th><th>Prix unitaire</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
        <h3>Total: {order.total:.2f} FCFA</h3>
      </body>
    </html>
    """.strip()
    invoice_path.write_text(invoice_html, encoding="utf-8")
    return str(invoice_path.relative_to(base_dir))


def create_qr_coupon(order_id: int, qrcode_dir: Path) -> Coupon:
    qrcode_dir.mkdir(parents=True, exist_ok=True)
    code = f"GRIEELIVE-{order_id}-{secrets.token_hex(4).upper()}"
    filename = f"coupon_order_{order_id}.png"
    qr_rel_path = f"/static/qrcodes/{filename}"
    img = qrcode.make(code)
    img.save(qrcode_dir / filename)
    coupon = Coupon(order_id=order_id, code=code, qr_path=qr_rel_path)
    db.session.add(coupon)
    return coupon


def get_or_create_support_thread(user_id: int) -> SupportThread:
    thread = SupportThread.query.filter_by(user_id=user_id).first()
    if thread:
        return thread
    thread = SupportThread(user_id=user_id)
    db.session.add(thread)
    db.session.flush()
    return thread


def message_to_dict(msg: SupportMessage) -> dict:
    return {
        "id": msg.id,
        "thread_id": msg.thread_id,
        "sender_role": msg.sender_role,
        "author": msg.author,
        "message": msg.message,
        "attachment_url": msg.attachment_url,
        "attachment_name": msg.attachment_name,
        "attachment_kind": msg.attachment_kind,
        "mime_type": msg.mime_type,
        "size_bytes": msg.size_bytes,
        "moderation_status": msg.moderation_status,
        "created_at": msg.created_at.isoformat(),
    }


def _infer_attachment_kind(ext: str) -> str | None:
    for kind, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts:
            return kind
    return None


def save_chat_attachment(file: FileStorage, upload_dir: Path) -> tuple[str, str, str, str, int]:
    filename = secure_filename(file.filename or "")
    if not filename:
        raise ValueError("Nom de fichier invalide.")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    kind = _infer_attachment_kind(ext)
    if not kind:
        raise ValueError("Type de fichier non autorise.")

    file.stream.seek(0, 2)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > MAX_ATTACHMENT_BYTES:
        raise ValueError("Fichier trop volumineux (max 20MB).")

    upload_dir.mkdir(parents=True, exist_ok=True)
    unique = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}_{filename}"
    path = upload_dir / unique
    file.save(path)

    mime_type = file.mimetype or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return f"/static/chat_uploads/{unique}", filename, kind, mime_type, size


def ensure_sqlite_column(table_name: str, column_name: str, ddl: str) -> None:
    if db.engine.url.get_backend_name() != "sqlite":
        return
    info = db.session.execute(text(f"PRAGMA table_info({table_name})")).mappings().all()
    existing = {row["name"] for row in info}
    if column_name not in existing:
        db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))


def migrate_schema() -> None:
    ensure_sqlite_column("user", "password_hash", "password_hash VARCHAR(255)")
    ensure_sqlite_column("user", "created_at", "created_at DATETIME")
    db.session.commit()


def seed_data(downloads_dir: Path) -> None:
    if Product.query.count() == 0:
        downloads_dir.mkdir(parents=True, exist_ok=True)
        (downloads_dir / "ebook-recettes.pdf").write_text(
            "Demo eBook recettes nutritionnelles.", encoding="utf-8"
        )
        (downloads_dir / "fiches-nutrition.pdf").write_text(
            "Demo fiches techniques nutritionnelles.", encoding="utf-8"
        )
        db.session.add_all(
            [
                Product(
                    name="Pack Detox Naturel",
                    description="Kit alimentaire physique pour 7 jours.",
                    price=18000,
                    category="physical",
                    image_url="https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=800&q=80",
                    is_free=False,
                    stock=30,
                    min_stock=10,
                ),
                Product(
                    name="Guide Recettes Minceur",
                    description="Livre numerique de 50 recettes healthy.",
                    price=4500,
                    category="digital",
                    image_url="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80",
                    is_free=False,
                    stock=9999,
                    min_stock=0,
                ),
                Product(
                    name="Fiches Techniques Nutritionnelles",
                    description="Pack PDF avec indicateurs et portions.",
                    price=0,
                    category="digital",
                    image_url="https://images.unsplash.com/photo-1484981138541-f5c27c6a7bd8?auto=format&fit=crop&w=800&q=80",
                    is_free=True,
                    stock=9999,
                    min_stock=0,
                ),
                Product(
                    name="Snacks Proteines Premium",
                    description="Boite physique de snacks faibles en sucre.",
                    price=9000,
                    category="physical",
                    image_url="https://images.unsplash.com/photo-1494597564530-871f2b93ac55?auto=format&fit=crop&w=800&q=80",
                    is_free=False,
                    stock=22,
                    min_stock=7,
                ),
            ]
        )

    admin = User.query.filter_by(email="ramatou@gmail.com").first()
    if not admin:
        admin = User(name="Ramatou Admin", email="ramatou@gmail.com", is_admin=True)
        db.session.add(admin)
    admin.is_admin = True
    admin.password_hash = generate_password_hash("ramatouAdmin")

    db.session.commit()
