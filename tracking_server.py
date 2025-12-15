import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import requests
from flask import Flask, Response, request, redirect
from pytz import timezone

# Importiere Redirect-URL aus config (optional)
try:
    from config import REDIRECT_URL
except ImportError:
    REDIRECT_URL = None

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
    # Neue Geo-Spalten (werden bei Bedarf ergänzt)
    for col in ["ip", "country", "region", "city", "zip_code", "isp"]:
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


def lookup_geo(ip: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Fragt eine Geo-IP API ab (Land, Region, Stadt, PLZ, ISP). Fehlertolerant."""
    if not ip:
        return None, None, None, None, None
    try:
        resp = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,regionName,city,zip,isp"},
            timeout=2.5,
        )
        data = resp.json()
        if data.get("status") != "success":
            return None, None, None, None, None
        return (
            data.get("country"),
            data.get("regionName"),
            data.get("city"),
            data.get("zip"),
            data.get("isp"),
        )
    except Exception:
        return None, None, None, None, None


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
    
    # Debug: Zeige alle ankommenden Parameter
    print(f"\n[DEBUG] Ankommende URL-Parameter:")
    print(f"  request.args: {dict(request.args)}")
    print(f"  name (raw): {request.args.get('name')}")
    print(f"  email (raw): {request.args.get('email')}")
    
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
    # IP und Geo-Info ermitteln (inkl. ISP & PLZ)
    ip = get_client_ip()
    country, region, city, zip_code, isp = lookup_geo(ip or "")
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
    print(f"  Geo: {country}, {region}, {city}, PLZ: {zip_code}")
    print(f"  ISP: {isp}")
    print(f"  Zeit: {timestamp}")
    print(f"  User-Agent: {ua[:100]}...")  # Erste 100 Zeichen

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO clicks (name, email, browser, os, device, timestamp, link_type, scenario, template, ip, country, region, city, zip_code, isp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                zip_code,
                isp,
            ),  # Unnötige Felder = None
        )
        conn.commit()
        conn.close()
    except sqlite3.OperationalError as e:
        # Falls Spalten fehlen, versuche Migration und dann Fallback
        print(f"  ⚠️ Datenbank-Fehler: {e}")
        print(f"  🔄 Versuche Migration...")
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(clicks)")
            existing_cols = {row[1] for row in cur.fetchall()}
            for col in ["ip", "country", "region", "city", "zip_code", "isp"]:
                if col not in existing_cols:
                    cur.execute(f"ALTER TABLE clicks ADD COLUMN {col} TEXT")
            conn.commit()
            conn.close()
            print(f"  ✅ Migration erfolgreich, versuche erneut...")
            # Erneut versuchen
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO clicks (name, email, browser, os, device, timestamp, link_type, scenario, template, ip, country, region, city, zip_code, isp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    zip_code,
                    isp,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e2:
            print(f"  ❌ Migration fehlgeschlagen: {e2}")
            # Fallback: Nur alte Spalten verwenden (ohne neue Geo-Daten)
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO clicks (name, email, browser, os, device, timestamp, link_type, scenario, template, ip, country, region, city)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, email, browser, os, device, timestamp, None, None, None, ip, country, region, city),
            )
            conn.commit()
            conn.close()
            print(f"  ⚠️ Fallback: Nur alte Spalten verwendet")
    except Exception as e:
        print(f"  ❌ Unerwarteter Fehler beim Speichern: {e}")
        import traceback
        traceback.print_exc()

    # Redirect auf Decoy-URL, falls konfiguriert (versteckt Render-URL in Millisekunden)
    if REDIRECT_URL and REDIRECT_URL.strip():
        print(f"  🔀 Redirect zu: {REDIRECT_URL}")
        return redirect(REDIRECT_URL, code=302)  # 302 = temporärer Redirect (sehr schnell)
    
    # Sonst: 404-Seite zurückgeben (bewusst "kaputt")
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
        "SELECT id, name, email, browser, os, device, timestamp, ip, country, region, city, zip_code, isp FROM clicks ORDER BY id DESC"
    )
    rows = cur.fetchall()
    conn.close()

    # Statistiken berechnen
    browsers = {}
    os_list = {}
    devices = {}
    countries = {}
    for r in rows:
        browser = r[3] or 'Unknown'
        os = r[4] or 'Unknown'
        device = r[5] or 'Unknown'
        country = r[8] or 'Unknown'
        browsers[browser] = browsers.get(browser, 0) + 1
        os_list[os] = os_list.get(os, 0) + 1
        devices[device] = devices.get(device, 0) + 1
        countries[country] = countries.get(country, 0) + 1
    
    # Browser-Icons Mapping
    browser_icons = {
        'Google Chrome': '🌐',
        'Mozilla Firefox': '🦊',
        'Safari': '🧭',
        'Edge': '🔷',
        'Opera': '🎭',
        'Brave Private VPN Webbrowser': '🛡️',
        'Samsung Internet': '📱',
        'DuckDuckGo': '🦆',
        'Studo App': '📚',
    }
    
    # OS-Icons Mapping
    os_icons = {
        'Windows': '🪟',
        'macOS': '🍎',
        'Linux': '🐧',
        'Android': '🤖',
        'iOS': '📱',
    }
    
    # Device-Icons Mapping
    device_icons = {
        'Desktop': '💻',
        'Mobile': '📱',
        'Tablet': '📲',
    }
    
    # HTML-Tabelle erstellen (Dark Mode + Tech Style)
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Tracking Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #e0e0e0;
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { 
            color: #00d4ff;
            font-size: 32px;
            margin-bottom: 30px;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
            font-weight: 600;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid rgba(0, 212, 255, 0.2);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 20px rgba(0, 212, 255, 0.3);
            border-color: rgba(0, 212, 255, 0.4);
        }
        .stat-number {
            font-size: 36px;
            font-weight: 700;
            color: #00d4ff;
            font-family: 'Courier New', monospace;
            margin-bottom: 5px;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }
        .stat-label {
            color: #a0a0a0;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .export-btn {
            display: inline-block;
            background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
            color: #0a0a0a;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 10px rgba(0, 212, 255, 0.3);
        }
        .export-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0, 212, 255, 0.5);
        }
        .table-wrapper {
            background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(0, 212, 255, 0.2);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        th {
            background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
            color: #0a0a0a;
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 1px;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid rgba(0, 212, 255, 0.1);
            color: #e0e0e0;
        }
        tr:hover {
            background: rgba(0, 212, 255, 0.1);
            transition: background 0.2s;
        }
        .icon {
            font-size: 18px;
            margin-right: 6px;
            vertical-align: middle;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            background: rgba(0, 212, 255, 0.2);
            color: #00d4ff;
            border: 1px solid rgba(0, 212, 255, 0.3);
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }
        .empty-state-icon {
            font-size: 64px;
            margin-bottom: 20px;
            opacity: 0.3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ Tracking Dashboard</h1>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">""" + str(len(rows)) + """</div>
                <div class="stat-label">Gesamt Klicks</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">""" + str(len(browsers)) + """</div>
                <div class="stat-label">Browser Typen</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">""" + str(len(os_list)) + """</div>
                <div class="stat-label">Betriebssysteme</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">""" + str(len(countries)) + """</div>
                <div class="stat-label">Länder</div>
            </div>
            <div class="stat-card" style="display: flex; align-items: center; justify-content: center;">
                <a href="/export.csv" class="export-btn">📥 CSV Export</a>
            </div>
        </div>
        <div class="table-wrapper">
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
                        <th>PLZ</th>
                        <th>ISP</th>
                    </tr>
                </thead>
                <tbody>"""

    if rows:
        for r in rows:
            browser = r[3] or 'Unknown'
            os = r[4] or 'Unknown'
            device = r[5] or 'Unknown'
            browser_icon = browser_icons.get(browser, '🌐')
            os_icon = os_icons.get(os, '💻')
            device_icon = device_icons.get(device, '📱')
            html += f"""
            <tr>
                <td><span class="badge">#{r[0]}</span></td>
                <td>{r[1] or '<span style="color: #666;">-</span>'}</td>
                <td>{r[2] or '<span style="color: #666;">-</span>'}</td>
                <td><span class="icon">{browser_icon}</span>{browser}</td>
                <td><span class="icon">{os_icon}</span>{os}</td>
                <td><span class="icon">{device_icon}</span>{device}</td>
                <td style="font-family: 'Courier New', monospace; color: #00d4ff;">{r[6] or '-'}</td>
                <td style="font-family: 'Courier New', monospace; color: #a0a0a0;">{r[7] or '<span style="color: #666;">-</span>'}</td>
                <td>{r[8] or '<span style="color: #666;">-</span>'}</td>
                <td>{r[9] or '<span style="color: #666;">-</span>'}</td>
                <td>{r[10] or '<span style="color: #666;">-</span>'}</td>
                <td>{r[11] or '<span style="color: #666;">-</span>'}</td>
                <td>{r[12] or '<span style="color: #666;">-</span>'}</td>
            </tr>"""
    else:
        html += """
            <tr>
                <td colspan="12" class="empty-state">
                    <div class="empty-state-icon">📊</div>
                    <div style="font-size: 18px; margin-bottom: 10px; color: #a0a0a0;">Noch keine Daten vorhanden</div>
                    <div style="color: #666;">Klicke auf einen Tracking-Link, um Daten zu sammeln.</div>
                </td>
            </tr>"""

    html += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""

    return html


@app.route("/export.csv")
def export_csv() -> Response:
    """Exportiert alle Klick-Daten als CSV."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email, browser, os, device, timestamp, ip, country, region, city, zip_code, isp FROM clicks ORDER BY id ASC"
    )
    rows = cur.fetchall()
    conn.close()

    header = "id,name,email,browser,os,device,timestamp,ip,country,region,city,zip_code,isp"
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
                f'"{esc(r[7])}"',
                f'"{esc(r[8])}"',
                f'"{esc(r[9])}"',
                f'"{esc(r[10])}"',
                f'"{esc(r[11])}"',
                f'"{esc(r[12])}"',
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

