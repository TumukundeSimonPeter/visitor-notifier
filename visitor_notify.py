import smtplib
import os
import threading
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# --- Config (set these in Render environment variables) ---
SMTP_EMAIL = os.environ.get("SMTP_EMAIL")       # your Gmail address
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD") # Gmail App Password
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL")   # where to send alerts (can be same as SMTP_EMAIL)


def send_notification(ip, path, user_agent, time):
    """Send an email notification about a new visitor."""
    subject = f"👁️ New Visitor on Your Website"

    body = f"""
    <h2>Someone just visited your website!</h2>
    <table border="0" cellpadding="10" cellspacing="0" style="font-family: sans-serif; border-collapse: collapse;">
        <tr style="background: #f8fafc;"><td style="font-weight: bold; color: #6366f1;">Time:</td><td>{time}</td></tr>
        <tr><td style="font-weight: bold; color: #6366f1;">IP Address:</td><td><code>{ip}</code></td></tr>
        <tr style="background: #f8fafc;"><td style="font-weight: bold; color: #6366f1;">Page Visited:</td><td><code>{path}</code></td></tr>
        <tr><td style="font-weight: bold; color: #6366f1;">Device:</td><td style="font-size: 12px; color: #64748b;">{user_agent}</td></tr>
    </table>
    <p style="margin-top: 20px; color: #94a3b8; font-size: 12px;">Sent by Visitor Notify</p>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = NOTIFY_EMAIL
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, NOTIFY_EMAIL, msg.as_string())
            print(f"[✓] Notification sent for visitor from {ip}")
    except Exception as e:
        print(f"[✗] Failed to send email: {e}")


def send_notification_async(ip, path, user_agent, time):
    """Run send_notification in a background thread so the user doesn't wait."""
    thread = threading.Thread(target=send_notification, args=(ip, path, user_agent, time))
    thread.start()


@app.before_request
def notify_on_visit():
    """Fires before every request — captures visitor info and sends email."""
    # Skip favicon, static files, and internal health checks
    if request.path == "/favicon.ico" or request.path.startswith("/internal") or request.path.startswith("/static"):
        return

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    path = request.path
    user_agent = request.headers.get("User-Agent", "Unknown")
    time = datetime.utcnow().strftime("%H:%M:%S UTC on %d %b %Y")

    send_notification_async(ip, path, user_agent, time)


@app.route("/")
def home():
    """A beautiful landing page for your visitor notifier service."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Visitor Notify | Insight Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --accent: #6366f1;
                --bg: #0f172a;
                --card-bg: rgba(30, 41, 59, 0.7);
            }
            body {
                margin: 0;
                padding: 0;
                font-family: 'Outfit', sans-serif;
                background: radial-gradient(circle at top right, #1e1b4b, #0f172a);
                color: #f8fafc;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                overflow: hidden;
            }
            .container {
                background: var(--card-bg);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 3rem;
                border-radius: 24px;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                max-width: 500px;
                text-align: center;
                animation: fadeIn 0.8s ease-out;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            h1 { font-size: 2.5rem; margin-bottom: 1rem; font-weight: 600; color: #fff; }
            p { font-size: 1.1rem; color: #94a3b8; line-height: 1.6; }
            .status-badge {
                display: inline-block;
                padding: 0.5rem 1rem;
                background: rgba(34, 197, 94, 0.2);
                color: #4ade80;
                border-radius: 99px;
                font-size: 0.875rem;
                margin-bottom: 2rem;
                font-weight: 600;
                border: 1px solid rgba(34, 197, 94, 0.3);
            }
            .code-block {
                background: #020617;
                padding: 1.5rem;
                border-radius: 12px;
                text-align: left;
                margin-top: 2rem;
                position: relative;
            }
            code { color: #818cf8; font-family: monospace; font-size: 0.8rem; word-break: break-all; }
            .label { color: #475569; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 0.5rem; letter-spacing: 1px; }
            .hint { font-size: 0.8rem; color: #475569; margin-top: 1rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="status-badge">● SERVICE ONLINE</div>
            <h1>Visitor Notify</h1>
            <p>Your invisible visitor tracking is active. Add the following pixel to your website to start receiving alerts.</p>
            
            <div class="code-block">
                <div class="label">Embed Tag (HTML)</div>
                <code>&lt;img src="https://your-app.render.com/pixel.png" style="display:none"&gt;</code>
            </div>
            <div class="hint">Replace <b>your-app.render.com</b> with your actual hosted URL once deployed.</div>
        </div>
    </body>
    </html>
    """


@app.route("/pixel.png")
def tracking_pixel():
    """Serves a 1x1 transparent PNG pixel to track visitors from other sites."""
    # This is a base64 encoded 1x1 transparent PNG
    pixel_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    return pixel_data, 200, {"Content-Type": "image/png"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
