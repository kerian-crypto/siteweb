from __future__ import annotations

from flask import session
from flask_socketio import emit, join_room

from extensions import socketio


def room_for_thread(thread_id: int) -> str:
    return f"thread:{thread_id}"


def room_admin_global() -> str:
    return "admins:global"


@socketio.on("join_admin_global")
def handle_join_admin_global():
    if not session.get("user_id") or not session.get("is_admin"):
        emit("error_event", {"error": "Acces admin requis."})
        return
    join_room(room_admin_global())
    emit("joined_admin_global", {"ok": True})


@socketio.on("join_thread")
def handle_join_thread(payload):
    if not session.get("user_id"):
        emit("error_event", {"error": "Connexion requise."})
        return
    thread_id = int((payload or {}).get("thread_id", 0))
    if thread_id <= 0:
        emit("error_event", {"error": "Thread invalide."})
        return
    join_room(room_for_thread(thread_id))
    emit("joined_thread", {"thread_id": thread_id})
