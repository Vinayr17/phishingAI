"""
Zentrale Konfiguration für das Tracking-System.

TRACKING_URL: Basis-URL deines Tracking-Servers (online oder lokal).
Beispiele:
- Lokal:    "http://localhost:5000/track"
- Online:   "https://dein-tracking-service.example.com/track"

TRACKING_DISPLAY_TEXT: Der sichtbare Text des Links in der Email.
"""

# Tracking-Link (aktuell Bitly-Shortlink, leitet auf Render-Track-Endpoint weiter)
# Wenn du den Shortlink ändern willst, passe nur diese Zeile an.
TRACKING_URL = "https://bit.ly/4rWbnuc"
# TRACKING_URL = "https://phishingai.onrender.com/track"  # Online auf Render
# TRACKING_URL = "http://172.21.89.58:5000/track"         # Lokale IP für Tests (auskommentiert)
# TRACKING_URL = "http://localhost:5000/track"            # Nur für PC-Tests (auskommentiert)

# Sichtbarer Text in der Email für den Tracking-Link.
TRACKING_DISPLAY_TEXT = "moodle.uni-hamburg.de/dokument"

