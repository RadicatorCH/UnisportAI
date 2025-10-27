# Supabase Migrations für Unisport Scraper

## Übersicht

Diese Migrationen aktualisieren die `sportkurse` Tabelle, um `bs_code` und `bs_kursid` zu speichern (anstatt `buchung_href`).

## Ausführung

Führe diese SQL-Befehle nacheinander in deinem **Supabase SQL Editor** aus:

### 1. Spalte umbenennen
```bash
.scraper/migrations/001_rename_buchung_href_to_bs_code.sql
```

### 2. Neue Spalte hinzufügen
```bash
.scraper/migrations/002_add_bs_kursid_column.sql
```

## Erklärung

- **bs_code**: Booking Session Code (hidden input aus dem Formular), pro Angebots-Seite fest, nicht pro Nutzer individuell
- **bs_kursid**: Submit Button Name (z.B. "BS_Kursid_23421") für die Buchung

Diese Werte werden vom Scraper extrahiert und für den Buchungsprozess benötigt.

## Nach der Migration

Teste den Scraper:
```bash
python3 .scraper/scrape_sportangebote.py
```

