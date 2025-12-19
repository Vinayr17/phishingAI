"""
Zentrale Konfiguration für das Tracking-System.

TRACKING_URL: Basis-URL deines Tracking-Servers (online oder lokal).
Beispiele:
- Lokal:    "http://localhost:5000/track"
- Online:   "https://dein-tracking-service.example.com/track"

TRACKING_DISPLAY_TEXT: Der sichtbare Text des Links in der Email.
"""

# Tracking-Link (direkt auf Render, leitet dann zu Cloudflare Pages weiter)
TRACKING_URL = "https://phishingai.onrender.com/track"
# TRACKING_URL = "https://bit.ly/4rWbnuc"  # Bitly-Shortlink (auskommentiert, da Parameter-Probleme)
# TRACKING_URL = "http://172.21.89.58:5000/track"         # Lokale IP für Tests (auskommentiert)
# TRACKING_URL = "http://localhost:5000/track"            # Nur für PC-Tests (auskommentiert)

# Sichtbarer Text in der Email für den Tracking-Link.
TRACKING_DISPLAY_TEXT = "lecture2go.uni-hamburg.de/materials/genai-business"

# Redirect-URL nach dem Tracking (optional)
# Wenn gesetzt, wird der Nutzer nach dem Track sofort hierhin weitergeleitet.
# Dadurch sieht man die Render-URL nicht mehr in der Adressleiste.
REDIRECT_URL = "https://evasys.pages.dev"

