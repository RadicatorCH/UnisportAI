# 🎯 UnisportAI

Eine intelligente Streamlit-basierte Webanwendung zur Entdeckung und Verwaltung von Sportangeboten an der Universität St.Gallen (HSG).

## 📖 Inhaltsverzeichnis

- [Projektübersicht](#-projektübersicht)
- [Features](#-features)
- [Technologie-Stack](#-technologie-stack)
- [Schnellstart](#-schnellstart)
- [Detaillierte Installation](#-detaillierte-installation)
- [Projektarchitektur](#-projektarchitektur)
- [Entwickler-Guide](#-entwickler-guide)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Kontakt & Support](#-kontakt--support)

## 🎉 Projektübersicht

UnisportAI ist eine moderne Webanwendung, die es Studierenden und Mitarbeitern der Universität St.Gallen ermöglicht, Sportkurse zu entdecken, zu filtern und zu verwalten. Die App bietet eine intuitive Benutzeroberfläche mit erweiterten Filtermöglichkeiten, Bewertungssystem, persönlichem Kalender und Community-Features.

**Was macht diese App besonders?**

- 🔐 **Sichere Authentifizierung**: Google OAuth Integration - kein Passwort nötig
- 📊 **Intelligente Filterung**: Finde den perfekten Kurs nach Zeit, Ort, Intensität und mehr
- ⭐ **Community-Bewertungen**: Sieh Bewertungen von anderen Teilnehmern
- 📅 **Kalender-Integration**: Importiere deine Kurse in Google Calendar, Outlook, etc.
- 👥 **Soziale Features**: Finde Freunde und sehe wer noch teilnimmt
- 📱 **Mobile-freundlich**: Funktioniert auf allen Geräten

## ✨ Features

### 🔐 Authentifizierung & Sicherheit

- **Google OAuth 2.0**: Sicherer Login ohne Passwort
- **Automatische Benutzer-Synchronisation** mit Supabase
- **Terms of Service & Privacy Policy** Acceptance
- **GDPR-konforme** Datenverarbeitung
- **Personalisierte Tokens** für iCal-Feeds
- **Session Management** mit automatischer Token-Erneuerung

### 📊 Sportangebot-Management

- **Übersicht aller Kurse** mit Filtermöglichkeiten
- **Detailansicht** für einzelne Aktivitäten
- **Wochenansicht** aller verfügbaren Termine
- **Trainer-Informationen** mit Bewertungen
- **Kursbilder** und visuelle Darstellung
- **Intensitäts-Filter**: Leicht, Mittel, Intensiv
- **Fokus-Filter**: Ausdauer, Kraft, Flexibilität, etc.
- **Setting-Filter**: Indoor, Outdoor, Wasser, etc.

### 📅 Kalender & Terminverwaltung

- **Wochenkalender** mit allen Terminen
- **iCal Feed** für persönliche Kalender-Integration
- **Erinnerungen** 15 Minuten vor Kursbeginn
- **Anmeldungs-Tracking**: "Going" Funktion
- **Abgesagte Kurse** automatisch ausgeblendet
- **Multi-Termin-Auswahl** für direkte Navigation

### 👥 Community Features

- **Freundesystem**: Finde Sport-Freunde
- **Benachrichtigungen**: Sieh wer noch teilnimmt
- **Bewertungssystem**: Bewerte Kurse und Trainer
- **Profile-Management**: Persönliche Einstellungen
- **Athleten-Vermittlung**: Finde Trainingspartner

### 🔧 Admin-Funktionen

- **User Management**: Benutzerübersicht und Verwaltung
- **Bulk-Operations**: Massen-Aktionen für alle Nutzer
- **System-Statistiken**: Überblick über Nutzung und Daten
- **Rollen-Management**: Admin-Berechtigungen

## 🛠 Technologie-Stack

Diese Anwendung nutzt moderne Web- und Cloud-Technologien:

| Technologie | Zweck | Version |
|------------|------|---------|
| **Python** | Programmiersprache | 3.9+ |
| **Streamlit** | Web-Framework | Latest |
| **Supabase** | Backend-as-a-Service | Cloud |
| **Google OAuth** | Authentifizierung | OIDC |
| **PostgreSQL** | Datenbank | (via Supabase) |

**Hauptbibliotheken:**
- `streamlit` - Web UI Framework
- `st-supabase` - Supabase Connection für Streamlit
- `python-dateutil` - Datum-Handling
- Weitere Abhängigkeiten (siehe `requirements.txt`)

## 🚀 Schnellstart

### Voraussetzungen

Bevor du startest, stelle sicher dass du folgendes installiert hast:

- **Python 3.9 oder höher** ([Download](https://www.python.org/downloads/))
- **pip** (meist automatisch mit Python installiert)
- **Git** ([Download](https://git-scm.com/downloads))
- **Ein Google-Konto** (für OAuth)
- **Supabase Account** (kostenlos auf [supabase.com](https://supabase.com))

> 💡 **Tipp**: Überprüfe deine Python-Version mit `python --version` im Terminal.

### Schritt 1: Repository klonen

```bash
git clone https://github.com/deinusername/unisport.git
cd unisport
```

### Schritt 2: Abhängigkeiten installieren

Erstelle zunächst eine virtuelle Umgebung (empfohlen für Python-Projekte):

```bash
# Erstelle virtuelle Umgebung
python -m venv venv

# Aktiviere virtuelle Umgebung
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Installiere Abhängigkeiten
pip install -r requirements.txt
```

> 💡 **Was ist eine virtuelle Umgebung?** Sie isoliert Python-Pakete deines Projekts von anderen Projekten auf deinem Computer, um Konflikte zu vermeiden.

### Schritt 3: Supabase Setup

1. Gehe zu [supabase.com](https://supabase.com) und erstelle einen kostenlosen Account
2. Erstelle ein neues Projekt
3. Notiere dir die **Project URL** und **API Key** aus deinen Project Settings

### Schritt 4: Google OAuth konfigurieren

1. Gehe zu [Google Cloud Console](https://console.cloud.google.com/)
2. Erstelle ein neues Projekt oder wähle ein bestehendes
3. Aktiviere die **Google+ API**
4. Erstelle OAuth 2.0 Credentials
5. Konfiguriere Redirect URIs (siehe [Detaillierte Installation](#google-oauth-setup))

### Schritt 5: Secrets konfigurieren

Erstelle eine Datei `.streamlit/secrets.toml` (im Hauptverzeichnis):

```toml
[connections.supabase]
url = "https://xxxxx.supabase.co"
key = "dein-api-key-hier"

[auth]
cookie_secret = "ein-mindestens-32-zeichen-langes-geheimnis"

[auth.google]
client_id = "deine-google-client-id"
client_secret = "dein-google-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

> ⚠️ **Wichtig**: Füge `.streamlit/secrets.toml` zu `.gitignore` hinzu (bereits vorhanden), damit keine Secrets ins Repository hochgeladen werden!

### Schritt 6: App starten

```bash
streamlit run streamlit_app.py
```

Die App öffnet sich automatisch in deinem Browser unter `http://localhost:8501`.

---

## 📚 Detaillierte Installation

### Python Basics - Für Einsteiger

Wenn du Python noch nicht kennst, hier sind die Grundlagen:

**Was ist Python?**
Python ist eine benutzerfreundliche Programmiersprache, die oft für Webentwicklung, Datenanalyse und Automatisierung verwendet wird.

**Warum eine virtuelle Umgebung?**
- Verhindert Konflikte zwischen verschiedenen Projekten
- Jedes Projekt kann unterschiedliche Versionen von Bibliotheken verwenden
- Einfache Wartung und Deployment

### Supabase Setup - Schritt für Schritt

**Was ist Supabase?**
Supabase ist eine open-source Alternative zu Firebase und bietet Datenbank, Authentifizierung, Storage und mehr in einem Service.

**Warum Supabase?**
- PostgreSQL-Datenbank (mächtig und zuverlässig)
- Automatische API-Generierung
- Real-time Subscriptions
- Kostenlose Starter-Tier
- Open-Source

**Detaillierte Anleitung:**

1. **Account erstellen**:
   - Besuche [supabase.com](https://supabase.com)
   - Klicke auf "Start your project"
   - Melde dich mit GitHub, Google oder E-Mail an

2. **Neues Projekt erstellen**:
   - Klicke auf "New Project"
   - Wähle eine Organisation (oder erstelle eine neue)
   - Gib deinem Projekt einen Namen (z.B. "unisport")
   - Wähle eine Region nahe deinem Standort
   - Erstelle ein Master-Passwort (speichere es sicher!)
   - Klicke auf "Create new project"
   - Warte 2-3 Minuten bis das Projekt initialisiert ist

3. **Credentials holen**:
   - Gehe zu Project Settings → API
   - Kopiere die **Project URL** (beginnt mit `https://`)
   - Kopiere den **anon/public key**
   - Diese Daten brauchst du für `.streamlit/secrets.toml`

4. **Datenbank konfigurieren**:
   - Die App nutzt verschiedene Tabellen (siehe Projektarchitektur)
   - Diese werden automatisch über Migrations angelegt
   - Gehe zu SQL Editor in Supabase und führe die Migrations aus

**Häufige Fehler:**
- ❌ "Connection refused": Prüfe URL auf Tippfehler
- ❌ "Invalid API key": Hole den korrekten anon key
- ❌ "Row Level Security Error": Aktiviere RLS Policies

### Google OAuth Setup

**Was ist OAuth?**
OAuth ist ein Standard für sichere Authentifizierung ohne Passwort. Benutzer melden sich mit ihrem Google-Account an.

**Warum Google Login?**
- Keine eigenen Passwörter zu verwalten
- Vertraute Authentifizierung
- Fortgeschrittene Sicherheits-Features
- Einfache Integration

**Detaillierte Anleitung:**

1. **Google Cloud Console Setup**:
   ```
   1. Gehe zu: https://console.cloud.google.com/
   2. Klicke oben auf Projekt auswählen
   3. Klicke auf "NEUES PROJEKT"
   4. Gib einen Projektnamen ein (z.B. "UnisportAI")
   5. Klicke auf "Erstellen"
   6. Warte bis die Benachrichtigung erscheint
   ```

2. **OAuth Consent Screen konfigurieren**:
   - Im Menü links: APIs & Services → OAuth consent screen
   - Wähle "Internal" (für Organisation) oder "External" (öffentlich)
   - Fülle aus:
     - App-Name: UnisportAI
     - User support email: deine E-Mail
     - Developer contact: deine E-Mail
   - Klicke auf "Save and Continue"
   - Scope: Lasse Standard, klicke "Save and Continue"
   - Test Users (nur für External): Füge Test-E-Mails hinzu

3. **OAuth Credentials erstellen**:
   - Im Menü links: APIs & Services → Credentials
   - Klicke auf "+ CREATE CREDENTIALS"
   - Wähle "OAuth client ID"
   - Application type: "Web application"
   - Name: UnisportAI Client
   - **Authorized redirect URIs** hinzufügen:
     ```
     http://localhost:8501/oauth2callback
     https://unisportai.streamlit.app/oauth2callback
     ```
   - Klicke auf "Create"
   - **WICHTIG**: Kopiere sofort Client ID und Client Secret (nur einmal sichtbar!)

4. **Redirect URI Probleme vermeiden**:
   
   **Problem**: Streamlit verwendet verschiedene Ports lokal
   
   **Lösung**: Verwende einen festen Port:
   ```bash
   streamlit run streamlit_app.py --server.port 8501
   ```
   
   Oder füge mehrere URIs hinzu:
   ```
   http://localhost:8501/oauth2callback
   http://localhost:8502/oauth2callback
   ```

5. **Secrets aktualisieren**:
   Füge Client ID und Secret zu `.streamlit/secrets.toml` hinzu.

**Häufige Fehler:**
- ❌ "redirect_uri_mismatch": Prüfe dass URIs exakt übereinstimmen
- ❌ "invalid_client": Prüfe Client ID und Secret
- ❌ "This app isn't verified": Verwende Test User (External Mode)

### Datenbank-Migration

Die App nutzt eine PostgreSQL-Datenbank mit folgenden Haupt-Tabellen:

- `users` - Benutzerdaten
- `sportangebote_with_ratings` - Sportkurse mit Bewertungen
- `kurs_termine` - Einzelne Kurstermine
- `vw_termine_full` - View für Termine mit allen Daten
- `friend_course_notifications` - Freunde-Beziehungen

**Migrations ausführen:**

1. Öffne Supabase Dashboard
2. Gehe zu SQL Editor
3. Kopiere den Inhalt von `supabase/migrations/add_ical_feed_token.sql`
4. Führe die SQL-Statements aus
5. Wiederhole für weitere Migrationen

> 💡 **Was sind Views?** Views sind virtuelle Tabellen, die Daten aus mehreren Quellen kombinieren. Sie vereinfachen komplexe Queries.

## 🏗 Projektarchitektur

### Ordnerstruktur

```
Unisport/
├── streamlit_app.py          # 🚀 Entry Point - Haupt-Application
├── pages/                    # 📄 Streamlit Seiten
│   ├── overview.py           # Hauptübersicht aller Kurse
│   ├── details.py            # Detailansicht für Kurse
│   ├── calendar.py           # Wochenansicht aller Termine
│   ├── athletes.py           # Sportfreunde finden
│   ├── profile.py            # Benutzerprofil
│   └── admin.py              # Admin Panel (nur für Admins)
├── data/                     # 💾 Backend-Logik und Datenbank-Zugriff
│   ├── supabase_client.py    # Supabase Datenbank-Verbindung
│   ├── auth.py               # Authentifizierungslogik
│   ├── filters.py            # Filter-Funktionen
│   ├── shared_sidebar.py     # Gemeinsame Sidebar
│   ├── state_manager.py      # Session State Management
│   ├── rating.py             # Bewertungssystem
│   ├── security.py           # Sicherheits-Features
│   ├── tos_acceptance.py    # Terms of Service Acceptance
│   └── user_management.py    # Benutzerverwaltung
├── supabase/                 # 🗄 Datenbank und Edge Functions
│   ├── migrations/           # SQL-Migrationen
│   └── functions/
│       └── ical-feed/        # iCal Feed Edge Function
│           └── index.ts
└── docs/                     # 📚 Dokumentation
    ├── TERMS_OF_SERVICE.md
    └── PRIVACY_POLICY.md
```

### Datenfluss

```
1. Benutzer öffnet App → streamlit_app.py
   ↓
2. Prüfung auf Authentifizierung → auth.py
   ↓
3. Prüfung auf TOS Acceptance → tos_acceptance.py
   ↓
4. Navigation zu gewählter Seite → pages/*.py
   ↓
5. Laden von Daten aus Supabase → supabase_client.py
   ↓
6. Anwenden von Filtern → filters.py
   ↓
7. Darstellung in der UI → Streamlit Rendering
```

### Namenskonvention

Die App verwendet ein konsistentes Prefix-System für Variablen:

| Prefix | Verwendung | Beispiel |
|--------|-----------|----------|
| `offer_*` | Sportangebote | `offer.name`, `offer.href` |
| `event_*` | Einzelne Termine | `event.start_time`, `event.location` |
| `course_*` | Kurse | `course.kursnr`, `course.trainers` |
| `trainer_*` | Trainer-Info | `trainer.name`, `trainer.rating` |
| `location_*` | Standorte | `location.name`, `location.coords` |
| `state_*` | Session State | `state_sports_data`, `state_filters` |
| `filter_*` | Filter-Werte | `filter_intensity`, `filter_location` |

Dies erleichtert die Navigation im Code und verhindert Namenskonflikte.

### Module-Übersicht

#### streamlit_app.py
**Zweck**: Entry Point der Anwendung

**Aufgaben**:
- Prüft Authentifizierung
- Zeigt Login-Seite falls nicht eingeloggt
- Validiert Terms of Service Acceptance
- Regelt Navigation zwischen Seiten
- Zeigt Admin-Page nur für Admins

#### data/supabase_client.py
**Zweck**: Zentrale Datenbank-Verbindung

**Funktionen**:
- `get_offers_with_stats()` - Lädt alle Kurse mit Bewertungen
- `get_all_events()` - Lädt alle kommenden Termine
- `get_events_for_offer(href)` - Termine für bestimmten Kurs
- `create_or_update_user()` - Benutzer-Synchronisation
- Caching-Mechanismus für Performance

**Wichtige Pattern**: 
- Nutzt `@st.cache_data` für lokales Caching
- TTL (Time To Live) von 300-600 Sekunden
- Speicherefficient durch reduziere API-Calls

#### data/auth.py
**Zweck**: Authentifizierungs-Logik

**Funktionen**:
- `is_logged_in()` - Prüft Login-Status
- `show_login_page()` - Rendert Login-UI
- `check_token_expiry()` - Validiert Token-Gültigkeit
- `sync_user_to_supabase()` - Synchronisiert Benutzerdaten

#### data/filters.py
**Zweck**: Filter-Funktionen

**Konzept**: Stufenfiltrierung
1. Base-Filter: Suche, Intensität, Fokus, Setting
2. Detail-Filter: Datum, Zeit, Ort, Wochentag
3. Event-basiert: Filtert Kurse nach Termin-Kriterien

**Optimierung**: 
- Frühzeitiges Filtern reduziert Datenmenge
- Nested Filter für hohe Performance

#### pages/overview.py
**Zweck**: Hauptübersicht aller Sportkurse

**Features**:
- Karten-Layout für alle Kurse
- Filter-Sidebar
- Kommende Termine Vorschau
- Bewertungsanzeige
- Trainer-Info
- Navigations-Buttons

#### pages/details.py
**Zweck**: Detailansicht eines Kurses

**Features**:
- Alle kommenden Termine
- Multi-Select für mehrere Kurse
- Trainer-Details mit Bewertungen
- Standort-Information
- Kalender-Export

#### pages/calendar.py
**Zweck**: Wochenansicht aller Termine

**Features**:
- Vollständiger Wochenkalender
- Multi-Kurs-Auswahl
- Filter-Integration
- iCal Feed Generation
- Navigation zwischen Wochen

## 👨‍💻 Entwickler-Guide

### Code-Style

**Python Naming Conventions**:
```python
# Funktionen: snake_case
def get_user_data():
    pass

# Variablen: snake_case
user_name = "John"

# Konstanten: UPPER_CASE
MAX_LOGIN_ATTEMPTS = 5

# Klassen: PascalCase
class UserManager:
    pass
```

**Streamlit Best Practices**:

1. **Session State für Persistenz**:
```python
# Initialisiere im Session State
if 'counter' not in st.session_state:
    st.session_state['counter'] = 0

# Ändere Werte
st.session_state['counter'] += 1
```

2. **Caching für Performance**:
```python
@st.cache_data(ttl=300)  # Cache für 5 Minuten
def expensive_operation():
    # Wird nur einmal alle 5 Minuten ausgeführt
    pass
```

3. **Navigation mit switch_page**:
```python
if st.button("Go to Details"):
    st.switch_page("pages/details.py")
```

### Neue Features hinzufügen

**1. Neue Seite erstellen**:

Erstelle `pages/new_page.py`:
```python
import streamlit as st
from data.auth import is_logged_in

if not is_logged_in():
    st.error("❌ Bitte melden Sie sich an.")
    st.stop()

st.title("Meine Neue Seite")
st.write("Willkommen!")
```

Füge zur Navigation in `streamlit_app.py` hinzu:
```python
new_page = st.Page("pages/new_page.py", title="Neue Seite", icon="🔷")
pages.append(new_page)
```

**2. Neue Filter hinzufügen**:

1. Füge Filter-UI zu `data/shared_sidebar.py` hinzu
2. Erweitere Filter-Logik in `data/filters.py`
3. Erweitere `state_manager.py` für neue State-Variablen
4. Teste auf allen Seiten

**3. Neue Datenbank-Query**:

Füge Funktion zu `data/supabase_client.py` hinzu:
```python
@st.cache_data(ttl=600)
def get_my_new_data():
    conn = supaconn()
    result = conn.table("my_table").select("*").execute()
    return result.data
```

### Testing

**Manuelle Tests**:

1. **Authentifizierung**:
   - Login mit Google
   - Logout
   - Session Timeout

2. **Filter**:
   - Alle Filter durchtesten
   - Kombinationen ausprobieren
   - Edge Cases (leere Ergebnisse)

3. **Navigation**:
   - Alle Seiten öffnen
   - Zurück-Buttons
   - Query-Parameter

**Debugging**:

Streamlit bietet eingebaute Debug-Tools:

```python
# Debug-Modus aktivieren
import logging
logging.basicConfig(level=logging.DEBUG)

# Session State anzeigen
st.write(st.session_state)

# Exceptions loggen
try:
    result = risky_operation()
except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
```

### Performance-Optimierung

**Häufige Bottlenecks**:

1. **Zu viele API-Calls**:
   - ✅ Verwende `@st.cache_data`
   - ✅ Nutze batch-Queries
   - ❌ Vermeide Queries in Loops

2. **Große Datenmengen**:
   - ✅ Nutze Pagination
   - ✅ Filtere früh
   - ✅ Zeige nur sichtbare Daten

3. **Schwere Berechnungen**:
   - ✅ Nutze `@st.cache_data`
   - ✅ Berechne offline
   - ✅ Nutze Generators für große Listen

## 🚢 Deployment

### Lokale Entwicklung

**Optimale Entwicklungsumgebung**:

```bash
# Terminal 1: Streamlit App
cd /path/to/unisport
source venv/bin/activate  # Mac/Linux
streamlit run streamlit_app.py

# Terminal 2: Supabase CLI (optional für lokales Testing)
supabase start
```

**Hot Reload**: 
- Streamlit lädt automatisch neu bei Code-Änderungen
- Nicht für `.toml` Dateien - restart erforderlich

### Streamlit Cloud Deployment

**Vorteile von Streamlit Cloud**:
- Kostenlos für öffentliche Repos
- Automatische Deployments via Git
- HTTPS out-of-the-box
- Shared State Management

**Deployment-Schritte**:

1. **Repository zu GitHub pushen**:
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Streamlit Cloud Setup**:
   - Gehe zu [share.streamlit.io](https://share.streamlit.io)
   - Logge dich mit GitHub ein
   - Klicke "New app"
   - Wähle Repository: `username/unisport`
   - Branch: `main`
   - Main file: `streamlit_app.py`
   - Klicke "Deploy!"

3. **Secrets konfigurieren**:
   - In Streamlit Cloud: Settings → Secrets
   - Kopiere Inhalt von `.streamlit/secrets.toml`
   - Füge in Secrets-Editor ein
   - Klicke "Save"

4. **Redirect URIs aktualisieren**:
   - Gehe zu Google Cloud Console
   - Bearbeite OAuth Credentials
   - Füge hinzu: `https://unisportai.streamlit.app/oauth2callback`
   - Speichern

**Umgebungsvariablen verwalten**:

In `.streamlit/secrets.toml`:
```toml
# Lokal
[connections.supabase]
url = "https://xxxxx.supabase.co"
key = "local-key"

# Production (auf Streamlit Cloud)
# Automatisch von Cloud Secrets geholt
```

**Deployment-Tipps**:

- ✅ **Kleine Commits**: Ein Feature pro Commit
- ✅ **Commit Messages**: Beschreibend und klar
- ✅ **Testing**: Lokal testen vor Push
- ❌ **Sensitive Daten**: Niemals Secrets committen
- ❌ **Große Dateien**: Nutze Git LFS oder externe Storage

### Alternativen zu Streamlit Cloud

**Heroku**:
- Eigene Container-Option
- Kostenpflichtig ab 2022
- Mehr Konfiguration nötig

**Docker + Cloud Provider**:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 🐛 Troubleshooting

### Authentifizierungsfehler

**Problem**: "Redirect URI mismatch"

**Lösung**: 
```bash
# Prüfe .streamlit/secrets.toml
# Füge korrekte Redirect URIs in Google Console hinzu:
# Lokal: http://localhost:8501/oauth2callback
# Cloud: https://unisportai.streamlit.app/oauth2callback
```

**Problem**: "Invalid credentials"

**Lösung**:
- Prüfe Client ID und Secret in secrets.toml
- Stelle sicher dass keine Leerzeichen/Absätze vorhanden
- Regenerate Credentials in Google Console falls nötig

### Supabase Connection Issues

**Problem**: "Connection refused"

**Lösung**:
```python
# Überprüfe URL in secrets.toml
# Format: https://xxxxx.supabase.co (kein trailing slash!)
```

**Problem**: "Invalid API Key"

**Lösung**:
- Hole neuen API Key von Supabase Dashboard
- Stelle sicher dass `anon/public` key verwendet wird
- Nicht `service_role` key für Client-Seite!

**Problem**: "Row Level Security Policy Error"

**Lösung**:
- Check RLS Policies in Supabase Dashboard
- Die App nutzt User-spezifische Queries
- Policies müssen für `authenticated` user aktiv sein

### Port-Konflikte

**Problem**: "Port 8501 already in use"

**Lösung**:
```bash
# Option 1: Verwende anderen Port
streamlit run streamlit_app.py --server.port 8502

# Option 2: Beende anderen Prozess
# Windows:
netstat -ano | findstr :8501
taskkill /PID <PID-NUMBER> /F

# Mac/Linux:
lsof -ti:8501 | xargs kill
```

### Cache-Probleme

**Problem**: Änderungen nicht sichtbar

**Lösung**:
```bash
# Cache löschen
streamlit cache clear

# Reload (C auf Tastatur)
# Oder: Hamburgermenü → Settings → Clear cache
```

**Problem**: Alte Daten angezeigt

**Lösung**:
- Überprüfe TTL-Werte in `@st.cache_data` Decorators
- Reduziere TTL für Entwicklungszeit
- Nutze `clear_on_rerun=True` für Tests

### Performance-Issues

**Problem**: Langsame Seiten

**Ursachen prüfen**:
```python
import time

start = time.time()
# Deine Operation
duration = time.time() - start
st.write(f"Operation took: {duration:.2f}s")
```

**Häufige Ursachen**:
- Zu viele API-Calls ohne Caching
- Unoptimierte Queries
- Große Datenmengen ohne Pagination

**Lösungen**:
- Nutze `@st.cache_data` wo möglich
- Implementiere Lazy Loading
- Zeige Ladebalken: `st.progress()` oder `st.spinner()`

### Weitere häufige Probleme

**Streamlit zeigt "Please wait..." ewig**:
- Browser Cache löschen
- Adblocker deaktivieren
- Anderen Browser testen

**Module nicht gefunden**:
```bash
# Stelle sicher dass virtuelle Umgebung aktiviert ist
# Check Python Path
which python
# Sollte auf venv verweisen

# Reinstall packages
pip install -r requirements.txt
```

**Google Login funktioniert nicht lokal aber in Cloud**:
- Lokaler Redirect URI prüfen
- Https vs. Http Unterschied
- Cookie-Einstellungen im Browser

## 🤝 Contributing

Wir freuen uns über Beiträge! Hier ist wie du helfen kannst:

### Voraussetzungen

- Python 3.9+
- Git
- Supabase Account
- Google Cloud Console Account

### Beitragsprozess

1. **Fork das Repository**
   ```bash
   git fork https://github.com/deinusername/unisport.git
   ```

2. **Erstelle Feature Branch**
   ```bash
   git checkout -b feature/mein-feature
   ```

3. **Mache Änderungen und teste**
   - Teste lokal
   - Füge Kommentare hinzu
   - Update README falls nötig

4. **Commit und Push**
   ```bash
   git add .
   git commit -m "Add: Beschreibung des Features"
   git push origin feature/mein-feature
   ```

5. **Erstelle Pull Request**
   - Beschreibe deine Änderungen
   - Nenne Motivation und Use Cases
   - Warte auf Review

### Code Standards

- **PEP 8**: Python Style Guide befolgen
- **Documentation**: Docstrings für alle Funktionen
- **Type Hints**: Wo sinnvoll verwenden
- **Tests**: Unit Tests für neue Funktionen
- **Backward Compatibility**: Breaking Changes dokumentieren

### Bug Reports

Bei Bug Reports bitte folgende Information angeben:
- Streamlit Version
- Python Version  
- Betriebssystem
- Error Message (vollständig)
- Steps to Reproduce
- Screenshots wenn relevant

## 📞 Kontakt & Support

### Projektbetreuer

- **GitHub**: [@deinusername](https://github.com/deinusername)
- **Email**: deine-email@example.com

### Community

- **Issues**: [GitHub Issues](https://github.com/deinusername/unisport/issues)
- **Discussions**: [GitHub Discussions](https://github.com/deinusername/unisport/discussions)

### Weitere Ressourcen

- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)
- **Supabase Docs**: [supabase.com/docs](https://supabase.com/docs)
- **Google OAuth Guide**: [developers.google.com](https://developers.google.com/identity/protocols/oauth2)

### Lizenz

Dieses Projekt ist lizenziert unter der MIT License - siehe LICENSE file für Details.

---

**Made with ❤️ for Universität St.Gallen**

*Letzte Aktualisierung: 2025-01*
