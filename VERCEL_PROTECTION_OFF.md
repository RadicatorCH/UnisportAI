# Vercel Protection Deaktivieren

## 🚪 Deployment Protection Deaktivieren

### Option 1: Vercel Dashboard (Einfach)

1. **Gehe zu https://vercel.com**
2. **Wähle dein Projekt**: `unisport-ai` oder `unisport`
3. **Klicke auf "Settings"** (Zahnrad-Symbol)
4. **Gehe zu "Protection"** im Menü
5. **Unter "Deployment Protection"**
   - Finde **"Production Protection"** 
   - Toggle auf **"Off"** stellen
6. **Speichern**

### Option 2: Vercel CLI (Wenn installiert)

```bash
# Login
vercel login

# Remove protection
vercel env rm PREVIEW_PROTECTION_SECRET --yes
vercel env rm DEPLOYMENT_PROTECTION_SECRET --yes

# Redeploy
vercel --prod
```

## 📝 Nach dem Deaktivieren

1. **Teste die URL**:
   ```bash
   curl https://unisport-f2hi9yvwz-radicatorchs-projects.vercel.app/
   ```

2. **Sollte jetzt funktionieren** ohne Passwort!

3. **Environment Variables setzen** (falls noch nicht geschehen):
   - Gehe zu Settings → Environment Variables
   - Füge hinzu:
     - `SUPABASE_URL` = https://mcbbjvjezbgekbmcajii.supabase.co
     - `SUPABASE_SERVICE_ROLE_KEY` = dein-key

4. **Update data/user_management.py**:
   ```python
   ical_feed_url = f"https://unisport-f2hi9yvwz-radicatorchs-projects.vercel.app/ical-feed?token={ical_token}"
   ```

5. **Commit & Push**:
   ```bash
   git add data/user_management.py
   git commit -m "feat: Switch to Vercel iCal feed"
   git push origin main
   ```

## ✅ Dann verwendet die App:

- **Vercel FastAPI** für den Live-Feed
- **Automatische Updates** via iCal Subscription
- **Keine Passwort-Barriere** mehr

