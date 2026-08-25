import os
import re
import hmac
import hashlib
import secrets
import sqlite3
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "agrinova.db")

SESSION_HOURS = 24
MAX_LOGIN_ATTEMPTS = 5
LOCK_MINUTES = 15


def now():
    return datetime.now(timezone.utc)


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            country TEXT,
            language TEXT,
            role TEXT,
            verified INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            csrf_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            email TEXT PRIMARY KEY,
            attempts INTEGER DEFAULT 0,
            locked_until TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def hash_password(password):
    salt = secrets.token_bytes(32)

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        310000
    )

    return (
        "pbkdf2_sha256$310000$"
        + salt.hex()
        + "$"
        + derived.hex()
    )


def verify_password(password, stored):
    try:
        algorithm, iterations, salt_hex, hash_hex = stored.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            bytes.fromhex(salt_hex),
            int(iterations)
        )

        return hmac.compare_digest(
            derived.hex(),
            hash_hex
        )

    except Exception:
        return False


def valid_email(email):
    return bool(
        re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email
        )
    )


def valid_password(password):
    return (
        isinstance(password, str)
        and len(password) >= 8
        and bool(re.search(r"[A-Z]", password))
        and bool(re.search(r"[a-z]", password))
        and bool(re.search(r"[0-9]", password))
    )


def token_hash(token):
    return hashlib.sha256(
        token.encode()
    ).hexdigest()


def log_event(user_id, event):
    conn = db()

    conn.execute(
        """
        INSERT INTO security_events
        (user_id, event, created_at)
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            event,
            now().isoformat()
        )
    )

    conn.commit()
    conn.close()


def locked(email):
    conn = db()

    row = conn.execute(
        """
        SELECT attempts, locked_until
        FROM login_attempts
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    conn.close()

    if not row or not row["locked_until"]:
        return False

    return now() < datetime.fromisoformat(
        row["locked_until"]
    )


def failed_login(email):
    conn = db()

    row = conn.execute(
        """
        SELECT attempts
        FROM login_attempts
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    attempts = (row["attempts"] if row else 0) + 1

    locked_until = None

    if attempts >= MAX_LOGIN_ATTEMPTS:
        locked_until = (
            now() +
            timedelta(minutes=LOCK_MINUTES)
        ).isoformat()

    conn.execute(
        """
        INSERT INTO login_attempts
        (email, attempts, locked_until)
        VALUES (?, ?, ?)
        ON CONFLICT(email)
        DO UPDATE SET
            attempts=excluded.attempts,
            locked_until=excluded.locked_until
        """,
        (
            email,
            attempts,
            locked_until
        )
    )

    conn.commit()
    conn.close()


def successful_login(email):
    conn = db()

    conn.execute(
        """
        DELETE FROM login_attempts
        WHERE email = ?
        """,
        (email,)
    )

    conn.commit()
    conn.close()


def create_session(user_id):
    session_token = secrets.token_urlsafe(48)
    csrf_token = secrets.token_urlsafe(32)

    conn = db()

    conn.execute(
        """
        INSERT INTO sessions
        (user_id, token_hash, csrf_hash, expires_at, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            token_hash(session_token),
            token_hash(csrf_token),
            (
                now() +
                timedelta(hours=SESSION_HOURS)
            ).isoformat(),
            now().isoformat()
        )
    )

    conn.commit()
    conn.close()

    return session_token, csrf_token


def get_session(token):
    if not token:
        return None

    conn = db()

    row = conn.execute(
        """
        SELECT s.*, u.name, u.email, u.country,
               u.language, u.role, u.verified
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token_hash = ?
        """,
        (token_hash(token),)
    ).fetchone()

    conn.close()

    if not row:
        return None

    if datetime.fromisoformat(row["expires_at"]) <= now():
        return None

    return row


class Handler(BaseHTTPRequestHandler):

    def send_json(self, status, data, cookies=None):

        payload = json.dumps(
            data,
            ensure_ascii=False
        ).encode()

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(payload))
        )

        if cookies:
            for cookie in cookies:
                self.send_header(
                    "Set-Cookie",
                    cookie
                )

        self.end_headers()
        self.wfile.write(payload)

    def read_json(self):

        length = int(
            self.headers.get(
                "Content-Length",
                "0"
            )
        )

        raw = self.rfile.read(length)

        try:
            return json.loads(
                raw.decode("utf-8")
            )
        except Exception:
            return None

    def do_OPTIONS(self):

        self.send_response(204)

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, X-CSRF-Token"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.end_headers()

    def do_POST(self):

        if self.path == "/api/auth/register":
            return self.register()

        if self.path == "/api/auth/login":
            return self.login()

        if self.path == "/api/auth/logout":
            return self.logout()

        self.send_json(
            404,
            {"error": "Route inconnue"}
        )

    def do_GET(self):

        if self.path == "/api/auth/me":
            return self.me()

        if self.path == "/api/health":
            return self.send_json(
                200,
                {
                    "status": "ok",
                    "service": "AgriNova Auth",
                    "version": "5.1"
                }
            )

        self.send_json(
            404,
            {"error": "Route inconnue"}
        )

    def register(self):

        data = self.read_json()

        if not data:
            return self.send_json(
                400,
                {"error": "Données invalides"}
            )

        name = str(
            data.get("name", "")
        ).strip()

        email = str(
            data.get("email", "")
        ).strip().lower()

        password = data.get("password", "")

        country = str(
            data.get("country", "")
        ).strip()

        language = str(
            data.get("language", "")
        ).strip()

        role = str(
            data.get("role", "")
        ).strip()

        if not name or len(name) > 120:
            return self.send_json(
                400,
                {"error": "Nom invalide"}
            )

        if not valid_email(email):
            return self.send_json(
                400,
                {"error": "Adresse email invalide"}
            )

        if not valid_password(password):
            return self.send_json(
                400,
                {
                    "error":
                    "Mot de passe trop faible"
                }
            )

        conn = db()

        exists = conn.execute(
            """
            SELECT id FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if exists:
            conn.close()

            return self.send_json(
                409,
                {
                    "error":
                    "Un compte existe déjà avec cet email"
                }
            )

        cur = conn.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password_hash,
                country,
                language,
                role,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                email,
                hash_password(password),
                country,
                language,
                role,
                now().isoformat()
            )
        )

        user_id = cur.lastrowid

        conn.commit()
        conn.close()

        log_event(
            user_id,
            "account_created"
        )

        return self.send_json(
            201,
            {
                "success": True,
                "message":
                    "Compte AgriNova créé",
                "user_id": user_id
            }
        )

    def login(self):

        data = self.read_json()

        if not data:
            return self.send_json(
                400,
                {"error": "Données invalides"}
            )

        email = str(
            data.get("email", "")
        ).strip().lower()

        password = data.get(
            "password",
            ""
        )

        if locked(email):
            return self.send_json(
                429,
                {
                    "error":
                    "Compte temporairement verrouillé"
                }
            )

        conn = db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        conn.close()

        if not user or not verify_password(
            password,
            user["password_hash"]
        ):
            failed_login(email)

            if user:
                log_event(
                    user["id"],
                    "login_failed"
                )

            return self.send_json(
                401,
                {
                    "error":
                    "Identifiants incorrects"
                }
            )

        successful_login(email)

        session_token, csrf_token = (
            create_session(user["id"])
        )

        log_event(
            user["id"],
            "login_success"
        )

        cookies = [

            (
                "agrinova_session="
                + session_token
                + "; HttpOnly; SameSite=Strict; "
                "Path=/; Max-Age=86400"
            ),

            (
                "agrinova_csrf="
                + csrf_token
                + "; SameSite=Strict; "
                "Path=/; Max-Age=86400"
            )
        ]

        return self.send_json(
            200,
            {
                "success": True,
                "user": {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "country": user["country"],
                    "language": user["language"],
                    "role": user["role"],
                    "verified": bool(
                        user["verified"]
                    )
                }
            },
            cookies
        )

    def me(self):

        cookie = self.headers.get(
            "Cookie",
            ""
        )

        token = None

        for part in cookie.split(";"):

            part = part.strip()

            if part.startswith(
                "agrinova_session="
            ):
                token = part.split(
                    "=",
                    1
                )[1]

        session = get_session(token)

        if not session:
            return self.send_json(
                401,
                {
                    "authenticated": False
                }
            )

        return self.send_json(
            200,
            {
                "authenticated": True,
                "user": {
                    "id": session["user_id"],
                    "name": session["name"],
                    "email": session["email"],
                    "country": session["country"],
                    "language": session["language"],
                    "role": session["role"],
                    "verified": bool(
                        session["verified"]
                    )
                }
            }
        )

    def logout(self):

        cookie = self.headers.get(
            "Cookie",
            ""
        )

        token = None

        for part in cookie.split(";"):

            part = part.strip()

            if part.startswith(
                "agrinova_session="
            ):
                token = part.split(
                    "=",
                    1
                )[1]

        if token:

            session = get_session(token)

            if session:

                conn = db()

                conn.execute(
                    """
                    DELETE FROM sessions
                    WHERE token_hash = ?
                    """,
                    (token_hash(token),)
                )

                conn.commit()
                conn.close()

                log_event(
                    session["user_id"],
                    "logout"
                )

        return self.send_json(
            200,
            {"success": True},
            [
                (
                    "agrinova_session=; "
                    "HttpOnly; SameSite=Strict; "
                    "Path=/; Max-Age=0"
                ),
                (
                    "agrinova_csrf=; "
                    "SameSite=Strict; "
                    "Path=/; Max-Age=0"
                )
            ]
        )


init_db()


PORT = int(os.environ.get("PORT", "8092"))

server = ThreadingHTTPServer(
    ("0.0.0.0", PORT),
    Handler
)

print("========================================")
print("🔐 AGRINOVA AUTH BACKEND V5.1")
print("========================================")
print(f"Serveur : http://0.0.0.0:{PORT}")
print("SQLite  : agrinova.db")
print("Hash    : PBKDF2-SHA256")
print("Sessions: serveur")
print("Rate limit : ACTIVÉ")
print("========================================")

server.serve_forever()
