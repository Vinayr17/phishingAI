"""
Phishing-Email Generator
========================
Generiert täuschend echte Phishing-Emails mit Text + Design.

Für Anfänger: Dieses Script kombiniert:
- AI-generierten Text (von deinem trainierten Modell)
- Professionelles HTML-Design
= Perfekte Fake-Email!
"""

import requests
import json
from pathlib import Path
import re
import subprocess
import os
import sys
from typing import Dict, List, Optional, Tuple

# Fix Windows encoding für Emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Import des intelligenten Backup-Systems
try:
    from email_generator_backup import generate_smart_fallback
    HAS_SMART_BACKUP = True
except ImportError:
    HAS_SMART_BACKUP = False


def safe_print(text: str) -> None:
    """Druckt Text sicher auch auf Windows (Emoji-Fallback)."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Entferne Emojis und versuche nochmal
        safe_text = text.encode('ascii', 'ignore').decode('ascii')
        print(safe_text)

DEFAULT_SIGNATURE = {
    "name": "Prof. Dr. Michael Schmidt",
    "position": "Lehrstuhl für IT-Sicherheit und KI",
    "faculty": "University of Hamburg Business School",
    "address": "Von-Melle Park 5",
    "city": "20146 Hamburg",
    "email": "m.schmidt@techuniversity.edu",
    "website": "https://www.techuniversity.edu",
}


def ensure_paragraph_html(text: str, template_name: str = "professional") -> str:
    """Konvertiert einfachen Text in HTML-Absätze. Erhält Absätze und macht Links anklickbar.
    
    Args:
        text: Der Text, der konvertiert werden soll
        template_name: Name des Templates (z.B. "anne", "uni_hh") - bestimmt die Styles
    """
    if not text:
        return "<p></p>"
    if text.strip().startswith("<"):
        return text
    
    import re
    
    # Bestimme Styles basierend auf Template
    # Für "anne" Template: Times New Roman, 11pt, line-height 1.4 (passend zum Template)
    if template_name == "anne":
        p_style = 'style="font-family:\'Times New Roman\', Times, serif !important; font-size:11pt !important; color:#000000 !important; line-height:1.4 !important; margin:0 0 0.8em 0 !important;"'
    else:
        # Standard: keine expliziten Styles (erbt vom Parent)
        p_style = ""
    
    # Teile Text in Zeilen auf, behalte leere Zeilen für Absätze
    lines = text.split('\n')
    paragraphs = []
    
    for line in lines:
        line = line.strip()
        if not line:
            # Leere Zeile = neuer Absatz
            paragraphs.append("")
        else:
            # Erkenne URLs und mache sie zu anklickbaren Links
            # WICHTIG: Erkenne URLs auch ohne http:// oder www. am Anfang!
            # Pattern für URLs: 
            # 1. http:// oder https:// URLs (höchste Priorität)
            # 2. www. URLs
            # 3. Domain-URLs ohne Protokoll (z.B. amazon.com/path) - erkennt .com, .de, .org, etc.
            
            # Prüfe zuerst, ob die Zeile bereits Links enthält (dann nicht nochmal konvertieren)
            if '<a href=' in line:
                paragraphs.append(line)
                continue
            
            # Liste bekannter TLDs für bessere Erkennung
            common_tlds = r'(?:com|de|org|net|edu|gov|io|co|uk|fr|it|es|nl|be|at|ch|info|biz|tv|me|app|dev|tech|online|site|website|academy|blog|cloud|digital|email|global|group|international|media|news|online|services|solutions|store|studio|support|systems|technology|tools|world|zone)'
            
            # Hilfsfunktion: Prüft ob eine Position bereits innerhalb eines <a> Tags ist
            def is_inside_link(text, pos):
                """Prüft ob Position pos in text bereits innerhalb eines <a> Tags liegt."""
                # Finde alle <a> Tags und prüfe ob pos innerhalb liegt
                for match in re.finditer(r'<a[^>]*>', text):
                    start = match.start()
                    # Finde das schließende </a> Tag
                    end_match = re.search(r'</a>', text[start:])
                    if end_match:
                        end = start + end_match.end()
                        if start <= pos < end:
                            return True
                return False
            
            # Pattern 1: URLs mit Protokoll (http:// oder https://) - zuerst verarbeiten
            def make_http_link(match):
                url = match.group(1)
                pos = match.start()
                if not is_inside_link(line, pos):
                    return f'<a href="{url}" style="color: #0066cc !important; text-decoration: underline !important; cursor: pointer !important;">{url}</a>'
                return url
            
            line = re.sub(
                r'(https?://[^\s<>"\'\)]+)',
                make_http_link,
                line
            )
            
            # Pattern 2: URLs mit www. (nur wenn noch nicht als Link erkannt)
            def make_www_link(match):
                url = match.group(1)
                pos = match.start()
                if not is_inside_link(line, pos):
                    return f'<a href="https://{url}" style="color: #0066cc !important; text-decoration: underline !important; cursor: pointer !important;">{url}</a>'
                return url
            
            line = re.sub(
                r'(www\.[^\s<>"\'\)]+)',
                make_www_link,
                line
            )
            
            # Pattern 3: Domain-URLs ohne Protokoll (z.B. amazon.com/path oder example.de)
            def make_domain_link(match):
                url = match.group(1)
                pos = match.start()
                # Prüfe ob bereits in Link
                if is_inside_link(line, pos):
                    return url
                # Prüfe ob es wirklich eine Domain ist (enthält TLD)
                if '.' in url:
                    # Prüfe ob es eine bekannte TLD enthält (z.B. .com, .de, etc.)
                    tld_pattern = r'\.' + common_tlds + r'(?:/|$|\s|"|\'|\)|>)'
                    if re.search(tld_pattern, url, re.IGNORECASE):
                        href = 'https://' + url.rstrip('.,;:!?')  # Entferne Satzzeichen am Ende
                        display_url = url.rstrip('.,;:!?')
                        return f'<a href="{href}" style="color: #0066cc !important; text-decoration: underline !important; cursor: pointer !important;">{display_url}</a>'
                return url
            
            # Erkenne Domain-URLs (z.B. amazon.com/path oder example.de)
            # Pattern: Domain mit TLD, optional Pfad
            line = re.sub(
                r'([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.' + common_tlds + r'(?:/[^\s<>"\'\)]*)?)',
                make_domain_link,
                line,
                flags=re.IGNORECASE
            )
            
            paragraphs.append(line)
    
    # Konvertiere zu HTML-Absätzen
    html_parts = []
    for para in paragraphs:
        if para == "":
            # Leerer Absatz = <br/>
            html_parts.append("<br/>")
        else:
            if p_style:
                html_parts.append(f"<p {p_style}>{para}</p>")
            else:
                html_parts.append(f"<p>{para}</p>")
    
    return "".join(html_parts)


def paragraphs_to_html(paragraphs: List[str]) -> str:
    if not paragraphs:
        return ""
    cleaned = [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]
    if not cleaned:
        return ""
    return "".join(f"<p>{paragraph}</p>" for paragraph in cleaned)


def apply_signature(html: str, signature: Optional[Dict[str, Optional[str]]]) -> str:
    data = DEFAULT_SIGNATURE.copy()
    if signature:
        for key, value in signature.items():
            if key in data:
                # Übernehme Wert IMMER, auch wenn None (wichtig für "keine Website")
                data[key] = value

    website_block = ""
    # Nur Website-Block erstellen, wenn Website NICHT None ist
    if data.get("website") is not None and data.get("website"):
        website = data["website"]
        # Für Anne-Template: einfacher Text-Link (wie im Original)
        # Für andere Templates: formatierter Link
        website_block = f'<br>{website}'  # Einfach wie im Original

    replacements = {
        "{{NAME}}": data["name"] or "Prof. Dr. Michael Schmidt",
        "{{POSITION}}": data["position"] or "Lehrstuhl für IT-Sicherheit und KI",
        "{{FACULTY}}": data["faculty"] or "University of Hamburg Business School",
        "{{ADDRESS}}": data["address"] or "Von-Melle Park 5",
        "{{CITY}}": data["city"] or "20146 Hamburg",
        "{{EMAIL}}": data["email"] or "m.schmidt@techuniversity.edu",
        "{{WEBSITE_BLOCK}}": website_block,
        # Fallbacks, falls Template bereits feste Strings enthält
        "Prof. Dr. Michael Schmidt": data["name"] or "Prof. Dr. Michael Schmidt",
        "Lehrstuhl für IT-Sicherheit und KI": data["position"] or "Lehrstuhl für IT-Sicherheit und KI",
        "University of Hamburg Business School": data["faculty"] or "University of Hamburg Business School",
        "Von-Melle Park 5": data["address"] or "Von-Melle Park 5",
        "20146 Hamburg": data["city"] or "20146 Hamburg",
        "m.schmidt@techuniversity.edu": data["email"] or "m.schmidt@techuniversity.edu",
    }

    for placeholder, value in replacements.items():
        if value is not None:  # Nur ersetzen, wenn Wert vorhanden
            html = html.replace(placeholder, value)
    return html


def adjust_template_paths(html: str, template_name: str) -> str:
    """Passe Pfade in Templates an, damit Logos im generated_emails-Folder gefunden werden."""
    # Für Uni-Hamburg-Templates (tutor & anne) Logo-Pfad vereinheitlichen
    if template_name in {"tutor", "anne"}:
        html = html.replace("../email_templates/assets/logo_uni_hamburg.png", "assets/logo_uni_hamburg.png")
    return html


def copy_template_assets(template_name: str, output_dir: Path) -> None:
    """Kopiere statische Assets (z.B. UHH-Logo) in den generated_emails-Ordner.

    Wird für Templates genutzt, die das Uni-Hamburg-Logo verwenden.
    Für das "anne" Template werden auch die drei unteren Logos kopiert.
    """
    if template_name not in {"tutor", "anne"}:
        return

    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    import shutil

    # UHH-Logo kopieren (für tutor und anne)
    logo_src = Path(__file__).parent / "email_templates" / "assets" / "logo_uni_hamburg.png"
    if logo_src.exists():
        logo_dst = assets_dir / "logo_uni_hamburg.png"
        if not logo_dst.exists():
            shutil.copy2(logo_src, logo_dst)
    
    # Für "anne" Template: Kopiere auch die drei unteren Logos
    if template_name == "anne":
        anne_logos = [
            "anne_linkedin.png",
            "anne_equis.gif",
            "anne_prime.gif",
        ]
        for logo_filename in anne_logos:
            logo_src = Path(__file__).parent / "email_templates" / "assets" / logo_filename
            if logo_src.exists():
                logo_dst = assets_dir / logo_filename
                if not logo_dst.exists():
                    shutil.copy2(logo_src, logo_dst)
                    print(f"   ✅ Anne-Logo kopiert: {logo_filename}")
            else:
                print(f"   ⚠️ Anne-Logo nicht gefunden: {logo_filename}")


def parse_model_response(raw_text: str) -> Dict[str, object]:
    """Parst die KI-Antwort und extrahiert Betreff + Body, auch wenn JSON nicht perfekt ist."""
    raw = raw_text.strip()

    # Entferne ALLES nach dem schließenden JSON (``` und nachfolgender Text)
    # Finde das letzte } das zum JSON gehört
    json_start = raw.find('{')
    if json_start == -1:
        # Kein JSON gefunden
        return {}
    
    # Suche das passende schließende }
    brace_count = 0
    json_end = -1
    for i in range(json_start, len(raw)):
        if raw[i] == '{':
            brace_count += 1
        elif raw[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                json_end = i
                break
    
    if json_end == -1:
        # Kein passendes } gefunden
        return {}
    
    # Extrahiere NUR das JSON
    json_str = raw[json_start:json_end + 1]
    
    subject = "Wichtige Mitteilung"
    body_html = ""
    paragraphs: List[str] = []

    try:
        data = json.loads(json_str)
        subject = data.get("subject") or subject
        body_data = data.get("body") or data.get("paragraphs") or []
        if isinstance(body_data, str):
            body_data = [body_data]
        if isinstance(body_data, list):
            paragraphs = [str(item).strip() for item in body_data if str(item).strip() and not str(item).strip().lower().startswith("absatz ")]
            body_html = paragraphs_to_html(paragraphs)
        
        # Erfolg! JSON wurde geparst
        return {
            "subject": subject.strip() or "Wichtige Mitteilung",
            "body_html": body_html,
            "paragraphs": paragraphs,
            "raw": raw_text,
        }
    except json.JSONDecodeError:
        # JSON ist nicht perfekt - versuche es zu reparieren
        try:
            # Entferne problematische Zeichen
            json_str = re.sub(r'([{,]\s*"[^"]*"[^,}]*),(\s*"[^"]*")', r'\1\2', json_str)
            json_str = re.sub(r'([{,]\s*"[^"]*"[^,}]*),(\s*[}\]])', r'\1\2', json_str)
            data = json.loads(json_str)
            subject = data.get("subject") or subject
            body_data = data.get("body") or data.get("paragraphs") or []
            if isinstance(body_data, str):
                body_data = [body_data]
            if isinstance(body_data, list):
                paragraphs = [str(item).strip() for item in body_data if str(item).strip()]
                body_html = paragraphs_to_html(paragraphs)
            
            # Reparatur erfolgreich
            return {
                "subject": subject.strip() or "Wichtige Mitteilung",
                "body_html": body_html,
                "paragraphs": paragraphs,
                "raw": raw_text,
            }
        except:
            pass

    # Wenn JSON-Parsing fehlschlägt, versuche Text-Parsing
    if not body_html or not paragraphs:
        # Suche nach "subject" oder "Betreff" im Text
        subject_match = re.search(r'(?:subject|betreff)[\s:]+["\']?([^"\'\n]+)["\']?', raw_text, re.IGNORECASE)
        if subject_match:
            subject = subject_match.group(1).strip()
        
        # Suche nach "body" Array oder Absätzen
        body_match = re.search(r'"body"\s*:\s*\[(.*?)\]', raw_text, re.DOTALL | re.IGNORECASE)
        if body_match:
            body_content = body_match.group(1)
            # Extrahiere Strings aus dem Array
            paragraphs = re.findall(r'["\']([^"\']+)["\']', body_content)
            if paragraphs:
                body_html = paragraphs_to_html(paragraphs)
        
        # Wenn immer noch nichts: Versuche strukturierten Text zu parsen
        if not paragraphs:
            # Suche nach Anrede + Absätzen
            lines = raw_text.split('\n')
            found_greeting = False
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Überspringe JSON-Struktur
                if line.startswith('{') or line.startswith('}') or line.startswith('"subject') or line.startswith('"body'):
                    continue
                # Überspringe Markdown
                if line.startswith('```') or line.startswith('#'):
                    continue
                # Überspringe Anweisungen
                if any(word in line.lower() for word in ['example', 'beispiel', 'wichtig', 'aufgabe', 'jetzt erstelle']):
                    continue
                # Finde Anrede
                if any(greeting in line for greeting in ["Liebe", "Sehr geehrte", "Hallo", "Guten Tag"]):
                    found_greeting = True
                    paragraphs.append(line)
                elif found_greeting and len(line) > 10:
                    paragraphs.append(line)
            
            if paragraphs:
                body_html = paragraphs_to_html(paragraphs)

    # Filter ungültige Antworten
    preview = raw_text.lower()[:300]
    if "please respond" in preview or ("example" in preview and "beispiel" not in preview and len(paragraphs) == 0):
        return {}

    # Wenn wir immer noch nichts haben, gib leeres Ergebnis zurück
    if not body_html or not paragraphs:
        return {}

    return {
        "subject": subject.strip() or "Wichtige Mitteilung",
        "body_html": body_html,
        "paragraphs": paragraphs,
        "raw": raw_text,
    }


def summarise_topic(topic: str) -> str:
    """Bereinigt den Topic-Text und extrahiert nur den relevanten Inhalt."""
    cleaned = re.sub(r"\s+", " ", topic)
    # Entferne Klammern und Zitate
    cleaned = re.sub(r"\(.*?\)", "", cleaned)
    cleaned = cleaned.replace('"', '').replace("'", "")
    cleaned = cleaned.strip(' .,')
    if not cleaned:
        return ""
    
    # Entferne Meta-Informationen
    lower = cleaned.lower()
    # Entferne "bezüglich:" am Anfang
    cleaned = re.sub(r"^bezüglich:\s*", "", cleaned, flags=re.IGNORECASE)
    # Entferne "wo es darum" Konstruktionen
    cleaned = re.sub(r"wo\s+es\s+darum\s*,?\s*", "", cleaned, flags=re.IGNORECASE)
    # Entferne "dass" am Anfang
    if cleaned.lower().startswith("dass"):
        cleaned = re.sub(r"^dass\s+", "", cleaned, flags=re.IGNORECASE)
    # Entferne "dieser soll" Teile
    cleaned = re.split(r"\bdieser\s+soll\b", cleaned, 1, flags=re.IGNORECASE)[0]
    cleaned = cleaned.strip(' .,')
    
    return cleaned


def extract_dates_and_reason(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    dates = re.findall(r"\b\d{1,2}\.\d{1,2}\b", text)
    first_date = dates[0] if len(dates) >= 1 else None
    second_date = dates[1] if len(dates) >= 2 else None
    reason = None
    reason_match = re.search(r"weil\s+(.*)", text, re.IGNORECASE)
    if reason_match:
        reason = reason_match.group(1).strip(' .,")')
    return first_date, second_date, reason


def build_fallback_content(target_name: str, topic: str, scenario: str) -> Tuple[str, str]:
    main_statement = summarise_topic(topic)
    first_date, second_date, reason = extract_dates_and_reason(topic)

    subject_base = main_statement if main_statement else topic.strip()
    subject_base = subject_base.strip(' .,')
    if len(subject_base) > 80:
        subject_base = subject_base[:77] + "..."

    scenario_subjects = {
        "update": f"Aktualisierung: {subject_base}" if subject_base else "Aktualisierung",
        "deadline": f"Fristinformation: {subject_base}" if subject_base else "Fristinformation",
        "urgent_request": f"Wichtige Bitte: {subject_base}" if subject_base else "Wichtige Mitteilung",
        "reminder": f"Erinnerung: {subject_base}" if subject_base else "Erinnerung",
        "question": subject_base or "Rückfrage",
    }
    subject = scenario_subjects.get(scenario, subject_base or "Mitteilung")

    name_lower = target_name.lower()
    if "stud" in name_lower:
        greeting = "Liebe Studierende"
    elif "team" in name_lower:
        greeting = "Liebes Team"
    else:
        greeting = f"Liebe/r {target_name}"

    paragraphs = [greeting + ","]

    if first_date and second_date:
        paragraphs.append(
            f"die ursprünglich für den {first_date} angesetzte Prüfung wird auf den {second_date} verschoben."
        )
    elif first_date:
        paragraphs.append(
            f"die Prüfung am {first_date} kann nicht wie geplant stattfinden."
        )

    if main_statement:
        paragraphs.append(main_statement)

    if reason:
        paragraphs.append(f"Grund: {reason}.")

    paragraphs.append("Bitte informieren Sie sich zeitnah über weitere Schritte oder melden Sie sich bei Fragen.")
    paragraphs.append("Vielen Dank für Ihr Verständnis.")

    body_html = paragraphs_to_html(paragraphs)
    return subject, body_html


def generate_email_text(target_name, target_role, topic, scenario="urgent_request") -> Optional[Dict[str, object]]:
    """Generiert Email-Bestandteile (Betreff + Body) mit dem trainierten Modell."""

    # Bestimme Anrede basierend auf Empfänger
    if "stud" in target_name.lower():
        greeting = "Liebe Studierende"
    elif "team" in target_name.lower():
        greeting = "Liebes Team"
    else:
        greeting = f"Liebe/r {target_name}"

    # Few-Shot Examples für besseres Verständnis
    examples = {
        "update": '''Beispiel 1:
Eingabe: Empfänger: Studierende, Thema: Klausur am 17.12 fällt aus, verschoben auf 20.12 wegen Systemfehler im Studienbüro
Ausgabe: {"subject": "Verschobene Klausur am 20.12", "body": ["Liebe Studierende,", "die ursprünglich für den 17.12 angesetzte Klausur muss aufgrund eines Systemfehlers im Studienbüro auf den 20.12 verschoben werden.", "Bitte informieren Sie sich zeitnah über weitere Details oder melden Sie sich bei Fragen.", "Vielen Dank für Ihr Verständnis."]}''',
        "deadline": '''Beispiel 2:
Eingabe: Empfänger: Max Müller, Thema: Projektabgabe bis 25.12
Ausgabe: {"subject": "Erinnerung: Projektabgabe bis 25.12", "body": ["Liebe/r Max Müller,", "dies ist eine freundliche Erinnerung, dass die Abgabe Ihres Projekts bis zum 25.12 erfolgen muss.", "Bitte reichen Sie alle erforderlichen Unterlagen bis spätestens 23:59 Uhr ein.", "Bei Rückfragen stehe ich gerne zur Verfügung."]}''',
        "question": '''Beispiel 3:
Eingabe: Empfänger: Studierende, Thema: Rückfrage zu eingereichten Unterlagen
Ausgabe: {"subject": "Rückfrage zu eingereichten Unterlagen", "body": ["Liebe Studierende,", "ich habe Ihre eingereichten Unterlagen erhalten und benötige noch eine kurze Klärung.", "Bitte melden Sie sich bei mir, damit wir die offenen Punkte besprechen können.", "Vielen Dank im Voraus."]}'''
    }

    example = examples.get(scenario, examples["update"])

    prompt = f"""Du bist ein Email-Generator für Security Awareness Training an der Universität Hamburg.

AUFGABE: Erstelle eine realistische, professionelle Email im Stil eines Universitätsprofessors.

{example}

JETZT ERSTELLE FÜR:
Empfänger: {target_name} ({target_role})
Thema: {topic}
Anrede: {greeting}
Szenario: {scenario}

WICHTIG: Antworte NUR mit JSON, kein Text davor oder danach, kein Markdown:
{{
  "subject": "Betreff der Email",
  "body": [
    "{greeting},",
    "Erster Absatz mit Hauptinformation",
    "Zweiter Absatz mit Details oder Handlungsaufforderung",
    "Abschluss mit Höflichkeitsformel"
  ]
}}

Die Email soll authentisch, professionell und im Stil eines deutschen Universitätsprofessors sein."""

    print(f"🤖 Generiere Email für {target_name}...")
    print(f"   Thema: {topic}")

    try:
        # Prüfe ob Ollama läuft (versuche direkten Pfad)
        ollama_path = r"C:\Users\vinay\AppData\Local\Programs\Ollama\ollama.exe"
        if not os.path.exists(ollama_path):
            ollama_path = "ollama"  # Fallback auf PATH

        # Prüfe ob Ollama läuft
        try:
            check_response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if check_response.status_code != 200:
                print("   ⚠️ Ollama läuft nicht oder antwortet nicht")
                print(f"   💡 Starte Ollama mit: {ollama_path} serve")
                return None
        except Exception as e:
            print(f"   ⚠️ Ollama läuft nicht! ({e})")
            print(f"   💡 Starte Ollama mit: {ollama_path} serve")
            print("   💡 Oder: Öffne Ollama App manuell")
            return None

        # Anfrage an Ollama mit dem trainierten Modell
        # Nutzt API (Ollama muss laufen!)
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "professor-emails",  # Dein trainiertes Modell!
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 400
                }
            },
            timeout=120  # Erhöht auf 2 Minuten
        )

        if response.status_code == 200:
            result = response.json()
            raw_text = result.get("response", "")

            if raw_text.strip() == "":
                print("   ⚠️ Leere Antwort erhalten")
                return None

            lower_preview = raw_text.lower()[:200]
            if "cannot" in lower_preview or "unable" in lower_preview:
                print("   ⚠️ Model blockiert noch - versuche anderen Prompt...")
                return None

            parsed = parse_model_response(raw_text)
            if not parsed.get("paragraphs"):
                print("   ⚠️ Antwort enthielt kein gültiges JSON")
                # Debug: Zeige ersten Teil der Antwort
                preview = raw_text[:200] if len(raw_text) > 200 else raw_text
                print(f"   📄 Antwort-Vorschau: {preview}...")
                return None
            print("   ✅ Email-Bestandteile generiert!")
            return parsed
        else:
            print(f"   ❌ Error: Status {response.status_code}")
            return None

    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None


def extract_subject_and_body(email_text):
    """
    Extrahiert Betreff und Body aus generiertem Text.

    Args:
        email_text: Der komplette Email-Text

    Returns:
        (subject, body) tuple
    """
    lines = email_text.strip().split('\n')

    subject = "Wichtige Mitteilung"  # Default
    body_lines = []
    body_started = False

    for line in lines:
        # Suche Betreff
        if line.strip().lower().startswith('betreff:'):
            subject = line.split(':', 1)[1].strip()
        elif line.strip().lower().startswith('subject:'):
            subject = line.split(':', 1)[1].strip()
        # Body sammeln
        elif body_started or (line.strip() and not line.strip().lower().startswith('betreff')):
            if line.strip():  # Nicht-leere Zeilen
                body_started = True
                body_lines.append(line)

    body = '\n'.join(body_lines)

    body_html = ensure_paragraph_html(body)

    return subject, body_html


def combine_with_template(subject, body, template_name="professional"):
    """
    Kombiniert AI-Text mit HTML-Template.

    Args:
        subject: Email-Betreff
        body: Email-Body (HTML)
        template_name: Name des Templates ("professional", "tutor", "university_style")

    Returns:
        Komplette HTML-Email
    """
    # Template-Mapping
    templates = {
        "professional": "professional_template.html",
        "tutor": "tutor_template.html",
        "university_style": "university_style_template.html",
        # Neues Template im Anne-Stil (Professorin)
        "anne": "anne_template.html",
    }

    template_file = templates.get(template_name, "professional_template.html")
    template_path = Path(__file__).parent / "email_templates" / template_file

    if not template_path.exists():
        print(f"   ⚠️ Template nicht gefunden: {template_file}, nutze professional_template.html")
        template_path = Path(__file__).parent / "email_templates" / "professional_template.html"

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Ersetze Platzhalter
    html = template.replace('{{SUBJECT}}', subject)
    html = html.replace('{{BODY}}', body)

    # WICHTIG: Signatur-Platzhalter werden NICHT hier ersetzt!
    # Das macht apply_signature() später, damit die echten Daten eingesetzt werden
    # Nur für Templates ohne {{PLATZHALTER}} (alte Kompatibilität):
    if '{{NAME}}' not in html and 'Prof. Dr. Michael Schmidt' in html:
        # Altes Template ohne Platzhalter - ersetze direkt
        pass  # apply_signature() macht das später

    return html


def generate_complete_phishing_email(
    target_name: str,
    target_role: str,
    topic: str,
    scenario: str = "urgent_request",
    template_name: str = "professional",
    signature: Optional[Dict[str, Optional[str]]] = None,
    manual_body: Optional[str] = None,
    manual_subject: Optional[str] = None,
) -> Optional[str]:
    """Generiert eine KOMPLETTE Phishing-Mail (Text + HTML-Template)."""

    print("\n" + "=" * 60)
    try:
        print("📧 GENERIERE PHISHING-EMAIL")
    except UnicodeEncodeError:
        print("[EMAIL] GENERIERE PHISHING-EMAIL")
    print("=" * 60)

    subject = topic
    body_html = ""

    if manual_body:
        subject = manual_subject or topic
        body_html = ensure_paragraph_html(manual_body, template_name)
    else:
        ai_result = generate_email_text(target_name, target_role, topic, scenario)
        if ai_result and ai_result.get("subject") and ai_result.get("body_html"):
            subject = ai_result.get("subject", topic)
            body_html = ai_result.get("body_html", "")
            if not body_html:
                body_html = paragraphs_to_html(ai_result.get("paragraphs", []))
        else:
            print("❌ Konnte Email-Text nicht generieren")
            # Nutze intelligentes Backup-System, falls verfügbar
            if HAS_SMART_BACKUP:
                print("   🔄 Nutze intelligentes Backup-System...")
                backup_result = generate_smart_fallback(target_name, topic, scenario)
                subject = backup_result.get("subject", topic)
                body_paragraphs = backup_result.get("body", [])
                body_html = paragraphs_to_html(body_paragraphs)
            else:
                # Fallback auf altes System
                subject, body_html = build_fallback_content(target_name, topic, scenario)

    if not body_html:
        if HAS_SMART_BACKUP:
            backup_result = generate_smart_fallback(target_name, topic, scenario)
            subject = backup_result.get("subject", topic)
            body_paragraphs = backup_result.get("body", [])
            body_html = paragraphs_to_html(body_paragraphs)
        else:
            _, body_html = build_fallback_content(target_name, topic, scenario)

    print(f"\n📝 Betreff: {subject}")
    print(f"🎨 Kombiniere mit HTML-Template ({template_name})...")
    html_email = combine_with_template(subject, body_html, template_name)
    
    # Wenn manueller Text verwendet wird, wende IMMER die Signatur an (wie bei automatischem Text)
    # Nur die automatische "Mit freundlichen Grüßen" Zeile entfernen, wenn der Nutzer bereits eine Grußformel geschrieben hat
    if manual_body:
        import re
        
        # Prüfe ob der Text bereits eine Grußformel enthält
        manual_lower = manual_body.lower()
        has_greeting = any(phrase in manual_lower for phrase in [
            "mit freundlichen grüßen", "beste grüße", "liebe grüße", 
            "viele grüße", "herzliche grüße", "freundliche grüße"
        ])
        
        # Wende IMMER die Signatur an (Logo und alle Signatur-Daten bleiben erhalten)
        html_email = apply_signature(html_email, signature)
        
        # Entferne nur die automatische "Mit freundlichen Grüßen" Zeile, wenn der Nutzer bereits eine Grußformel geschrieben hat
        if has_greeting:
            print("   ℹ️  Manueller Text mit Grußformel erkannt - entferne automatische Grußformel, behalte Signatur")
            html_email = re.sub(
                r'<div><br/></div>\s*<div>Mit freundlichen Grüßen[^<]*</div>',
                '',
                html_email,
                flags=re.IGNORECASE
            )
        else:
            print("   ℹ️  Manueller Text ohne Grußformel - entferne automatische Grußformel, behalte Signatur")
            # Entferne auch die automatische "Mit freundlichen Grüßen" Zeile
            html_email = re.sub(
                r'<div><br/></div>\s*<div>Mit freundlichen Grüßen[^<]*</div>',
                '',
                html_email,
                flags=re.IGNORECASE
            )
    else:
        # Automatisch generierter Text - normale Signatur anwenden
        html_email = apply_signature(html_email, signature)
    
    html_email = adjust_template_paths(html_email, template_name)
    print("   ✅ HTML-Email erstellt!")

    output_dir = Path(__file__).parent / "generated_emails"
    output_dir.mkdir(exist_ok=True)
    copy_template_assets(template_name, output_dir)

    # Normalisiere Template-Name für Dateinamen
    safe_template = template_name.replace(" ", "_").replace("/", "_")
    filename = f"phishing_{target_name.replace(' ', '_')}_{scenario}_{safe_template}.html"
    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_email)

    print("💾 Gespeichert:")
    print(f"   {output_path.absolute()}")

    return html_email


# ===== HAUPTPROGRAMM =====
if __name__ == "__main__":
    import sys

    print("🚀 PHISHING-EMAIL GENERATOR")
    print("Generiert täuschend echte Emails für Security Training\n")

    # Template aus Kommandozeile oder Default
    template = "tutor" if len(sys.argv) > 1 and sys.argv[1] == "--tutor" else "professional"

    if template == "tutor":
        print("📧 Nutze Tutor-Template (Uni Hamburg Style)")

    # Beispiel mit gewähltem Template
    html = generate_complete_phishing_email(
        target_name="Max Müller",
        target_role="Student",
        topic="Rückfrage zu eingereichten Unterlagen",
        scenario="question",
        template_name=template
    )

    if html:
        print("\n✅ Email erfolgreich generiert!")
        print(f"📁 Öffne: generated_emails/phishing_Max_Müller_question_{template}.html")
    else:
        print("\n❌ Generierung fehlgeschlagen")

    print("\n💡 Tipp: Nutze --tutor für Tutor-Template")
    print("   Beispiel: python generate_phishing.py --tutor")

