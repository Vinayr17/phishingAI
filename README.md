<div align="center">

# 🎣 Phishing Simulation System

### An AI-powered phishing simulation platform demonstrating the accessibility and effectiveness of modern social engineering attacks in educational contexts

---

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/UHH_Universit%C3%A4t_Hamburg_Logo_mit_Schrift_2010_Farbe_CMYK.svg/500px-UHH_Universit%C3%A4t_Hamburg_Logo_mit_Schrift_2010_Farbe_CMYK.svg.png" width="300" alt="Universität Hamburg Logo"/>

**Developed at Universität Hamburg**  
*Risk and Rewards of Generative AI in Business*  
*Winter Semester 2024/2025*

---

</div>

---

## ⚠️ Ethical Notice

**This project is strictly for educational and research purposes.**

All experiments were conducted under ethical supervision with explicit instructor approval. Participants received comprehensive debriefing following data collection. This system should never be used for unauthorized activities or malicious purposes.

---

## 📖 About This Project

This research project investigates the intersection of generative AI, social engineering, and cybersecurity education by building and deploying a complete phishing simulation system. I developed the entire technical implementation - from email generation to tracking infrastructure to analytics dashboard - as the technical component of a broader group research project. The project demonstrates a critical finding: creating sophisticated phishing campaigns has become remarkably accessible through modern cloud infrastructure, open-source tools, and AI assistance (including AI-powered development support and prompting), requiring only intermediate programming knowledge and minimal financial investment.

Through a controlled experiment targeting university students enrolled in a cybersecurity-focused course, we provide empirical evidence that theoretical awareness of phishing threats does not reliably translate into cautious behavioral responses when individuals encounter realistic communications from trusted institutional sources.

## 🎯 Research Objectives

Our project addresses three interconnected objectives:

**1. Technical Implementation**  
I designed and deployed a fully functional phishing simulation infrastructure that replicates the capabilities available to real-world attackers, including automated email generation, real-time interaction tracking, and comprehensive metadata collection. Development was supported by AI-assisted coding tools and prompting techniques.

**2. Proof of Concept**  
Demonstrate the technical accessibility of sophisticated phishing systems by documenting exact costs, explaining every architectural decision, and proving that students with intermediate programming skills can create convincing attack simulations using exclusively mainstream development tools.

**3. Empirical Awareness Research**  
Collect real behavioral data from participants within our academic community to measure actual phishing susceptibility rather than relying on theoretical assumptions, thereby contributing evidence-based insights to cybersecurity education.

---

## 🏗️ System Architecture

Our system comprises four integrated components working together to simulate, track, and analyze phishing interactions:

### 1️⃣ Email Generation Module

**Purpose**: Create institutionally authentic emails that precisely replicate university communication patterns.

**How it works**: I developed a custom HTML extraction tool that analyzes real emails from our professor. Using browser developer tools ("Inspect Element"), we copied the HTML structure of authentic university emails and processed it through our extraction tool. This tool automatically identified and preserved:

- Typography specifications (Times New Roman, 12pt)
- Logo placement and sizing
- Signature structure and formatting
- Footer elements and spacing
- Color schemes and layout patterns

The email generator then uses this extracted template to wrap custom message content in authentic-looking university formatting, automatically adding logos, signatures, and institutional branding. Each generated email is visually indistinguishable from legitimate university communications.

### 2️⃣ Tracking Server

**Purpose**: Capture comprehensive interaction data when recipients click embedded links.

**How it works**: A Flask-based web application deployed on Render's cloud platform serves as our tracking endpoint. When recipients click links in our emails, their browsers send HTTP requests to this server. The Flask application:

- Extracts recipient email addresses from URL parameters
- Automatically derives names through string parsing algorithms
- Analyzes User-Agent headers to identify browser, OS, and device type
- Captures IP addresses from HTTP request metadata
- Queries ip-api.com's geolocation service for approximate location data
- Records precise timestamps in Europe/Berlin timezone
- Commits all data to SQLite database in <200 milliseconds
- Issues HTTP 302 redirects to a decoy error page

The entire process happens so quickly that users only briefly see the tracking server URL before being redirected to our Cloudflare-hosted decoy page displaying a realistic "404 Error" message.

### 3️⃣ SQLite Database

**Purpose**: Persistently store all captured interaction data for analysis.

**How it works**: We use SQLite, a file-based relational database requiring no separate server process. Each click interaction generates one database row containing 13 fields:

- User identification (name, email)
- Technical environment (browser, OS, device)
- Network context (IP, country, region, city, postal code, ISP)
- Temporal data (timestamp)

The database file (`tracking.db`) resides on the Render server's filesystem, providing ACID transaction guarantees while remaining simple enough for our experimental scale of 15 participants.

### 4️⃣ Analytics Dashboard

**Purpose**: Provide real-time visualization and analysis of collected data.

**How it works**: A web interface accessible at our Render domain presents aggregate statistics (total clicks, browser diversity, geographic distribution) alongside a detailed table showing every individual click event with complete metadata. The dashboard features a dark mode aesthetic with technical styling, interactive hover effects, and CSV export functionality for offline statistical analysis.

---

## 🧪 Experimental Methodology

We conducted a two-phase email campaign targeting 15 students enrolled in our "Risk and Rewards of Generative AI in Business" course.

### Phase 1: Pre-Holiday Campaign
- **Date**: December 20, 2025, 00:00 (midnight)
- **Subject**: "Reading Materials for Semester Break"
- **Approach**: Subtle urgency framing ("please make sure to go through the readings")
- **Email Style**: Precise replication of professor's communication patterns
- **Domain**: Sent via IONOS SMTP using uni-hamburg.net domain
- **Result**: 10 clicks

### Phase 2: Post-Holiday Follow-Up
- **Date**: January 2, 2026, 20:39
- **Subject**: "Happy New Year - Updated Link for Reading Materials"
- **Approach**: Explicit de-escalation ("purely optional"), explained server issues
- **Result**: 4 additional clicks

### Technical Details
- **Personalization**: Each of the 15 students received an individually customized email with a unique tracking link containing their email address as a URL parameter
- **Email Service**: IONOS SMTP (smtp.ionos.de:587) for authenticated email transmission
- **Observation Period**: December 20, 2025 - January 4, 2026 (16 days)

---

## 📊 Results

### Quantitative Findings

- **Participant Click-Through Rate**: 33.3% (5 out of 15 students)
- **Total Click Events**: 14 across both campaigns
- **Average Clicks per Clicking Participant**: 2.8
- **First Email**: 10 clicks
- **Second Email**: 4 clicks (despite explicit "optional" framing)

### Behavioral Patterns

All 5 participants who clicked engaged multiple times, suggesting persistent interaction even after encountering non-functional links. The substantial delay between campaigns (13 days) combined with continued engagement demonstrates that phishing vulnerability persists across different temporal contexts and urgency framings.

### Technical Performance

- **Server Uptime**: 99.9% (Render cloud platform)
- **Response Latency**: Average 150ms from click to database commit
- **Data Integrity**: Zero lost records - all click events successfully captured
- **Geographic Coverage**: Successfully geolocated Hamburg and surrounding areas (Reinbek, Glinde)

---

## 🔍 Key Research Findings

### 1. Phishing Systems Are Easy to Build

I built this complete implementation - including email templates, cloud hosting, tracking infrastructure, and analytics dashboard - using intermediate Python programming skills with support from AI-assisted development tools and prompting techniques. Total monthly operating costs remain under $10 (Render hosting + IONOS domain). No specialized cybersecurity expertise or expensive tools were necessary. All components utilize mainstream, publicly available technologies: Python, Flask, SQLite, affordable cloud hosting, and free APIs. This demonstrates that sophisticated phishing capabilities are no longer exclusive to professional hackers - anyone with basic coding proficiency and access to AI assistance can create them.

### 2. Students Remain Vulnerable Despite Awareness

33.3% of participants clicked on our phishing emails despite being enrolled in a course explicitly addressing AI risks and cybersecurity. These students possess theoretical knowledge that phishing threats exist and understand social engineering tactics, yet they still engaged with our carefully crafted simulations. This finding reinforces existing research (Kumaraguru et al., 2009; Alsharnouby et al., 2015) demonstrating that theoretical knowledge does not reliably produce cautious behavioral responses.

### 3. Institutional Trust Overrides Critical Thinking

Even when our second email explicitly stated materials were "purely optional" and reduced urgency, participants continued to click. The combination of our professor's authentic email style, university logo, institutional domain (uni-hamburg.net), and professional formatting created automatic trust responses. Students encountered communications that appeared familiar and official, triggering compliance without critical evaluation. This demonstrates that authority signaling and visual authenticity remain powerful psychological triggers that override theoretical awareness.

---

## 💻 Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Programming Language** | Python 3.13 | Core development language |
| **Web Framework** | Flask 3.0.0 | HTTP server and routing |
| **Database** | SQLite 3 | Data persistence |
| **Cloud Platform** | Render.com | 24/7 server hosting |
| **Email Service** | IONOS SMTP | Authenticated email transmission |
| **Domain** | uni-hamburg.net | Institutional credibility |
| **Geolocation API** | ip-api.com | IP address resolution |
| **Static Hosting** | Cloudflare Pages | Decoy error page delivery |
| **HTML Parsing** | BeautifulSoup | Template extraction |
| **Timezone Handling** | pytz | German time localization |

**Total Monthly Cost**: <$10 ($7 Render + $1 domain)

---

## 🔐 Data Privacy & Security

### What We Collect
- Email addresses (from URL parameters)
- Names (automatically extracted from email addresses)
- Browser and device information (from User-Agent headers)
- IP addresses (from HTTP requests)
- Approximate geolocation (country, region, city, postal code via ip-api.com)
- Internet Service Provider identification
- Precise timestamps in German timezone

### What We DON'T Collect
- ❌ Passwords or credentials (no fake login pages)
- ❌ Precise GPS coordinates (only city-level approximation)
- ❌ Tracking cookies or persistent identifiers
- ❌ Any data beyond the single click event

### Geolocation Limitations

IP-based geolocation provides only approximate positioning. The system identifies where internet service provider infrastructure is registered, not users' actual physical locations. Testing revealed substantial inaccuracies:

- University building (Von-Melle-Park 5, postal code 20146) → System showed 22303 (university gateway location)
- Glinde → System showed Reinbek (nearby town, ISP routing)

This represents a fundamental limitation of IP geolocation technology, which cannot pinpoint specific buildings or addresses.

---

## 📚 Academic References

This project builds upon established research in phishing susceptibility and cybersecurity education:

- **Kumaraguru, P., et al. (2009)**. Teaching Johnny not to fall for phish. *ACM Transactions on Internet Technology, 10*(2), Article 7.

- **Alsharnouby, M., et al. (2015)**. Why phishing still works: User strategies for combating phishing attacks. *International Journal of Human-Computer Studies, 82*, 69-82.

- **Liaqat, M. S., et al. (2024)**. Exploring phishing attacks in the AI age: A comprehensive literature review. *Journal of Computing & Biomedical Informatics, 7*(2). https://doi.org/10.56979/702/2024

- **Anti-Phishing Working Group (2024)**. Phishing activity trends report, 4th quarter 2024. Retrieved from https://apwg.org/trendsreports/

- **Cialdini, R. B. (2006)**. *Influence: The psychology of persuasion*. Harper Business.

---

## 🎓 Educational Implications

Our findings suggest clear directional guidance for cybersecurity education:

**Passive Training Is Insufficient**  
Traditional lecture-based approaches that emphasize theoretical knowledge demonstrate limited impact on actual behavior when students confront realistic phishing scenarios.

**Experiential Learning Is Necessary**  
Students require hands-on exposure to realistic phishing attacks in controlled environments, coupled with immediate personalized feedback demonstrating concrete consequences of vulnerability.

**Authority Signaling Matters**  
Even explicit warnings about optional content fail to prevent clicks when emails maintain institutional authenticity markers like professional formatting and trusted sender identities.

---

## ⚖️ License & Disclaimer

**Academic Use Only**

This system was developed exclusively for academic research purposes. The authors assume no responsibility for misuse, illegal use, or any activities conducted without proper ethical oversight.

### Prohibited Uses
- Unauthorized phishing attacks against non-consenting individuals
- Credential theft or password harvesting
- Privacy violations or unauthorized data collection
- Any activities violating computer fraud laws

### Permitted Uses
- Academic research with institutional ethical approval
- Cybersecurity education in supervised, controlled environments
- Awareness training programs with explicit participant consent
- Replication studies following proper ethical protocols

---

## 🔬 Methodological Notes

### Sample Size Limitations
Our experiment involved only 15 participants from a single course at one university. Results may not generalize to broader student populations, different institutional contexts, or other demographic groups.

### Context Specificity
Participants' enrollment in a course explicitly addressing AI risks may have influenced results. Truly unsuspecting victims might demonstrate even higher vulnerability rates.

### Click Events vs. Unique Participants
Our system tracks individual click events. The 5 participants who clicked generated 14 total clicks (averaging 2.8 clicks per person), indicating repeated engagement attempts after initial link failures.

---

<div align="center">

## 💡 The Bottom Line

**Phishing attacks are no longer exclusive to professional hackers.**

Modern tools, cloud services, and AI language models have democratized sophisticated social engineering capabilities. Anyone with basic programming knowledge can now create convincing phishing campaigns at minimal cost.

**Theoretical knowledge alone cannot protect users.**

Even students studying cybersecurity remain vulnerable when confronted with realistic emails from trusted authorities. Effective defense requires experiential learning, not just passive instruction.

**With great power comes great responsibility.**

Use this knowledge to improve security awareness, not to harm others.

</div>

---

*For questions about research methodology or ethical considerations, contact: vinaydiwan.netlify.app  
*University of Hamburg, Faculty of Business Administration*

**🔒 Remember: Always obtain proper authorization before conducting security research.**
