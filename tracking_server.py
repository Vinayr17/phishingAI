import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import requests
from flask import Flask, Response, request
from pytz import timezone

# Datenbank-Pfad (lokal im Projektordner)
DB_PATH = Path(__file__).parent / "tracking.db"

app = Flask(__name__)


def init_db() -> None:
    """Erstellt die Tabelle, falls sie noch nicht existiert."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            browser TEXT,
            os TEXT,
            device TEXT,
            timestamp TEXT,
            link_type TEXT,
            scenario TEXT,
            template TEXT
        )
        """
    )
    # Neue Spalten hinzufügen, falls sie fehlen (Migration)
    cur.execute("PRAGMA table_info(clicks)")
    existing_cols = {row[1] for row in cur.fetchall()}
    for col in ["ip", "country", "region", "city"]:
        if col not in existing_cols:
            cur.execute(f"ALTER TABLE clicks ADD COLUMN {col} TEXT")
    conn.commit()
    conn.close()


def parse_user_agent(ua: str) -> Tuple[str, str, str]:
    """Verbesserte Heuristik für Browser, OS und Gerätetyp.
    
    WICHTIG: Prüfe spezifischere Browser ZUERST, da viele auf Chromium basieren
    und "chrome" im User-Agent enthalten.
    """
    ua_lower = ua.lower()

    # Browser (inkl. Mobile Apps)
    # WICHTIG: Reihenfolge ist wichtig! Spezifischere Browser zuerst prüfen.
    
    # Mobile Apps zuerst
    if "studo" in ua_lower or "studip" in ua_lower:
        browser = "Studo App"
    # Samsung Internet (muss VOR Chrome geprüft werden, da Chromium-basiert)
    elif "samsungbrowser" in ua_lower or "samsung internet" in ua_lower:
        browser = "Samsung Internet"
    # DuckDuckGo Browser (muss VOR Chrome geprüft werden, da Chromium-basiert)
    elif "duckduckgo" in ua_lower:
        browser = "DuckDuckGo"
    # Edge (enthält "chrome" im UA, muss VOR Chrome geprüft werden)
    elif "edg/" in ua_lower or ("edg" in ua_lower and "edge" not in ua_lower):
        browser = "Edge"
    # Opera (enthält "chrome" im UA, muss VOR Chrome geprüft werden)
    elif "opr/" in ua_lower or "opera" in ua_lower:
        browser = "Opera"
    # Brave Private VPN Webbrowser (enthält "chrome" im UA)
    elif "brave" in ua_lower:
        browser = "Brave Private VPN Webbrowser"
    # Vivaldi (enthält "chrome" im UA)
    elif "vivaldi" in ua_lower:
        browser = "Vivaldi"
    # Google Chrome (zuletzt, da viele andere Browser "chrome" enthalten)
    elif "chrome" in ua_lower and "edg" not in ua_lower and "opr" not in ua_lower:
        browser = "Google Chrome"
    # Mozilla Firefox
    elif "firefox" in ua_lower:
        browser = "Mozilla Firefox"
    # Safari (enthält KEIN "chrome" im UA)
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        browser = "Safari"
    else:
        browser = "Unknown"

    # OS
    if "windows" in ua_lower:
        os = "Windows"
    elif "mac os" in ua_lower or "macintosh" in ua_lower:
        os = "macOS"
    elif "linux" in ua_lower and "android" not in ua_lower:
        os = "Linux"
    elif "android" in ua_lower:
        os = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower or "ios" in ua_lower:
        os = "iOS"
    else:
        os = "Unknown"

    # Gerätetyp
    if "mobile" in ua_lower or "iphone" in ua_lower or "android" in ua_lower:
        device = "Mobile"
    elif "ipad" in ua_lower or "tablet" in ua_lower:
        device = "Tablet"
    else:
        device = "Desktop"

    return browser, os, device


def get_client_ip() -> Optional[str]:
    """Ermittelt die Client-IP unter Berücksichtigung von Proxies (Render setzt X-Forwarded-For)."""
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        # Erster Eintrag ist die Client-IP, Rest sind Proxies
        return xff.split(",")[0].strip()
    return request.remote_addr


def lookup_geo(ip: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Fragt eine Geo-IP API ab (nur grob: Land, Region, Stadt). Fehlertolerant."""
    if not ip:
        return None, None, None
    try:
        resp = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,regionName,city"},
            timeout=2.5,
        )
        data = resp.json()
        if data.get("status") != "success":
            return None, None, None
        return data.get("country"), data.get("regionName"), data.get("city")
    except Exception:
        return None, None, None


@app.route("/health")
def health() -> Response:
    return Response("ok", status=200)


def extract_name_from_email(email: str) -> str:
    """Extrahiert Name aus Email-Adresse (z.B. sophia.anthkowiak@gmail.com -> Sophia Anthkowiak)."""
    if not email or "@" not in email:
        return None
    
    # Nimm Teil vor @
    local_part = email.split("@")[0]
    
    # Entferne Zahlen und Sonderzeichen
    import re
    # Ersetze Punkte/Unterstriche durch Leerzeichen
    name_parts = re.sub(r'[._-]', ' ', local_part).split()
    
    # Entferne Zahlen
    name_parts = [p for p in name_parts if not p.isdigit()]
    
    if not name_parts:
        return None
    
    # Erste Buchstaben groß, Rest klein
    formatted_parts = [p.capitalize() for p in name_parts if p.isalpha()]
    
    if formatted_parts:
        return " ".join(formatted_parts)
    return None


@app.route("/track")
def track() -> Response:
    """Erfasst einen Klick und gibt eine 404-Seite zurück."""
    # URL-Parameter holen - nur Name und Email (rest wird automatisch erfasst)
    name = request.args.get("name") or None
    email = request.args.get("email") or None
    
    # Leere Strings zu None konvertieren
    if name == "":
        name = None
    if email == "":
        email = None
    
    # WICHTIG: Wenn Name fehlt, aber Email vorhanden ist, extrahiere Name aus Email
    if not name and email:
        extracted_name = extract_name_from_email(email)
        if extracted_name:
            name = extracted_name
            print(f"   💡 Name aus Email extrahiert: {email} -> {name}")

    # Automatisch erfasste Daten (aus User-Agent)
    ua = request.headers.get("User-Agent", "")
    browser, os, device = parse_user_agent(ua)
    # IP und Geo-Info ermitteln
    ip = get_client_ip()
    country, region, city = lookup_geo(ip or "")
    # Lokale Zeit (Deutschland) statt UTC verwenden
    berlin_tz = timezone('Europe/Berlin')
    timestamp = datetime.now(berlin_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    # Debug-Logging (in Konsole)
    print(f"\n[TRACKING] Klick erfasst:")
    print(f"  Name: {name}")
    print(f"  Email: {email}")
    print(f"  Browser: {browser}")
    print(f"  OS: {os}")
    print(f"  Device: {device}")
    print(f"  IP: {ip}")
    print(f"  Geo: {country}, {region}, {city}")
    print(f"  Zeit: {timestamp}")
    print(f"  User-Agent: {ua[:100]}...")  # Erste 100 Zeichen

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO clicks (name, email, browser, os, device, timestamp, link_type, scenario, template, ip, country, region, city)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            email,
            browser,
            os,
            device,
            timestamp,
            None,
            None,
            None,
            ip,
            country,
            region,
            city,
        ),  # Unnötige Felder = None
    )
    conn.commit()
    conn.close()

    # 404-Seite zurückgeben (bewusst "kaputt")
    html = """<!DOCTYPE html>
    <html><head><title>404 - Seite nicht gefunden</title></head>
    <body><h1>404 Error</h1><p>Die angeforderte Seite konnte nicht gefunden werden.</p></body></html>"""
    return Response(html, status=404, mimetype="text/html")


@app.route("/dashboard")
@app.route("/")
def dashboard() -> str:
    """Zeigt alle Klick-Daten als schöne HTML-Tabelle."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email, browser, os, device, timestamp, ip, country, region, city FROM clicks ORDER BY id DESC"
    )
    rows = cur.fetchall()
    conn.close()

    # HTML-Tabelle erstellen
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Tracking Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        th { background: #4CAF50; color: white; padding: 12px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #ddd; }
        tr:hover { background: #f9f9f9; }
        .stats { background: white; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-item { display: inline-block; margin-right: 30px; }
        .stat-number { font-size: 24px; font-weight: bold; color: #4CAF50; }
        .stat-label { color: #666; font-size: 14px; }
        a { color: #4CAF50; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>📊 Tracking Dashboard</h1>
    <div class="stats">
        <div class="stat-item">
            <div class="stat-number">""" + str(len(rows)) + """</div>
            <div class="stat-label">Gesamt Klicks</div>
        </div>
        <div class="stat-item">
            <a href="/export.csv">📥 CSV Export</a>
        </div>
    </div>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Browser</th>
                <th>OS</th>
                <th>Gerät</th>
                <th>Zeitstempel</th>
                <th>IP</th>
                <th>Land</th>
                <th>Region</th>
                <th>Stadt</th>
            </tr>
        </thead>
        <tbody>"""

    if rows:
        for r in rows:
            html += f"""
            <tr>
                <td>{r[0]}</td>
                <td>{r[1] or '-'}</td>
                <td>{r[2] or '-'}</td>
                <td>{r[3] or '-'}</td>
                <td>{r[4] or '-'}</td>
                <td>{r[5] or '-'}</td>
                <td>{r[6] or '-'}</td>
                <td>{r[7] or '-'}</td>
                <td>{r[8] or '-'}</td>
                <td>{r[9] or '-'}</td>
                <td>{r[10] or '-'}</td>
            </tr>"""
    else:
        html += """
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: #999;">
                    Noch keine Daten vorhanden. Klicke auf einen Tracking-Link, um Daten zu sammeln.
                </td>
            </tr>"""

    html += """
        </tbody>
    </table>
</body>
</html>"""

    return html


@app.route("/export.csv")
def export_csv() -> Response:
    """Exportiert alle Klick-Daten als CSV."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email, browser, os, device, timestamp, ip, country, region, city FROM clicks ORDER BY id ASC"
    )
    rows = cur.fetchall()
    conn.close()

    header = "id,name,email,browser,os,device,timestamp,ip,country,region,city"
    lines = [header]
    def esc(val: str) -> str:
        # Doppelte Anführungszeichen im CSV verdoppeln
        return (val or "").replace('"', '""')

    for r in rows:
        line = ",".join(
            [
                str(r[0]),
                f'"{esc(r[1])}"',
                f'"{esc(r[2])}"',
                f'"{esc(r[3])}"',
                f'"{esc(r[4])}"',
                f'"{esc(r[5])}"',
                f'"{esc(r[6])}"',
            ]
        )
        lines.append(line)

    csv_content = "\n".join(lines)
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=clicks.csv"},
    )


init_db()

if __name__ == "__main__":
    import os
    # Für Deployment: Nutze PORT Environment Variable (Railway/Render setzen diese)
    port = int(os.environ.get('PORT', 5000))
    # Debug nur lokal, nicht in Production
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host="0.0.0.0", port=port, debug=debug)

