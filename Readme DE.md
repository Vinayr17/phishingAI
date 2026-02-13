# 🎣 Phishing Simulation System

> Eine KI-gestützte Phishing-Simulationsplattform, die die Zugänglichkeit und Wirksamkeit moderner Social-Engineering-Angriffe in Bildungskontexten demonstriert.

<div align="center">

**Entwickelt an der Universität Hamburg**  
*Risk and Rewards of Generative AI in Business*  
*Wintersemester 2024/2025*

</div>

---

## ⚠️ Ethischer Hinweis

**Dieses Projekt dient ausschließlich Bildungs- und Forschungszwecken.**

Alle Experimente wurden unter ethischer Aufsicht und mit expliziter Genehmigung der Kursleitung durchgeführt. Die Teilnehmer erhielten nach der Datenerhebung eine umfassende Aufklärung. Dieses System sollte niemals für unbefugte Aktivitäten oder böswillige Zwecke verwendet werden.

---

## 📖 Über dieses Projekt

Dieses Forschungsprojekt untersucht die Schnittstelle zwischen generativer KI, Social Engineering und Cybersecurity-Bildung durch den Aufbau und Einsatz eines vollständigen Phishing-Simulationssystems. Ich entwickelte die gesamte technische Implementation - von der Email-Generierung über die Tracking-Infrastruktur bis zum Analytics-Dashboard - als technische Komponente eines größeren Gruppenforschungsprojekts. Das Projekt demonstriert eine kritische Erkenntnis: Die Erstellung ausgefeilter Phishing-Kampagnen ist durch moderne Cloud-Infrastruktur, Open-Source-Tools und KI-Unterstützung (einschließlich KI-gestützter Entwicklungsunterstützung und Prompting) bemerkenswert zugänglich geworden und erfordert nur mittlere Programmierkenntnisse und minimale finanzielle Investitionen.

Durch ein kontrolliertes Experiment mit Studierenden eines Cybersecurity-Kurses liefern wir empirische Belege dafür, dass theoretisches Bewusstsein für Phishing-Bedrohungen nicht zuverlässig in vorsichtiges Verhalten übergeht, wenn Personen mit realistischen Kommunikationen von vertrauenswürdigen institutionellen Quellen konfrontiert werden.

## 🎯 Forschungsziele

Unser Projekt verfolgt drei miteinander verbundene Ziele:

**1. Technische Implementation**  
Entwurf und Bereitstellung einer voll funktionsfähigen Phishing-Simulationsinfrastruktur, die die Fähigkeiten realer Angreifer repliziert, einschließlich automatisierter Email-Generierung, Echtzeit-Interaktionsverfolgung und umfassender Metadatenerfassung.

**2. Proof of Concept**  
Demonstration der technischen Zugänglichkeit ausgefeilter Phishing-Systeme durch Dokumentation exakter Kosten, Erklärung jeder Architekturentscheidung und Nachweis, dass Studierende mit mittleren Programmierkenntnissen überzeugende Angriffssimulationen mit ausschließlich Mainstream-Entwicklungstools erstellen können.

**3. Empirische Awareness-Forschung**  
Sammlung realer Verhaltensdaten von Teilnehmern aus unserer akademischen Gemeinschaft, um tatsächliche Phishing-Anfälligkeit zu messen statt auf theoretische Annahmen zu vertrauen, und damit evidenzbasierte Erkenntnisse für die Cybersecurity-Bildung beizutragen.

---

## 🏗️ System-Architektur

Unser System umfasst vier integrierte Komponenten, die zusammenarbeiten, um Phishing-Interaktionen zu simulieren, zu verfolgen und zu analysieren:

### 1️⃣ Email-Generierungs-Modul

**Zweck**: Erstellen institutionell authentischer Emails, die universitäre Kommunikationsmuster präzise replizieren.

**Funktionsweise**: Ich entwickelte ein benutzerdefiniertes HTML-Extraktions-Tool, das echte Emails unserer Professorin analysiert. Mit Browser-Entwicklertools ("Element untersuchen") kopierten wir die HTML-Struktur authentischer Universitäts-Emails und verarbeiteten sie mit unserem Extraktions-Tool. Dieses Tool identifizierte und bewahrte automatisch:

- Typografie-Spezifikationen (Times New Roman, 12pt)
- Logo-Platzierung und -Größe
- Signatur-Struktur und -Formatierung
- Footer-Elemente und Abstände
- Farbschemata und Layout-Muster

Der Email-Generator verwendet dann diese extrahierte Vorlage, um benutzerdefinierten Nachrichteninhalt in authentisch aussehende universitäre Formatierung zu verpacken, wobei automatisch Logos, Signaturen und institutionelles Branding hinzugefügt werden. Jede generierte Email ist visuell nicht von legitimen Universitätskommunikationen zu unterscheiden.

### 2️⃣ Tracking-Server

**Zweck**: Erfassung umfassender Interaktionsdaten, wenn Empfänger auf eingebettete Links klicken.

**Funktionsweise**: Eine Flask-basierte Webanwendung, die auf Render's Cloud-Plattform bereitgestellt wird, dient als unser Tracking-Endpunkt. Wenn Empfänger auf Links in unseren Emails klicken, senden ihre Browser HTTP-Requests an diesen Server. Die Flask-Anwendung:

- Extrahiert Empfänger-Email-Adressen aus URL-Parametern
- Leitet automatisch Namen durch String-Parsing-Algorithmen ab
- Analysiert User-Agent-Header zur Identifikation von Browser, OS und Gerätetyp
- Erfasst IP-Adressen aus HTTP-Request-Metadaten
- Fragt ip-api.com's Geolokalisierungsdienst für ungefähre Standortdaten ab
- Zeichnet präzise Zeitstempel in Europe/Berlin-Zeitzone auf
- Speichert alle Daten in SQLite-Datenbank in <200 Millisekunden
- Sendet HTTP 302 Redirects zu einer Decoy-Fehlerseite

Der gesamte Prozess läuft so schnell ab, dass Nutzer die Tracking-Server-URL nur kurz sehen, bevor sie zu unserer Cloudflare-gehosteten Decoy-Seite weitergeleitet werden, die eine realistische "404 Error" Nachricht anzeigt.

### 3️⃣ SQLite-Datenbank

**Zweck**: Persistente Speicherung aller erfassten Interaktionsdaten für die Analyse.

**Funktionsweise**: Wir verwenden SQLite, eine dateibasierte relationale Datenbank, die keinen separaten Serverprozess benötigt. Jede Klick-Interaktion erzeugt eine Datenbankzeile mit 13 Feldern:

- Benutzer-Identifikation (Name, Email)
- Technische Umgebung (Browser, OS, Gerät)
- Netzwerk-Kontext (IP, Land, Region, Stadt, PLZ, ISP)
- Zeitliche Daten (Zeitstempel)

Die Datenbankdatei (`tracking.db`) befindet sich im Dateisystem des Render-Servers und bietet ACID-Transaktionsgarantien, während sie für unsere experimentelle Größenordnung von 15 Teilnehmern ausreichend einfach bleibt.

### 4️⃣ Analytics-Dashboard

**Zweck**: Echtzeit-Visualisierung und Analyse der gesammelten Daten.

**Funktionsweise**: Eine Web-Oberfläche, die über unsere Render-Domain zugänglich ist, präsentiert aggregierte Statistiken (Gesamt-Klicks, Browser-Diversität, geografische Verteilung) neben einer detaillierten Tabelle, die jedes einzelne Klick-Event mit vollständigen Metadaten zeigt. Das Dashboard bietet eine Dark-Mode-Ästhetik mit technischem Styling, interaktiven Hover-Effekten und CSV-Export-Funktionalität für Offline-Statistikanalyse.

---

## 🧪 Experimentelle Methodik

Wir führten eine zweiphasige Email-Kampagne durch, die 15 Studierende unseres Kurses "Risk and Rewards of Generative AI in Business" ins Visier nahm.

### Phase 1: Vorweihnachtliche Kampagne
- **Datum**: 20. Dezember 2025, 00:00 Uhr (Mitternacht)
- **Betreff**: "Reading Materials for Semester Break"
- **Ansatz**: Subtile Dringlichkeitsrahmung ("please make sure to go through the readings")
- **Email-Stil**: Präzise Replikation der Kommunikationsmuster der Professorin
- **Domain**: Versandt via IONOS SMTP mit uni-hamburg.net Domain
- **Ergebnis**: 10 Klicks

### Phase 2: Nachw eihnachtliches Follow-Up
- **Datum**: 2. Januar 2026, 20:39 Uhr
- **Betreff**: "Happy New Year - Updated Link for Reading Materials"
- **Ansatz**: Explizite Deeskalation ("purely optional"), Erklärung von Server-Problemen
- **Ergebnis**: 4 zusätzliche Klicks

### Technische Details
- **Personalisierung**: Jeder der 15 Studierenden erhielt eine individuell angepasste Email mit einem eindeutigen Tracking-Link, der ihre Email-Adresse als URL-Parameter enthielt
- **Email-Service**: IONOS SMTP (smtp.ionos.de:587) für authentifizierte Email-Übertragung
- **Beobachtungszeitraum**: 20. Dezember 2025 - 4. Januar 2026 (16 Tage)

---

## 📊 Ergebnisse

### Quantitative Befunde

- **Teilnehmer-Click-Through-Rate**: 33,3% (5 von 15 Studierenden)
- **Gesamt-Klick-Events**: 14 über beide Kampagnen
- **Durchschnittliche Klicks pro klickender Teilnehmer**: 2,8
- **Erste Email**: 10 Klicks
- **Zweite Email**: 4 Klicks (trotz expliziter "optional"-Rahmung)

### Verhaltensmuster

Alle 5 Teilnehmer, die klickten, engagierten sich mehrfach, was auf persistente Interaktion selbst nach nicht funktionierenden Links hindeutet. Die substanzielle Verzögerung zwischen den Kampagnen (13 Tage) kombiniert mit fortgesetztem Engagement zeigt, dass Phishing-Anfälligkeit über verschiedene zeitliche Kontexte und Dringlichkeitsrahmungen hinweg bestehen bleibt.

### Technische Performance

- **Server-Uptime**: 99,9% (Render Cloud-Plattform)
- **Response-Latenz**: Durchschnittlich 150ms vom Klick bis zum Datenbank-Commit
- **Datenintegrität**: Null verlorene Datensätze - alle Klick-Events erfolgreich erfasst
- **Geografische Abdeckung**: Erfolgreich geolokalisiert Hamburg und Umgebung (Reinbek, Glinde)

---

## 🔍 Zentrale Forschungsergebnisse

### 1. Phishing-Systeme sind einfach zu bauen

Ich habe diese vollständige Implementation - einschließlich Email-Templates, Cloud-Hosting, Tracking-Infrastruktur und Analytics-Dashboard - mit mittleren Python-Programmierkenntnissen und Unterstützung durch KI-gestützte Entwicklungstools und Prompting-Techniken gebaut. Die monatlichen Gesamtkosten bleiben unter 10 Dollar (Render-Hosting + IONOS-Domain). Es waren keine spezialisierten Cybersecurity-Expertise oder teure Tools erforderlich. Alle Komponenten nutzen Mainstream-Technologien: Python, Flask, SQLite, erschwingliches Cloud-Hosting und kostenlose APIs. Dies zeigt, dass ausgefeilte Phishing-Fähigkeiten nicht mehr exklusiv für professionelle Hacker sind - jeder mit grundlegenden Programmierkenntnissen und Zugang zu KI-Unterstützung kann sie erstellen.

### 2. Studierende bleiben trotz Awareness anfällig

33,3% der Teilnehmer klickten auf unsere Phishing-Emails, obwohl sie in einem Kurs eingeschrieben waren, der sich explizit mit KI-Risiken und Cybersecurity befasst. Diese Studierenden besitzen theoretisches Wissen, dass Phishing-Bedrohungen existieren und verstehen Social-Engineering-Taktiken, dennoch engagierten sie sich mit unseren sorgfältig gestalteten Simulationen. Dieser Befund untermauert existierende Forschung (Kumaraguru et al., 2009; Alsharnouby et al., 2015), die zeigt, dass theoretisches Wissen nicht zuverlässig vorsichtige Verhaltensreaktionen produziert.

### 3. Institutionelles Vertrauen überschreibt kritisches Denken

Selbst als unsere zweite Email explizit erklärte, Materialien seien "purely optional" und die Dringlichkeit reduzierte, klickten Teilnehmer weiterhin. Die Kombination aus authentischem Email-Stil unserer Professorin, Universitäts-Logo, institutioneller Domain (uni-hamburg.net) und professioneller Formatierung erzeugte automatische Vertrauensreaktionen. Studierende begegneten Kommunikationen, die vertraut und offiziell erschienen, was Compliance ohne kritische Evaluation auslöste. Dies demonstriert, dass Autoritätssignalisierung und visuelle Authentizität mächtige psychologische Trigger bleiben, die theoretisches Bewusstsein überschreiben.

---

## 💻 Technischer Stack

| Komponente | Technologie | Zweck |
|-----------|------------|---------|
| **Programmiersprache** | Python 3.13 | Kern-Entwicklungssprache |
| **Web-Framework** | Flask 3.0.0 | HTTP-Server und Routing |
| **Datenbank** | SQLite 3 | Datenpersistenz |
| **Cloud-Plattform** | Render.com | 24/7 Server-Hosting |
| **Email-Service** | IONOS SMTP | Authentifizierte Email-Übertragung |
| **Domain** | uni-hamburg.net | Institutionelle Glaubwürdigkeit |
| **Geolocation-API** | ip-api.com | IP-Adressen-Auflösung |
| **Static Hosting** | Cloudflare Pages | Decoy-Fehlerseiten-Bereitstellung |
| **HTML-Parsing** | BeautifulSoup | Template-Extraktion |
| **Zeitzone-Handling** | pytz | Deutsche Zeit-Lokalisierung |

**Monatliche Gesamtkosten**: <10€ (7€ Render + 1€ Domain)

---

## 🔐 Datenschutz & Sicherheit

### Was wir erfassen
- Email-Adressen (aus URL-Parametern)
- Namen (automatisch aus Email-Adressen extrahiert)
- Browser- und Geräteinformationen (aus User-Agent-Headern)
- IP-Adressen (aus HTTP-Requests)
- Ungefähre Geolocation (Land, Region, Stadt, PLZ via ip-api.com)
- Internet Service Provider-Identifikation
- Präzise Zeitstempel in deutscher Zeitzone

### Was wir NICHT erfassen
- ❌ Passwörter oder Zugangsdaten (keine Fake-Login-Seiten)
- ❌ Präzise GPS-Koordinaten (nur Stadt-Ebenen-Approximation)
- ❌ Tracking-Cookies oder persistente Identifikatoren
- ❌ Jegliche Daten jenseits des einzelnen Klick-Events

### Geolocation-Limitierungen

IP-basierte Geolocation bietet nur ungefähre Positionsbestimmung. Das System identifiziert, wo Internet-Service-Provider-Infrastruktur registriert ist, nicht die tatsächlichen physischen Standorte der Nutzer. Tests zeigten substanzielle Ungenauigkeiten:

- Universitätsgebäude (Von-Melle-Park 5, PLZ 20146) → System zeigte 22303 (Uni-Gateway-Standort)
- Glinde → System zeigte Reinbek (nahegelegene Stadt, ISP-Routing)

Dies stellt eine fundamentale Limitation der IP-Geolocation-Technologie dar, die keine spezifischen Gebäude oder Adressen lokalisieren kann.

---

## 📚 Akademische Referenzen

Dieses Projekt baut auf etablierter Forschung zu Phishing-Anfälligkeit und Cybersecurity-Bildung auf:

- **Kumaraguru, P., et al. (2009)**. Teaching Johnny not to fall for phish. *ACM Transactions on Internet Technology, 10*(2), Article 7.

- **Alsharnouby, M., et al. (2015)**. Why phishing still works: User strategies for combating phishing attacks. *International Journal of Human-Computer Studies, 82*, 69-82.

- **Liaqat, M. S., et al. (2024)**. Exploring phishing attacks in the AI age: A comprehensive literature review. *Journal of Computing & Biomedical Informatics, 7*(2). https://doi.org/10.56979/702/2024

- **Anti-Phishing Working Group (2024)**. Phishing activity trends report, 4th quarter 2024. Abgerufen von https://apwg.org/trendsreports/

- **Cialdini, R. B. (2006)**. *Influence: The psychology of persuasion*. Harper Business.

---

## 🎓 Bildungsimplikationen

Unsere Befunde legen klare Richtungshinweise für Cybersecurity-Bildung nahe:

**Passives Training ist unzureichend**  
Traditionelle vorlesungsbasierte Ansätze, die theoretisches Wissen betonen, zeigen begrenzte Auswirkungen auf tatsächliches Verhalten, wenn Studierende mit realistischen Phishing-Szenarien konfrontiert werden.

**Erfahrungsbasiertes Lernen ist notwendig**  
Studierende benötigen hands-on Exposition zu realistischen Phishing-Angriffen in kontrollierten Umgebungen, gekoppelt mit sofortigem personalisiertem Feedback, das konkrete Konsequenzen von Verwundbarkeit demonstriert.

**Autoritätssignalisierung zählt**  
Selbst explizite Warnungen über optionale Inhalte verhindern keine Klicks, wenn Emails institutionelle Authentizitätsmarker wie professionelle Formatierung und vertrauenswürdige Absender-Identitäten beibehalten.

---

## ⚖️ Lizenz & Haftungsausschluss

**Nur akademische Nutzung**

Dieses System wurde ausschließlich für akademische Forschungszwecke entwickelt. Die Autoren übernehmen keine Verantwortung für Missbrauch, illegale Nutzung oder jegliche Aktivitäten ohne angemessene ethische Aufsicht.

### Verbotene Verwendungen
- Unerlaubte Phishing-Angriffe gegen nicht zustimmende Personen
- Credential-Diebstahl oder Passwort-Harvesting
- Datenschutzverletzungen oder unerlaubte Datensammlung
- Jegliche Aktivitäten, die Computer-Betrugsgesetze verletzen

### Erlaubte Verwendungen
- Akademische Forschung mit institutioneller ethischer Genehmigung
- Cybersecurity-Bildung in überwachten, kontrollierten Umgebungen
- Awareness-Trainingsprogramme mit expliziter Teilnehmer-Zustimmung
- Replikationsstudien unter Einhaltung angemessener ethischer Protokolle

---

## 🔬 Methodische Hinweise

### Stichproben-Limitierungen
Unser Experiment umfasste nur 15 Teilnehmer aus einem einzelnen Kurs an einer Universität. Ergebnisse generalisieren möglicherweise nicht auf breitere Studierendenpopulationen, unterschiedliche institutionelle Kontexte oder andere demografische Gruppen.

### Kontext-Spezifität
Die Einschreibung der Teilnehmer in einen Kurs, der explizit KI-Risiken adressiert, könnte Ergebnisse beeinflusst haben. Wirklich ahnungslose Opfer könnten noch höhere Verwundbarkeitsraten zeigen.

### Klick-Events vs. Eindeutige Teilnehmer
Unser System trackt individuelle Klick-Events. Die 5 Teilnehmer, die klickten, generierten 14 Gesamt-Klicks (durchschnittlich 2,8 Klicks pro Person), was wiederholte Engagement-Versuche nach initialen Link-Fehlern indiziert.

---

<div align="center">

## 💡 Das Fazit

**Phishing-Angriffe sind nicht mehr exklusiv für professionelle Hacker.**

Moderne Tools, Cloud-Services und KI-Sprachmodelle haben ausgefeilte Social-Engineering-Fähigkeiten demokratisiert. Jeder mit grundlegenden Programmierkenntnissen kann jetzt überzeugende Phishing-Kampagnen zu minimalen Kosten erstellen.

**Theoretisches Wissen allein kann Nutzer nicht schützen.**

Selbst Studierende, die Cybersecurity studieren, bleiben anfällig, wenn sie mit realistischen Emails von vertrauenswürdigen Autoritäten konfrontiert werden. Effektive Verteidigung erfordert erfahrungsbasiertes Lernen, nicht nur passive Instruktion.

**Mit großer Macht kommt große Verantwortung.**

Nutzen Sie dieses Wissen, um Sicherheitsbewusstsein zu verbessern, nicht um anderen zu schaden.

</div>

---

*Für Fragen zur Forschungsmethodik oder ethischen Überlegungen kontaktieren Sie:*  https://vinaydiwan.netlify.app
*Universität Hamburg, Fakultät für Betriebswirtschaftslehre*

**🔒 Denken Sie daran: Holen Sie immer die entsprechende Genehmigung ein, bevor Sie Sicherheitsforschung durchführen.**
