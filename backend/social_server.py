#!/usr/bin/env python3

import os
import json
import sqlite3
import secrets
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8091"))
DB = "data/agrinova_social.db"


def now():
    return datetime.now(timezone.utc).isoformat()


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = db()

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        country TEXT DEFAULT '',
        language TEXT DEFAULT 'fr',
        role TEXT DEFAULT 'user',
        avatar TEXT DEFAULT '',
        bio TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS presence (
        user_id TEXT PRIMARY KEY,
        status TEXT NOT NULL DEFAULT 'offline',
        last_seen TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS conversation_members (
        conversation_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        PRIMARY KEY(conversation_id, user_id),
        FOREIGN KEY(conversation_id) REFERENCES conversations(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        body TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(conversation_id) REFERENCES conversations(id),
        FOREIGN KEY(sender_id) REFERENCES users(id)
    );

    CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages(conversation_id, created_at);
    """)

    conn.commit()
    conn.close()


def response_json(handler, data, status=200):

    body = json.dumps(
        data,
        ensure_ascii=False
    ).encode("utf-8")

    handler.send_response(status)
    handler.send_header(
        "Content-Type",
        "application/json; charset=utf-8"
    )
    handler.send_header(
        "Content-Length",
        str(len(body))
    )
    handler.send_header(
        "Access-Control-Allow-Origin",
        "*"
    )
    handler.send_header(
        "Access-Control-Allow-Headers",
        "Content-Type"
    )
    handler.end_headers()

    handler.wfile.write(body)


def read_json(handler):

    length = int(
        handler.headers.get("Content-Length", "0")
    )

    if length <= 0:
        return {}

    raw = handler.rfile.read(length)

    return json.loads(raw.decode("utf-8"))


class API(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print("[AgriNova]", format % args)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )
        self.end_headers()

    def do_GET(self):

        parsed = urlparse(self.path)
        path = parsed.path

        try:

            if path == "/api/health":

                return response_json(
                    self,
                    {
                        "status": "ok",
                        "service": "AgriNova Social API",
                        "version": "V6.1.2",
                        "time": now()
                    }
                )

            if path == "/api/users":

                conn = db()

                rows = conn.execute("""
                    SELECT
                        u.*,
                        COALESCE(p.status, 'offline') AS status,
                        p.last_seen
                    FROM users u
                    LEFT JOIN presence p
                    ON p.user_id = u.id
                    ORDER BY u.created_at DESC
                """).fetchall()

                conn.close()

                return response_json(
                    self,
                    {"users": [dict(row) for row in rows]}
                )

            if path.startswith("/api/conversations/"):

                conversation_id = path.split("/")[-1]

                conn = db()

                rows = conn.execute("""
                    SELECT
                        id,
                        conversation_id,
                        sender_id,
                        body,
                        created_at
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY created_at ASC
                """, (conversation_id,)).fetchall()

                conn.close()

                return response_json(
                    self,
                    {
                        "conversation_id": conversation_id,
                        "messages": [
                            dict(row) for row in rows
                        ]
                    }
                )

            return response_json(
                self,
                {"error": "Route inconnue"},
                404
            )

        except Exception as e:

            return response_json(
                self,
                {
                    "error": "Erreur serveur",
                    "detail": str(e)
                },
                500
            )

    def do_POST():

        pass


def post_handler(self):

    path = urlparse(self.path).path

    try:

        data = read_json(self)

        # -----------------------------
        # CREATE USER
        # -----------------------------

        if path == "/api/users":

            name = str(data.get("name", "")).strip()

            if not name:
                return response_json(
                    self,
                    {"error": "Nom obligatoire"},
                    400
                )

            user_id = secrets.token_urlsafe(16)

            conn = db()

            conn.execute("""
                INSERT INTO users
                (id, name, country, language, role, avatar, bio, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                name,
                data.get("country", ""),
                data.get("language", "fr"),
                data.get("role", "user"),
                data.get("avatar", ""),
                data.get("bio", ""),
                now()
            ))

            conn.execute("""
                INSERT INTO presence
                (user_id, status, last_seen)
                VALUES (?, 'offline', ?)
            """, (
                user_id,
                now()
            ))

            conn.commit()

            row = conn.execute("""
                SELECT
                    u.*,
                    p.status,
                    p.last_seen
                FROM users u
                JOIN presence p
                ON p.user_id = u.id
                WHERE u.id = ?
            """, (user_id,)).fetchone()

            conn.close()

            return response_json(
                self,
                {"user": dict(row)},
                201
            )

        # -----------------------------
        # UPDATE PRESENCE
        # -----------------------------

        if path == "/api/presence":

            user_id = str(data.get("user_id", "")).strip()
            status = str(data.get("status", "offline")).strip()

            allowed = {
                "online",
                "away",
                "offline"
            }

            if status not in allowed:
                return response_json(
                    self,
                    {"error": "Statut invalide"},
                    400
                )

            conn = db()

            exists = conn.execute(
                "SELECT id FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

            if not exists:
                conn.close()

                return response_json(
                    self,
                    {"error": "Utilisateur introuvable"},
                    404
                )

            conn.execute("""
                INSERT INTO presence
                (user_id, status, last_seen)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET
                    status = excluded.status,
                    last_seen = excluded.last_seen
            """, (
                user_id,
                status,
                now()
            ))

            conn.commit()
            conn.close()

            return response_json(
                self,
                {
                    "success": True,
                    "user_id": user_id,
                    "status": status
                }
            )

        # -----------------------------
        # CREATE CONVERSATION
        # -----------------------------

        if path == "/api/conversations":

            user_a = str(data.get("user_a", "")).strip()
            user_b = str(data.get("user_b", "")).strip()

            if not user_a or not user_b or user_a == user_b:
                return response_json(
                    self,
                    {"error": "Participants invalides"},
                    400
                )

            conversation_id = secrets.token_urlsafe(18)

            conn = db()

            users = conn.execute("""
                SELECT id
                FROM users
                WHERE id IN (?, ?)
            """, (user_a, user_b)).fetchall()

            if len(users) != 2:
                conn.close()

                return response_json(
                    self,
                    {"error": "Utilisateur introuvable"},
                    404
                )

            conn.execute("""
                INSERT INTO conversations
                (id, created_at)
                VALUES (?, ?)
            """, (
                conversation_id,
                now()
            ))

            conn.executemany("""
                INSERT INTO conversation_members
                (conversation_id, user_id)
                VALUES (?, ?)
            """, [
                (conversation_id, user_a),
                (conversation_id, user_b)
            ])

            conn.commit()
            conn.close()

            return response_json(
                self,
                {
                    "success": True,
                    "conversation": {
                        "id": conversation_id,
                        "participants": [
                            user_a,
                            user_b
                        ]
                    }
                },
                201
            )

        # -----------------------------
        # SEND MESSAGE
        # -----------------------------

        if path == "/api/messages":

            conversation_id = str(
                data.get("conversation_id", "")
            ).strip()

            sender_id = str(
                data.get("sender_id", "")
            ).strip()

            body = str(
                data.get("body", "")
            ).strip()

            if not conversation_id:
                return response_json(
                    self,
                    {"error": "Conversation obligatoire"},
                    400
                )

            if not sender_id:
                return response_json(
                    self,
                    {"error": "Expéditeur obligatoire"},
                    400
                )

            if not body:
                return response_json(
                    self,
                    {"error": "Message vide"},
                    400
                )

            if len(body) > 5000:
                return response_json(
                    self,
                    {"error": "Message trop long"},
                    400
                )

            conn = db()

            member = conn.execute("""
                SELECT 1
                FROM conversation_members
                WHERE conversation_id = ?
                AND user_id = ?
            """, (
                conversation_id,
                sender_id
            )).fetchone()

            if not member:
                conn.close()

                return response_json(
                    self,
                    {"error": "Accès refusé"},
                    403
                )

            message_id = secrets.token_urlsafe(18)

            conn.execute("""
                INSERT INTO messages
                (id, conversation_id, sender_id, body, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                message_id,
                conversation_id,
                sender_id,
                body,
                now()
            ))

            conn.commit()
            conn.close()

            return response_json(
                self,
                {
                    "success": True,
                    "message": {
                        "id": message_id,
                        "conversation_id": conversation_id,
                        "sender_id": sender_id,
                        "body": body,
                        "created_at": now()
                    }
                },
                201
            )

        return response_json(
            self,
            {"error": "Route inconnue"},
            404
        )

    except Exception as e:

        return response_json(
            self,
            {
                "error": "Erreur serveur",
                "detail": str(e)
            },
            500
        )


API.do_POST = post_handler


if __name__ == "__main__":

    init_db()

    print("========================================")
    print("💬 AGRINOVA SOCIAL BACKEND V6.1.2")
    print("========================================")
    print(f"API              : http://127.0.0.1:{PORT}")
    print("Profils          : SQLite")
    print("Présence         : Online/Away/Offline")
    print("Conversations    : SQLite")
    print("Messages         : SQLite")
    print("Accès conversation: Vérifié")
    print("Paiement         : NON CONNECTÉ")
    print("========================================")

    server = ThreadingHTTPServer(
        (HOST, PORT),
        API
    )

    server.serve_forever()
