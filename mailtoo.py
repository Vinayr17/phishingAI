"""
MailTool - Einfache Menü-App für dein Projekt

Funktionen:
- Generate: Einzelne Email erzeugen (Freitext oder Formular)
- Batch: Mehrere Emails aus CSV
- Extract: HTML/EML → Template (mit Bild-Download)
- Send: HTML versenden (Dry-Run/SMTP)

Start:
  python mailtool.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from generate_phishing import (
    generate_complete_phishing_email,
    combine_with_template,
)

# Tracking-Konfiguration (URL & Link-Text)
try:
    from config import TRACKING_URL, TRACKING_DISPLAY_TEXT
except Exception:
    TRACKING_URL = None
    TRACKING_DISPLAY_TEXT = "moodle.uni-hamburg.de/dokument"

ROOT = Path(__file__).parent
TEMPLATES = {
    "tutor": ROOT / "email_templates" / "tutor_template.html",
    "professional": ROOT / "email_templates" / "professional_template.html",
    "university_style": ROOT / "email_templates" / "university_style_template.html",
}


def cls() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def ask(prompt: str, default: str = "") -> str:
    val = input(f"{prompt}{' ['+default+']' if default else ''}: ").strip()
    return val or default


def ask_multiline(prompt: str, end_marker: str = "END") -> str:
    """
    Fragt nach mehrzeiligem Text mit Möglichkeit zur Korrektur.
    Nutzer kann den gesamten Text eingeben und bearbeiten, bevor er mit END abschließt.
    """
    print(f"{prompt}\n(Beende mit einer neuen Zeile nur mit '{end_marker}'):\n")
    print("💡 Tipp: Du kannst den gesamten Text eingeben und bearbeiten.")
    print("   Wenn du fertig bist, gib '" + end_marker + "' in eine neue Zeile ein.\n")
    
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == end_marker:
            break
        lines.append(line)
    
    # Zeige den eingegebenen Text und frage ob korrekt
    if lines:
        while True:  # Wiederhole bis Nutzer zufrieden ist
            print("\n📝 Dein eingegebener Text:")
            print("-" * 50)
            for i, line in enumerate(lines, 1):
                print(f"{i:2d} | {line}")
            print("-" * 50)
            correct = ask("\nIst der Text korrekt? (Enter=Ja, n=Nein zum Bearbeiten, z=Zeile ändern)", "y").lower()
            
            if correct.startswith("z") or correct == "zeile":
                # Erlaube Bearbeitung einzelner Zeilen
                try:
                    line_num = int(ask("Welche Zeile möchtest du ändern? (Nummer)", ""))
                    if 1 <= line_num <= len(lines):
                        print(f"\nAktuelle Zeile {line_num}: {lines[line_num - 1]}")
                        new_line = ask(f"Neue Zeile {line_num} (Enter = unverändert lassen)", lines[line_num - 1])
                        if new_line.strip() or new_line == "":
                            lines[line_num - 1] = new_line
                        continue
                    else:
                        print(f"   ⚠️ Ungültige Zeilennummer (1-{len(lines)})")
                        continue
                except ValueError:
                    print("   ⚠️ Bitte gib eine Zahl ein")
                    continue
            elif correct.startswith("n"):
                # Erlaube komplette Neu-Eingabe
                print("\n💡 Du kannst jetzt den Text nochmal komplett eingeben:")
                new_text = ask_multiline("Neuer Text", end_marker)
                if new_text.strip():
                    return new_text
                continue
            else:
                # Text ist korrekt
                break
    
    return "\n".join(lines)


def detect_from_text(text: str) -> dict:
    """Verbesserte Heuristik für Freitext-Befehle.

    Beispieleingabe:
      "Uni HH style, Thema Projekt bis 25.12, an Steven Mölle"
      "Prüfung am 29.11 fällt aus, an Steven Laddach, Uni HH style"
      "Von Prof. Dr. Kay Nöth aus der Marketing fakultät, Prüfung am 29.11 fällt aus, an Steven Laddach"
    """
    original_text = text
    lower = text.lower()

    # Template (besser erkennen)
    template = "professional"
    if "uni" in lower and ("hamburg" in lower or "hh" in lower or "hamburg style" in lower or "design" in lower):
        template = "uni_hh"  # Wird intern zu "tutor" gemappt
    elif "university_style" in lower or "university style" in lower:
        template = "university_style"

    # Absender-E-Mail erkennen (ZUERST, um später Name zu extrahieren)
    email = None
    email_match = re.search(r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", text, re.IGNORECASE)
    if email_match:
        email = email_match.group(1)
    
    # Absender erkennen (mehrere Patterns)
    sender_name = "Prof. Dr. Michael Schmidt"  # Default
    # Pattern 1: "von Prof. Dr. ..."
    sender_match = re.search(r"von\s+(Prof\.?\s*Dr\.?\s+[A-ZÄÖÜ][a-zäöüß\-]+\s+[A-ZÄÖÜ][a-zäöüß\-]+)", text, re.IGNORECASE)
    if sender_match:
        sender_name = sender_match.group(1)
    else:
        # Pattern 2: "Absender ist Prof. Dr. ..."
        sender_match = re.search(r"absender\s+ist\s+(Prof\.?\s*Dr\.?\s+[A-ZÄÖÜ][a-zäöüß\-]+\s+[A-ZÄÖÜ][a-zäöüß\-]+)", text, re.IGNORECASE)
        if sender_match:
            sender_name = sender_match.group(1)
        else:
            # Pattern 3: "Der Absender ist ..."
            sender_match = re.search(r"der\s+absender\s+ist\s+(Prof\.?\s*Dr\.?\s+[A-ZÄÖÜ][a-zäöüß\-]+\s+[A-ZÄÖÜ][a-zäöüß\-]+)", text, re.IGNORECASE)
            if sender_match:
                sender_name = sender_match.group(1)
            elif email:
                # Pattern 4: Name aus E-Mail-Adresse extrahieren (z.B. clemens.klemens@uni-hamburg.de -> Prof. Dr. Clemens Klemens)
                email_local = email.split("@")[0]
                if "." in email_local:
                    parts = email_local.split(".")
                    if len(parts) >= 2:
                        first_name = parts[0].capitalize()
                        last_name = parts[1].capitalize()
                        sender_name = f"Prof. Dr. {first_name} {last_name}"

    # Lehrstuhl/Fakultät erkennen (auch in Klammern!)
    position = None
    # Suche explizit nach Fakultät-Namen in Klammern: "(Marketing)"
    faculty_match = re.search(r"\(([A-ZÄÖÜa-zäöüß\s\-]+)\)", text)
    if faculty_match:
        faculty_name = faculty_match.group(1).strip()
        if faculty_name.lower() in ["marketing", "informatik", "mathematik", "physik", "jura", "medizin"]:
            position = f"Lehrstuhl für {faculty_name.capitalize()}"
    
    # Falls nicht gefunden, suche im ganzen Text
    if not position:
        if "marketing" in lower:
            position = "Lehrstuhl für Marketing"
        elif "informatik" in lower:
            position = "Fakultät für Informatik"
        elif "wirtschaft" in lower or "business" in lower:
            position = "University of Hamburg Business School"
        else:
            position = "Lehrstuhl für IT-Sicherheit und KI"  # Default


    # Website erkennen
    website = None
    if "keine website" in lower or "keine eigene website" in lower:
        website = None
    else:
        website_match = re.search(r"https?://[^\s,]+", text, re.IGNORECASE)
        if website_match:
            website = website_match.group(0).rstrip('.",)')

    # Empfänger-Name (mehrere Patterns)
    name = "Max Müller"  # Default
    # Pattern 1: "an Studierende" oder "an Studenten" oder "an [Name]"
    if re.search(r"\ban\s+studierende\b", text, re.IGNORECASE):
        name = "Studierende"
    elif re.search(r"\ban\s+studenten\b", text, re.IGNORECASE):
        name = "Studierende"
    elif re.search(r"\ban\s+alle\b", text, re.IGNORECASE):
        name = "Studierende"
    else:
        # Pattern 2: "an [Vorname Nachname]"
        name_match = re.search(r"an\s+([A-ZÄÖÜ][a-zäöüß\-]+\s+[A-ZÄÖÜ][a-zäöüß\-]+)", text, re.IGNORECASE)
        if name_match:
            name = name_match.group(1)
        else:
            # Pattern 3: "für [Name]"
            name_match = re.search(r"für\s+([A-ZÄÖÜ][a-zäöüß\-]+\s+[A-ZÄÖÜ][a-zäöüß\-]+)", text, re.IGNORECASE)
            if name_match:
                name = name_match.group(1)
            else:
                # Pattern 4: Am Ende nach Komma
                name_match = re.search(r",\s*an\s+([A-ZÄÖÜ][a-zäöüß\-]+\s+[A-ZÄÖÜ][a-zäöüß\-]+)", text, re.IGNORECASE)
                if name_match:
                    name = name_match.group(1)

    # Bereinige Name (entferne Klammern/Zitate)
    name = re.sub(r"\(.*?\)", "", name)
    name = name.strip('" ').replace("  ", " ")

    # Topic (alles außer Name/Template-Keywords/Absender)
    topic_text = text
    
    # Entferne Absender-Informationen (alle Patterns)
    topic_text = re.sub(r"von\s+Prof\.?\s*Dr\.?\s+[A-ZÄÖÜ][a-zäöüß\-]+\s+[A-ZÄÖÜ][a-zäöüß\-]+", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"absender\s+ist\s+Prof\.?\s*Dr\.?\s+[A-ZÄÖÜ][a-zäöüß\-]+\s+[A-ZÄÖÜ][a-zäöüß\-]+", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"der\s+absender\s+ist\s+Prof\.?\s*Dr\.?\s+[A-ZÄÖÜ][a-zäöüß\-]+\s+[A-ZÄÖÜ][a-zäöüß\-]+", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"aus\s+der\s+[A-ZÄÖÜa-zäöüß\s]+fakultät", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"der\s+ein\s+Professor\s+Fakultät\s+[A-ZÄÖÜa-zäöüß]+", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"geschrieben\s+sein\s+der\s+ein\s+Professor", "", topic_text, flags=re.IGNORECASE)
    
    # Entferne Empfänger-Informationen
    if name != "Max Müller":
        topic_text = re.sub(rf"\b{re.escape(name)}\b", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"\ban\s+studierende\b", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"\ban\s+studenten\b", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"\ban\s+alle\b", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"\(.*?liebe\s+studierende.*?\)", "", topic_text, flags=re.IGNORECASE)
    
    # Entferne E-Mail-Adressen und Website-Informationen
    topic_text = re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", "", topic_text, re.IGNORECASE)
    topic_text = re.sub(r"die\s+des\s+professors\s+\(.*?\)\s+lautet:", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"und\s+hat\s+keine\s+eigene\s+website", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"und\s+hat\s+keine\s+website", "", topic_text, flags=re.IGNORECASE)
    
    # Entferne Template-Keywords
    topic_text = re.sub(r"\b(uni\s*hamburg|uni\s*hh|hamburg\s*style|university\s*style|design\s+der\s+uni|nutze\s+dabei\s+das\s+design)\b", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"\b(an|für)\s+[A-ZÄÖÜ][a-zäöüß\-]+\s+[A-ZÄÖÜ][a-zäöüß\-]+\b", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"\b(bitte|generiere|eine|mail|email|geht|wobei|das|wo\s+es\s+darum)\b", "", topic_text, flags=re.IGNORECASE)
    topic_text = re.sub(r"bezüglich:\s*zu\s*studierenden", "", topic_text, flags=re.IGNORECASE)
    
    # Suche nach dem eigentlichen Thema - extrahiere den Inhalt nach "dass" oder "wo es darum"
    topic_match = re.search(r"(?:dass|wo\s+es\s+darum)\s*,?\s*(.+?)(?:\.\s*Dieser|,\s*weil|$)", topic_text, re.IGNORECASE | re.DOTALL)
    if topic_match:
        topic = topic_match.group(1).strip()
        # Bereinige weiter
        topic = re.sub(r"dass\s+die\s+klausur", "die Klausur", topic, flags=re.IGNORECASE)
        topic = re.sub(r"\.\s*Dieser\s+soll.*$", "", topic, flags=re.IGNORECASE)
    else:
        # Suche nach "Thema:" oder "bezüglich:"
        topic_match = re.search(r"(?:thema|bezüglich|betreff|subject)[\s:]+(.+?)(?:\.|,|$)", topic_text, re.IGNORECASE)
        if topic_match:
            topic = topic_match.group(1).strip()
        else:
            # Suche nach "dass das Thema ..." oder "Thema ..."
            topic_match = re.search(r"(?:dass\s+)?das\s+thema\s+(.+?)(?:\.|,|$)", topic_text, re.IGNORECASE)
            if topic_match:
                topic = topic_match.group(1).strip()
            else:
                # Nimm alles bis zum ersten Punkt oder Komma, aber entferne Meta-Info
                topic = re.split(r"[\.\,]\s*(?:der\s+absender|bitte|nutze|design|dieser\s+soll)", topic_text, flags=re.IGNORECASE)[0].strip()
                if not topic or len(topic) < 5:
                    # Letzter Fallback: extrahiere nur den relevanten Teil
                    topic_match = re.search(r"(?:klausur|prüfung|projekt|thema).*?(?:\.|$)", topic_text, re.IGNORECASE)
                    if topic_match:
                        topic = topic_match.group(0).strip(' .,')
                    else:
                        topic = "Wichtige Mitteilung"  # Sicherer Fallback

    # Final Topic Cleanup (entferne verbleibenden Müll)
    topic = re.sub(r"^[\s,:\-]+", "", topic)  # Führende Kommas/Leerzeichen
    topic = re.sub(r"[\s,:\-]+$", "", topic)  # Trailing Kommas/Leerzeichen
    topic = re.sub(r"^an\s+,?\s*", "", topic, flags=re.IGNORECASE)  # "an ," am Anfang
    topic = re.sub(r"\s*,\s*,\s*", ", ", topic)  # Doppelte Kommas
    topic = re.sub(r"\s*:\s*", ": ", topic)  # Doppelpunkte bereinigen
    topic = topic.strip(" .,:")
    
    # Scenario (besser erkennen)
    scenario = "question"
    if re.search(r"\b(frist|deadline|bis\s*\d{1,2}[\.\/]|abgabe|termin)\b", lower):
        scenario = "deadline"
    elif "erinner" in lower or "reminder" in lower:
        scenario = "reminder"
    elif "dringend" in lower or "urgent" in lower or "wichtig" in lower:
        scenario = "urgent_request"
    elif "fällt aus" in lower or "ausfall" in lower or "absage" in lower:
        scenario = "update"

    # Stelle sicher, dass E-Mail-Adresse immer gesetzt ist (Standard: IONOS)
    if not email:
        email = "anne.lauscher@uni-hamburg.net"
    
    return {
        "name": name.strip(),
        "role": "Studierende" if "stud" in name.lower() else "Student",
        "topic": topic.strip(),
        "scenario": scenario,
        "template": template,
        "sender_name": sender_name.strip(),
        "position": position,
        "email": email,
        "website": website,
    }


def action_generate() -> None:
    cls()
    print("== Email generieren ==\n")
    print("Wähle Eingabeart:")
    print("  (1) Freitext - Beschreibe einfach was du willst")
    print("  (2) Formular - Schritt für Schritt")
    mode = ask("\nDeine Wahl", "1")

    if mode == "1":
        print("\n💡 Beispiel: 'Uni HH style, Thema Projekt bis 25.12, an Max Müller'")
        print("   Oder: 'Prüfung am 25.11 fällt aus, an Steven Mölle, Uni HH style'")
        text = ask("\nBeschreibe die Email", "")
        if not text:
            print("❌ Keine Eingabe - Abbruch")
            input("\nWeiter mit Enter…")
            return
        params = detect_from_text(text)
        print(f"\n✅ Erkannt:")
        print(f"   Empfänger: {params['name']}")
        print(f"   Absender: {params.get('sender_name', 'Prof. Dr. Michael Schmidt')}")
        print(f"   Lehrstuhl: {params.get('position', 'Lehrstuhl für IT-Sicherheit und KI')}")
        print(f"   Absender-E-Mail: {params.get('email', 'm.schmidt@techuniversity.edu')}")
        print(f"   Thema: {params['topic']}")
        print(f"   Template: {params['template']}")
        print(f"   Szenario: {params['scenario']}")
        
        # Bestätigung fragen
        confirm = ask("\nKorrekt? (Enter=Ja, n=Nein zum Anpassen)", "y")
        if confirm.lower().startswith("n"):
            # Nur wenn Nutzer "n" eingibt, werden alle Felder nochmal abgefragt
            params["name"] = ask("Empfänger Name", params["name"])
            params["sender_name"] = ask("Absender Name", params.get("sender_name", "Prof. Dr. Michael Schmidt"))
            params["position"] = ask("Lehrstuhl/Fakultät", params.get("position", "Lehrstuhl für IT-Sicherheit und KI"))
            params["faculty"] = ask("Fakultät/School", params.get("faculty", "University of Hamburg Business School"))
            params["address"] = ask("Adresse", params.get("address", "Von-Melle Park 5"))
            params["city"] = ask("Stadt/PLZ", params.get("city", "20146 Hamburg"))
            params["email"] = ask("Email", params.get("email", "m.schmidt@techuniversity.edu"))
            show_website = ask("Website angeben? (Ja/Nein)", "Nein").lower()
            if show_website.startswith("j") or show_website == "ja":
                params["website"] = ask("Website URL", params.get("website", "https://www.techuniversity.edu"))
            else:
                params["website"] = None  # Keine Website
            params["topic"] = ask("Thema", params["topic"])
            params["template"] = ask("Template [anne|uni_hh|professional|university_style]", params["template"])
            params["scenario"] = ask("Szenario [question|deadline|urgent_request|reminder|update]", params["scenario"])
        # Wenn Enter gedrückt wird (Bestätigung), werden die erkannten Werte verwendet - keine weitere Abfrage!
        
        # Frage auch im Freitext-Modus nach manuellem Text
        manual_text = ask("\nEmail-Text manuell eingeben? (Ja/Nein)", "Nein").lower()
        if manual_text.startswith("j") or manual_text == "ja":
            print("\n💡 Mehrzeilige Eingabe aktiv. Gib deinen Text ein.")
            print("   Du kannst normale Zeilen eingeben; Absätze werden automatisch gesetzt.")
            params["manual_body"] = ask_multiline("Email-Text", end_marker="END")
        else:
            params["manual_body"] = None
    else:
        params = {
            "name": ask("Empfänger Name (optional - wird sonst aus Email extrahiert)", ""),  # Optional
            "role": ask("Rolle", "Student"),
            "topic": ask("Thema", "Rückfrage zu eingereichten Unterlagen"),
            "scenario": ask("Szenario [question|deadline|urgent_request|reminder|update]", "question"),
            # Neues Template "anne" (Professorin-Layout) als Standard
            "template": ask("Template [anne|uni_hh|professional|university_style]", "anne"),
            "sender_name": ask("Absender Name (z.B. Prof. Dr. Kay Nöth)", "Prof. Dr. Michael Schmidt"),
            "position": ask("Lehrstuhl/Fakultät", "Lehrstuhl für IT-Sicherheit und KI"),
            "faculty": ask("Fakultät/School", "University of Hamburg Business School"),
            "address": ask("Adresse (z.B. Von-Melle Park 5)", "Von-Melle Park 5"),
            "city": ask("Stadt/PLZ", "20146 Hamburg"),
            "email": ask("Email-Adresse", "m.schmidt@techuniversity.edu"),
        }
        
        # Wenn Name leer ist, setze auf None (wird später aus Email extrahiert)
        if not params["name"] or params["name"].strip() == "":
            params["name"] = None

        # Standardwerte setzen, falls nicht erkannt
        params.setdefault("faculty", "University of Hamburg Business School")
        params.setdefault("address", "Von-Melle Park 5")
        params.setdefault("city", "20146 Hamburg")
        params.setdefault("email", "m.schmidt@techuniversity.edu")
        params.setdefault("website", None)

        manual_text = ask("Email-Text manuell eingeben? (Ja/Nein)", "Nein").lower()
        if manual_text.startswith("j") or manual_text == "ja":
            print("\n💡 Mehrzeilige Eingabe aktiv. Gib deinen Text ein.")
            print("   Du kannst normale Zeilen eingeben; Absätze werden automatisch gesetzt.")
            params["manual_body"] = ask_multiline("Email-Text", end_marker="END")
        else:
            params["manual_body"] = None

        show_website = ask("Website angeben? (Ja/Nein)", "Nein").lower()
        if show_website.startswith("j") or show_website == "ja":
            params["website"] = ask("Website URL", "https://www.techuniversity.edu")
        else:
            params["website"] = None

        template_input = params["template"].lower().strip()
        if "anne" in template_input:
            params["template"] = "anne"  # Anne-Template (Professorin-Stil)
        elif "uni" in template_input and ("hamburg" in template_input or "hh" in template_input):
            params["template"] = "uni_hh"  # Wird intern zu "tutor" gemappt
        elif "university" in template_input or "universität" in template_input:
            params["template"] = "university_style"
        elif "professional" in template_input or "prof" in template_input:
            params["template"] = "professional"
        else:
            params["template"] = "anne"  # Standard: Anne Template

        scenario_input = params["scenario"].lower().strip()
        if "deadline" in scenario_input or "frist" in scenario_input or "termin" in scenario_input:
            params["scenario"] = "deadline"
        elif "reminder" in scenario_input or "erinner" in scenario_input:
            params["scenario"] = "reminder"
        elif "urgent" in scenario_input or "dringend" in scenario_input or "wichtig" in scenario_input:
            params["scenario"] = "urgent_request"
        elif "update" in scenario_input or "ausfall" in scenario_input or "fällt aus" in scenario_input:
            params["scenario"] = "update"
        else:
            params["scenario"] = "question"

    print("\n🔄 Generiere Email...")
    print(f"   Empfänger: {params['name']}")
    print(f"   Absender: {params.get('sender_name', 'Prof. Dr. Michael Schmidt')}")
    print(f"   Lehrstuhl: {params.get('position', 'Lehrstuhl für IT-Sicherheit und KI')}")
    print(f"   Template: {params['template']}")
    print(f"   Szenario: {params['scenario']}")

    from generate_phishing import generate_complete_phishing_email

    # Normalisiere Template-Namen (interne Mapping)
    template_map = {
        "anne": "anne",           # Neues Anne-Template
        "uni_hh": "tutor",        # Uni HH style → tutor Template (intern)
        "uni hh": "tutor",
        "uni hamburg": "tutor",
        "hamburg": "tutor",
        "tutor": "tutor",         # Alte Bezeichnung weiterhin unterstützt
        "professional": "professional",
        "university_style": "university_style",
    }
    template_normalized = template_map.get(params["template"].lower().strip(), "anne")  # Standard: anne Template

    # E-Mail-Adresse für die Signatur (Anzeige unten in der Mail).
    # WICHTIG: Diese Adresse soll genau so angezeigt werden, wie du sie eingibst
    # (z.B. mit .de für die Professorin), unabhängig von der IONOS-.net-Adresse.
    # Deshalb KEINE automatische .de → .net Konvertierung hier.
    email_for_signature = params.get("email") or "anne.lauscher@uni-hamburg.de"

    signature = {
        "name": params.get("sender_name"),
        "position": params.get("position"),
        "faculty": params.get("faculty"),
        "address": params.get("address"),
        "city": params.get("city"),
        "email": email_for_signature,  # Verwende korrigierte E-Mail
        "website": params.get("website"),
    }

    # Tracking-Parameter für den Platzhalter [Link] im Text
    # WICHTIG: Name wird NICHT im Link gespeichert - kommt automatisch aus Email beim Klick
    # Email wird beim Versenden automatisch in den Link eingefügt
    tracking_params = {
        # Leer - Email wird beim Versenden hinzugefügt, Name wird aus Email extrahiert
    }

    html = generate_complete_phishing_email(
        target_name=params["name"],
        target_role=params.get("role", "Student"),
        topic=params["topic"],
        scenario=params["scenario"],
        template_name=template_normalized,
        signature=signature,
        manual_body=params.get("manual_body"),
        manual_subject=params.get("topic"),
        tracking_url=TRACKING_URL,
        tracking_params=tracking_params,
        tracking_display_text=TRACKING_DISPLAY_TEXT,
    )

    if html:
        print("\n✅ Email erfolgreich generiert! (siehe oben angezeigte Pfadangaben)")
        
        # NEUE FUNKTION: Direkt Versand anbieten
        send_now = ask("\n📮 Email jetzt versenden? (y/n)", "n").lower().startswith("y")
        if send_now:
            # Finde die generierte HTML-Datei - suche nach der neuesten Datei mit passendem Pattern
            safe_template = template_normalized.replace(" ", "_").replace("/", "_")
            pattern = f"phishing_{params['scenario']}_{safe_template}_*.html"
            generated_dir = ROOT / "generated_emails"
            
            # Finde alle passenden Dateien und nimm die neueste
            matching_files = list(generated_dir.glob(pattern))
            if matching_files:
                # Sortiere nach Änderungsdatum (neueste zuerst)
                html_path = max(matching_files, key=lambda p: p.stat().st_mtime)
                print(f"   📄 Verwende: {html_path.name}")
            else:
                print(f"\n❌ HTML-Datei nicht gefunden mit Pattern: {pattern}")
                html_path = None
            
            if not html_path or not html_path.exists():
                print("   💡 HTML-Datei nicht gefunden. Stelle sicher, dass die E-Mail erfolgreich generiert wurde.")
                input("\nWeiter mit Enter…")
                return
            
            # Sammle Versand-Informationen
            print("\n" + "=" * 50)
            print("📧 VERSAND-KONFIGURATION")
            print("=" * 50)
            
            recipient_email = ask("Empfänger-Email (komma-separiert für mehrere, z.B. email1@test.de, email2@test.de)", "test@example.com")
            recipients = [r.strip() for r in recipient_email.split(",") if r.strip()]
            if not recipients:
                print("❌ Keine Empfänger angegeben.")
                return
            subject = ask("Betreff", params.get("topic", "Wichtige Mitteilung"))

            # Tracking-Link pro Empfänger individualisieren (sichtbarer Link bleibt gleich)
            import re
            base_html_content = html_path.read_text(encoding='utf-8')

            def personalize_html(html_content: str, recipient: str) -> str:
                def replace_email(match):
                    url = match.group(1)
                    if "email=" in url:
                        url_updated = re.sub(r"email=[^&\"']*", f"email={recipient}", url)
                    else:
                        separator = "&" if "?" in url else "?"
                        url_updated = f"{url}{separator}email={recipient}"
                    return f'href="{url_updated}"'
                # Wenn ein Shortlink (Bitly) genutzt wird, arbeite mit der TRACKING_URL als Anker.
                # Fallback: alles was "track" enthält.
                if TRACKING_URL:
                    pattern = rf'href="({re.escape(TRACKING_URL)}[^"]*)"'
                else:
                    pattern = r'href="([^"]*track[^"]*)"'
                return re.sub(pattern, replace_email, html_content)
            sender_name = params.get("sender_name", "Prof. Dr. Anne Lauscher")
            # Formatiere Name für IONOS-Anzeige: "Lauscher, Prof. Dr. Anne" statt "Prof. Dr. Anne Lauscher"
            # Extrahiere Nachname und Vorname
            name_parts = sender_name.split()
            if len(name_parts) >= 3 and "Dr." in name_parts:
                # Format: "Prof. Dr. Anne Lauscher" -> "Lauscher, Prof. Dr. Anne"
                title = " ".join(name_parts[:-2])  # "Prof. Dr."
                first_name = name_parts[-2]  # "Anne"
                last_name = name_parts[-1]  # "Lauscher"
                display_name = f"{last_name}, {title} {first_name}"
            else:
                display_name = sender_name
            
            # Verwende IONOS E-Mail als Standard, falls nicht anders angegeben
            # WICHTIG: Für IONOS muss die Absender-Adresse IMMER .net sein (nicht .de)!
            default_sender_email = "anne.lauscher@uni-hamburg.net"
            sender_email = ask(f"Absender-E-Mail (IONOS: muss .net sein!)", default_sender_email)
            # Stelle sicher, dass E-Mail nicht None ist
            if not sender_email or sender_email == "None":
                sender_email = default_sender_email
            # WICHTIG: Korrigiere .de zu .net (IONOS-Domain muss übereinstimmen!)
            if sender_email.endswith("@uni-hamburg.de"):
                sender_email = sender_email.replace("@uni-hamburg.de", "@uni-hamburg.net")
                print(f"   ⚠️ E-Mail-Adresse korrigiert: .de → .net (IONOS erfordert .net)")
            # Verwende display_name - formataddr() in send_email.py setzt automatisch Anführungszeichen bei Kommas
            sender_full = f"{display_name} <{sender_email}>"
            
            dry_run = ask("Dry-Run (.eml speichern)? (y/n)", "y").lower().startswith("y")
            
            try:
                if dry_run:
                    print("\n📦 Erstelle .eml Datei(en)...")
                    for i, rec in enumerate(recipients, start=1):
                        per_html = personalize_html(base_html_content, rec)
                        per_path = html_path.with_name(f"{html_path.stem}_{i}.html")
                        per_path.write_text(per_html, encoding="utf-8")
                        subprocess.run(
                            [
                                sys.executable,
                                str(ROOT / "send_email.py"),
                                "--to", rec,
                                "--subject", subject,
                                "--html", str(per_path),
                                "--from_", sender_full,
                                "--dry-run"
                            ],
                            check=True
                        )
                    print("✅ .eml Datei(en) erstellt in: phishing_project/outbox/")
                else:
                    # IONOS SMTP-Daten als Standard vorschlagen
                    smtp_host = ask("SMTP Host", "smtp.ionos.de")
                    smtp_port = ask("SMTP Port", "587")
                    
                    # Für localhost keine Auth nötig
                    if smtp_host in ["localhost", "127.0.0.1", "::1"]:
                        print("\n📨 Sende via lokalen SMTP-Server...")
                        for i, rec in enumerate(recipients, start=1):
                            per_html = personalize_html(base_html_content, rec)
                            per_path = html_path.with_name(f"{html_path.stem}_{i}.html")
                            per_path.write_text(per_html, encoding="utf-8")
                            subprocess.run(
                                [
                                    sys.executable,
                                    str(ROOT / "send_email.py"),
                                    "--to", rec,
                                    "--subject", subject,
                                    "--html", str(per_path),
                                    "--from_", sender_full,
                                    "--smtp", smtp_host,
                                    "--port", smtp_port,
                                    "--no-tls"
                                ],
                                check=True
                            )
                    else:
                        # Für externe SMTP Auth benötigt
                        # IONOS Username = E-Mail-Adresse
                        default_username = sender_email if "ionos" in smtp_host.lower() else ""
                        username = ask("SMTP Username", default_username)
                        password = ask("SMTP Password/App-Password")
                        print("\n📨 Sende via SMTP...")
                        for i, rec in enumerate(recipients, start=1):
                            per_html = personalize_html(base_html_content, rec)
                            per_path = html_path.with_name(f"{html_path.stem}_{i}.html")
                            per_path.write_text(per_html, encoding="utf-8")
                            subprocess.run(
                                [
                                    sys.executable,
                                    str(ROOT / "send_email.py"),
                                    "--to", rec,
                                    "--subject", subject,
                                    "--html", str(per_path),
                                    "--from_", sender_full,
                                    "--smtp", smtp_host,
                                    "--port", smtp_port,
                                    "--username", username,
                                    "--password", password
                                ],
                                check=True
                            )
                    print("✅ Email erfolgreich versendet!")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Fehler beim Versenden (Exit-Code {e.returncode})")
                print(f"   Details: {e}")
                print("\n💡 Tipps:")
                print("   - Prüfe deine SMTP-Daten (Host, Port, Username, Password)")
                print("   - Stelle sicher, dass dein IONOS-Postfach freigeschaltet ist")
                print("   - Prüfe deine Internetverbindung")
            except Exception as e:
                print(f"\n❌ Unerwarteter Fehler beim Versenden:")
                print(f"   {type(e).__name__}: {e}")
                import traceback
                print("\n📋 Vollständige Fehlermeldung:")
                traceback.print_exc()
    else:
        print("\n❌ Fehler bei der Generierung")

    input("\nWeiter mit Enter…")


def action_batch() -> None:
    cls()
    print("== Batch (CSV) ==\n")
    csv_path = ask("Pfad zur CSV", str(ROOT / "batch.csv"))
    use_ai = ask("AI benutzen? (y/n)", "n").lower().startswith("y")
    # Starte das vorhandene Batch Script
    os.system(
        f'"{sys.executable}" "{ROOT / "batch_generate.py"}" --csv "{csv_path}"' + (" --use-ai" if use_ai else "")
    )
    input("\nWeiter mit Enter…")


def action_extract() -> None:
    cls()
    print("== HTML/EML → Template ==\n")
    src = ask("Input (.eml/.html)")
    out = ask("Output (z.B. email_templates/tutor_template.html)",
              str(ROOT / "email_templates" / "tutor_template.html"))
    dl = ask("Bilder herunterladen? (y/n)", "y").lower().startswith("y")
    cmd = f'"{sys.executable}" "{ROOT / "tools" / "html_extractor.py"}" --input "{src}" --out "{out}"' + (" --download-images" if dl else "")
    os.system(cmd)
    input("\nWeiter mit Enter…")


def action_send() -> None:
    cls()
    print("== Senden ==\n")
    html = ask("Pfad zur HTML", str(ROOT / "generated_emails" / "test_tutor_template.html"))
    dry = ask("Dry-Run (.eml speichern)? (y/n)", "y").lower().startswith("y")
    try:
        if dry:
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "send_email.py"),
                    "--to",
                    "test@example.com",
                    "--subject",
                    "Demo",
                    "--html",
                    html,
                    "--from_",
                    "TechUniversity <you@example.com>",
                    "--dry-run",
                ],
                check=True,
            )
        else:
            to = ask("Empfänger", "empfaenger@example.com")
            sender = ask("Absender", "Prof. Dr. Schmidt <you@gmail.com>")
            host = ask("SMTP Host", "smtp.gmail.com")
            port = ask("Port", "587")
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "send_email.py"),
                    "--to",
                    to,
                    "--subject",
                    "Demo",
                    "--html",
                    html,
                    "--from_",
                    sender,
                    "--smtp",
                    host,
                    "--port",
                    port,
                ],
                check=True,
            )
    except FileNotFoundError:
        print("❌ HTML-Datei wurde nicht gefunden – bitte Pfad prüfen.")
    except subprocess.CalledProcessError as exc:
        print(f"❌ Versand fehlgeschlagen (Exit-Code {exc.returncode}). Details oben im Log.")
    input("\nWeiter mit Enter…")


def main_menu() -> None:
    while True:
        cls()
        print("=" * 50)
        print("MailTool – Phishing Email Generator")
        print("=" * 50)
        print("\nWas möchtest du tun?\n")
        print("  1) Email generieren")
        print("  2) Batch aus CSV (mehrere Emails)")
        print("  3) Template extrahieren (aus HTML/EML)")
        print("  4) Senden (Demo/SMTP)")
        print("  5) Beenden\n")
        choice = ask("Wähle 1-5", "1")
        if choice == "1":
            action_generate()
        elif choice == "2":
            action_batch()
        elif choice == "3":
            action_extract()
        elif choice == "4":
            action_send()
        else:
            break


if __name__ == "__main__":
    main_menu()
