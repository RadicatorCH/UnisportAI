# 🔑 Values für Vercel Environment Variables

Da ich kein MCP Tool habe um die Variablen direkt in Vercel zu setzen, hier sind die **exakten Werte**:

## 📋 Kopiere diese Werte in Vercel Dashboard:

### 1. SUPABASE_URL
```
https://mcbbjvjezbgekbmcajii.supabase.co
```

### 2. SUPABASE_SERVICE_ROLE_KEY
**⚠️ Du musst diesen aus dem Supabase Dashboard holen:**

1. Gehe zu: https://supabase.com/dashboard/project/mcbbjvjezbgekbmcajii/settings/api
2. Unter **"Project API keys"**
3. Finde **"service_role"** (Secret!)
4. Klicke auf das Augen-Symbol um den Key anzuzeigen
5. Kopiere den kompletten Key

## ⚡ Oder nutze diese Werte aus deinen Streamlit Secrets:

Falls du bereits einen Service Role Key in `.streamlit/secrets.toml` hast, nutze diesen.

## 🚨 Wichtig

Der Service Role Key ist NICHT der `anon` key!
- ❌ `anon` key = öffentlich, eingeschränkte Rechte
- ✅ `service_role` key = SECRET, Admin-Rechte

Der Code liest: `SUPABASE_SERVICE_ROLE_KEY` - also der Service Role Key!

