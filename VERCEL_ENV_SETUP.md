# 🔧 Vercel Environment Variables Setup

## Schritt-für-Schritt Anleitung

### 1️⃣ Öffne Vercel Dashboard
1. Gehe zu **https://vercel.com**
2. Login mit deinem Account

### 2️⃣ Wähle dein Projekt
1. Klicke auf **"unisport-ai"** oder das richtige Projekt
2. Falls du das Projekt nicht siehst:
   - Klicke **"Add New Project"**
   - Verbinde mit deinem GitHub Repo
   - Wähle das **Unisport** Repository

### 3️⃣ Gehe zu Settings → Environment Variables
1. In der Projekt-Ansicht: Klicke auf **"Settings"** (Zahnrad-Symbol)
2. Im linken Menü: Klicke auf **"Environment Variables"**

### 4️⃣ Füge die Variablen hinzu

#### Variable 1: SUPABASE_URL
1. Klicke **"Add New"**
2. **Name**: `SUPABASE_URL`
3. **Value**: `https://mcbbjvjezbgekbmcajii.supabase.co`
4. **Environment**: Wähle alle (Production, Preview, Development)
5. Klicke **"Save"**

#### Variable 2: SUPABASE_SERVICE_ROLE_KEY
1. Klicke **"Add New"**
2. **Name**: `SUPABASE_SERVICE_ROLE_KEY`
3. **Value**: Dein Service Role Key (aus Streamlit Secrets)
4. **Environment**: Wähle alle (Production, Preview, Development)
5. Klicke **"Save"**

### 5️⃣ Redeploy
1. Gehe zurück zur **"Deployments"** Tab
2. Finde den letzten fehlgeschlagenen Deployment
3. Klicke auf die **drei Punkte** → **"Redeploy"**
4. Warte bis der Build fertig ist

### 6️⃣ Teste die API
```bash
curl https://unisport-f2hi9yvwz-radicatorchs-projects.vercel.app/
```

## ✅ Erwartetes Ergebnis
- API antwortet mit JSON: `{"message": "Unisport iCal Feed API", "version": "1.0.0"}`
- Kein "Deployment failed" mehr!

## 🔄 Dann in der App aktualisieren

In `data/user_management.py` - aktiviere Vercel:
```python
ical_feed_url = f"https://unisport-f2hi9yvwz-radicatorchs-projects.vercel.app/ical-feed?token={ical_token}&x-vercel-protection-bypass={vercel_bypass}"
```

## 🚨 Wichtige Notes
- **Niemals** die SUPABASE_SERVICE_ROLE_KEY committen!
- Die Variablen sind **verschlüsselt** in Vercel gespeichert
- Änderungen werden **sofort** nach Redeploy aktiv

