import os
import uuid
import sqlite3
import datetime
import mimetypes
import json
import logging
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# Config & App
# -----------------------------
app = Flask(__name__)

DB = os.getenv("DB_PATH", "data.db")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")  # WhatsApp Business phone number ID (string)
OWNER_WA_NUMBER = os.getenv("OWNER_WA_NUMBER")      # e.g., 91XXXXXXXXXX (without +)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "replace_me")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

# API endpoints for WhatsApp Cloud API
if WHATSAPP_PHONE_ID:
    MEDIA_UPLOAD_URL = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_ID}/media"
    MESSAGES_URL = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_ID}/messages"
else:
    # set placeholders; app will error if you actually call WA without setting the envs
    MEDIA_UPLOAD_URL = ""
    MESSAGES_URL = ""


# -----------------------------
# DB setup
# -----------------------------
def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DB)

def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS approvals (
            id TEXT PRIMARY KEY,
            invoice_id TEXT,
            biller_id TEXT,
            machine_id TEXT,
            admin_url TEXT,
            status TEXT,
            created_at TEXT,
            consumed INTEGER DEFAULT 0
        )
        """
    )
    con.commit()
    con.close()


init_db()


# -----------------------------
# WhatsApp helpers
# -----------------------------
def wa_headers():
    return {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    }


def wa_send_text(text: str, to: str = None):
    to = to or OWNER_WA_NUMBER
    if not (WHATSAPP_TOKEN and WHATSAPP_PHONE_ID and to):
        raise RuntimeError("WhatsApp env vars missing (TOKEN/PHONE_ID/OWNER_WA_NUMBER)")
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    r = requests.post(MESSAGES_URL, headers={**wa_headers(), "Content-Type": "application/json"}, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


def wa_send_buttons(text: str, action_id: str, to: str = None):
    to = to or OWNER_WA_NUMBER
    if not (WHATSAPP_TOKEN and WHATSAPP_PHONE_ID and to):
        raise RuntimeError("WhatsApp env vars missing (TOKEN/PHONE_ID/OWNER_WA_NUMBER)")
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": f"yes_{action_id}", "title": "YES"}},
                    {"type": "reply", "reply": {"id": f"no_{action_id}", "title": "NO"}},
                ]
            },
        },
    }
    r = requests.post(MESSAGES_URL, headers={**wa_headers(), "Content-Type": "application/json"}, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


def wa_upload_media(file_path: str, mime: str = None):
    if not (WHATSAPP_TOKEN and WHATSAPP_PHONE_ID):
        raise RuntimeError("WhatsApp env vars missing (TOKEN/PHONE_ID)")
    mime = mime or mimetypes.guess_type(file_path)[0] or "video/mp4"
    files = {
        "file": (os.path.basename(file_path), open(file_path, "rb"), mime),
        "messaging_product": (None, "whatsapp"),
    }
    r = requests.post(MEDIA_UPLOAD_URL, headers=wa_headers(), files=files, timeout=90)
    r.raise_for_status()
    return r.json()["id"]


def wa_send_media(media_id: str, caption: str, to: str = None):
    to = to or OWNER_WA_NUMBER
    if not (WHATSAPP_TOKEN and WHATSAPP_PHONE_ID and to):
        raise RuntimeError("WhatsApp env vars missing (TOKEN/PHONE_ID/OWNER_WA_NUMBER)")
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "video",
        "video": {"id": media_id, "caption": caption[:1024]},
    }
    r = requests.post(MESSAGES_URL, headers={**wa_headers(), "Content-Type": "application/json"}, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def root():
    return {"ok": True, "service": "zorder-backend", "version": "1.1.0"}


@app.get("/healthz")
def healthz():
    return "ok"


@app.post("/event/bill-edited")
def bill_edited():
    data = request.get_json(force=True)
    for k in ("invoice_id", "biller_id", "machine_id"):
        if k not in data:
            return {"error": f"missing {k}"}, 400

    admin_url = data.get("admin_url", "")
    action_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.UTC).isoformat() + "Z"

    logger.info(f"Processing bill edit request: invoice={data['invoice_id']}, biller={data['biller_id']}, machine={data['machine_id']}")

    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO approvals (id, invoice_id, biller_id, machine_id, admin_url, status, created_at) VALUES (?,?,?,?,?,?,?)",
        (action_id, data["invoice_id"], data["biller_id"], data["machine_id"], admin_url, "pending", now),
    )
    con.commit()
    con.close()

    text = (
        f"Biller {data['biller_id']} ne bill {data['invoice_id']} edit kiya.\n"
        f"Auto-login + 3 min screen recording allow karen?"
    )

    try:
        wa_send_buttons(text, action_id)
    except Exception as e:
        return {"error": "whatsapp_send_failed", "details": str(e)}, 500

    return {"ok": True, "action_id": action_id}


# WhatsApp webhook verification (GET)
@app.get("/webhook/whatsapp")
def verify_webhook():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Forbidden", 403


# WhatsApp webhook receiver (POST)
@app.post("/webhook/whatsapp")
def whatsapp_webhook():
    payload = request.get_json(force=True)
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    if msg.get("type") == "interactive":
                        reply = msg["interactive"].get("button_reply") or {}
                        rid = reply.get("id", "")
                        if not rid:
                            continue
                        status = None
                        if rid.startswith("yes_"):
                            status = "allowed"
                        elif rid.startswith("no_"):
                            status = "denied"
                        if status is None:
                            continue
                        action_id = rid.split("_", 1)[1]
                        con = sqlite3.connect(DB)
                        cur = con.cursor()
                        cur.execute("UPDATE approvals SET status=? WHERE id=?", (status, action_id))
                        con.commit()
                        con.close()
                        if status == "denied":
                            try:
                                wa_send_text("❌ Request rejected. Agent will not run.")
                            except Exception:
                                pass
                        else:
                            try:
                                wa_send_text("✅ Approved. Agent armed for next login (F5/F6).")
                            except Exception:
                                pass
    except Exception as e:
        print("webhook parse error:", e)
    return "ok"


@app.get("/tasks/<machine_id>")
def tasks(machine_id):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(
        "SELECT id, invoice_id, biller_id, admin_url, status FROM approvals "
        "WHERE machine_id=? AND status='allowed' AND consumed=0 ORDER BY created_at DESC LIMIT 10",
        (machine_id,),
    )
    rows = cur.fetchall()
    con.close()
    return jsonify([
        {"id": r[0], "invoice_id": r[1], "biller_id": r[2], "admin_url": r[3], "status": r[4]} for r in rows
    ])


@app.post("/tasks/consume")
def consume():
    data = request.get_json(force=True)
    action_id = data.get("id")
    if not action_id:
        return {"error": "missing id"}, 400
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("UPDATE approvals SET consumed=1 WHERE id=?", (action_id,))
    con.commit()
    con.close()
    return {"ok": True}


@app.post("/upload/recording")
def upload_recording():
    # Agent sends: multipart form with 'file' (mp4) and 'meta' (json string)
    if "file" not in request.files:
        return {"error": "file missing"}, 400

    f = request.files["file"]
    meta_raw = request.form.get("meta", "{}")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(UPLOAD_DIR, f.filename)
    f.save(save_path)

    # Prepare caption from meta (shortened)
    try:
        meta = json.loads(meta_raw)
    except Exception:
        meta = {"meta": meta_raw}

    caption_parts = []
    for key in ("invoice_id", "machine_id", "host", "ip", "time"):
        if key in meta:
            caption_parts.append(f"{key}: {meta[key]}")
    caption = " | ".join(caption_parts) or "Recording"

    try:
        media_id = wa_upload_media(save_path, mime="video/mp4")
        wa_send_media(media_id, caption)
        return {"ok": True}
    except Exception as e:
        return {"error": "whatsapp_media_failed", "details": str(e)}, 500


@app.route("/agent/arm-status/<machine_id>", methods=["GET"])
def agent_arm_status(machine_id):
    """Check if agent is armed for the given machine."""
    try:
        # Check if there's an active approval for this machine
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Look for pending approvals for this machine
        cursor.execute("""
            SELECT id, status, created_at, consumed
            FROM approvals 
            WHERE machine_id = ? AND status = 'allowed' AND consumed = 0
            ORDER BY created_at DESC 
            LIMIT 1
        """, (machine_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "armed": True,
                "action_id": result[0],
                "created_at": result[2],
                "machine_id": machine_id
            }
        else:
            return {
                "armed": False,
                "machine_id": machine_id
            }
            
    except Exception as e:
        return {"error": "arm_status_failed", "details": str(e)}, 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return {"error": "endpoint not found"}, 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return {"error": "internal server error"}, 500


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    logger.info("Starting Zorder Backend Server v1.1.0")
    logger.info(f"Database: {DB}")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    logger.info(f"WhatsApp configured: {bool(WHATSAPP_TOKEN and WHATSAPP_PHONE_ID)}")
    
    # In dev, enable debug; in prod, run behind a real WSGI server (gunicorn/uwsgi) + HTTPS reverse proxy
    app.run(host="0.0.0.0", port=8000, debug=True)
