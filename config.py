"""
Zentrale Konfiguration für das Tracking-System.

TRACKING_URL: Basis-URL deines Tracking-Servers (online oder lokal).
Beispiele:
- Lokal:    "http://localhost:5000/track"
- Online:   "https://dein-tracking-service.example.com/track"

TRACKING_DISPLAY_TEXT: Der sichtbare Text des Links in der Email.
"""

# TODO: Anpassen, sobald der Tracking-Server bereitsteht.
# Für lokale Tests auf Handy (im gleichen WLAN): Nutze deine lokale IP
# Für echtes Experiment: Später online deployen (Railway/Render)
TRACKING_URL = "http://172.21.89.58:5000/track"  # Lokale IP für Tests
# TRACKING_URL = "http://localhost:5000/track"  # Nur für PC-Tests

# Sichtbarer Text in der Email für den Tracking-Link.
TRACKING_DISPLAY_TEXT = "moodle.uni-hamburg.de/dokument"

