"""Időpontfoglaló – minimális CRUD webalkalmazás az audit tárgyaként.

Az alkalmazás kódja a v1 és a v2 környezetben azonos; az audit a futtatókörnyezetre irányul.
"""
import os
import time
from datetime import datetime, timedelta

import psycopg
from flask import Flask, Response, abort, redirect, render_template_string, request, url_for

app = Flask(__name__)


def _read_secret(name: str, default: str | None = None) -> str | None:
    """Titok olvasása: először <NAME>_FILE (Docker secret), utána <NAME> környezeti változó."""
    path = os.environ.get(f"{name}_FILE")
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    return os.environ.get(name, default)


def _dsn() -> str:
    url = _read_secret("DATABASE_URL")
    if url:
        return url
    return (
        f"host={os.environ.get('DB_HOST', 'db')} dbname={os.environ.get('DB_NAME', 'booking')} "
        f"user={os.environ.get('DB_USER', 'booking')} password={_read_secret('DB_PASSWORD', '')}"
    )


ADMIN_USER = os.environ.get("ADMIN_USER", "admin")


def db():
    return psycopg.connect(_dsn(), autocommit=True)


def init_db(retries: int = 30) -> None:
    for _ in range(retries):
        try:
            with db() as conn:
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS slots (
                           id SERIAL PRIMARY KEY,
                           starts_at TIMESTAMP NOT NULL UNIQUE,
                           name TEXT,
                           email TEXT,
                           booked_at TIMESTAMP)"""
                )
                if conn.execute("SELECT count(*) FROM slots").fetchone()[0] == 0:
                    base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
                    for d in range(5):
                        for h in range(0, 8):
                            conn.execute("INSERT INTO slots (starts_at) VALUES (%s)",
                                         (base + timedelta(days=d, hours=h),))
            return
        except psycopg.OperationalError:
            time.sleep(2)
    raise RuntimeError("Az adatbázis nem érhető el")


PAGE = """<!doctype html><html lang="hu"><head><meta charset="utf-8">
<title>Időpontfoglaló</title>
<style>body{font-family:system-ui,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem}
table{border-collapse:collapse;width:100%}td,th{padding:.4rem;border-bottom:1px solid #ddd;text-align:left}
.free{color:#1a7f37}.taken{color:#999}</style></head><body>
<h1>Időpontfoglaló</h1>
{% if msg %}<p><strong>{{ msg }}</strong></p>{% endif %}
<table><tr><th>Időpont</th><th>Állapot</th><th></th></tr>
{% for s in slots %}<tr><td>{{ s[1].strftime('%Y-%m-%d %H:%M') }}</td>
{% if s[2] %}<td class="taken">foglalt</td><td></td>
{% else %}<td class="free">szabad</td><td><form method="post" action="{{ url_for('book', slot_id=s[0]) }}">
<input name="name" placeholder="Név" required maxlength="80">
<input name="email" type="email" placeholder="E-mail" required maxlength="120">
<button>Foglalás</button></form></td>{% endif %}</tr>{% endfor %}
</table><p><a href="{{ url_for('admin') }}">Admin</a></p></body></html>"""

ADMIN = """<!doctype html><html lang="hu"><head><meta charset="utf-8"><title>Admin</title></head><body>
<h1>Foglalások</h1><table>
{% for s in slots %}<tr><td>{{ s[1].strftime('%Y-%m-%d %H:%M') }}</td><td>{{ s[2] }}</td><td>{{ s[3] }}</td>
<td><form method="post" action="{{ url_for('cancel', slot_id=s[0]) }}"><button>Törlés</button></form></td></tr>
{% endfor %}</table><p><a href="{{ url_for('index') }}">Vissza</a></p></body></html>"""


def require_admin():
    auth = request.authorization
    if not auth or auth.username != ADMIN_USER or auth.password != _read_secret("ADMIN_PASSWORD"):
        return Response("Hitelesítés szükséges", 401, {"WWW-Authenticate": 'Basic realm="admin"'})
    return None


@app.get("/")
def index():
    with db() as conn:
        slots = conn.execute(
            "SELECT id, starts_at, name IS NOT NULL FROM slots WHERE starts_at > now() ORDER BY starts_at"
        ).fetchall()
    return render_template_string(PAGE, slots=slots, msg=request.args.get("msg"))


@app.post("/book/<int:slot_id>")
def book(slot_id: int):
    name, email = request.form.get("name", "").strip(), request.form.get("email", "").strip()
    if not name or not email:
        abort(400)
    with db() as conn:
        cur = conn.execute(
            "UPDATE slots SET name=%s, email=%s, booked_at=now() WHERE id=%s AND name IS NULL",
            (name[:80], email[:120], slot_id),
        )
    msg = "Sikeres foglalás." if cur.rowcount else "Ez az időpont már foglalt."
    return redirect(url_for("index", msg=msg))


@app.get("/admin")
def admin():
    if (r := require_admin()) is not None:
        return r
    with db() as conn:
        slots = conn.execute(
            "SELECT id, starts_at, name, email FROM slots WHERE name IS NOT NULL ORDER BY starts_at"
        ).fetchall()
    return render_template_string(ADMIN, slots=slots)


@app.post("/admin/cancel/<int:slot_id>")
def cancel(slot_id: int):
    if (r := require_admin()) is not None:
        return r
    with db() as conn:
        conn.execute("UPDATE slots SET name=NULL, email=NULL, booked_at=NULL WHERE id=%s", (slot_id,))
    return redirect(url_for("admin"))


@app.get("/healthz")
def healthz():
    with db() as conn:
        conn.execute("SELECT 1")
    return "ok"


init_db()
