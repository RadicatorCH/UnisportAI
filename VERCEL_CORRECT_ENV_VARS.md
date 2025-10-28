# ✅ Richtige Environment Variables für Vercel

## Was du gesetzt hast:
❌ `SUPABASE` = Client Key (anon key)

## Was die FastAPI BRAUCHT:

### Variable 1:
```
Name:  SUPABASE_URL
Value: https://mcbbjvjezbgekbmcajii.supabase.co
```

### Variable 2:
```
Name:  SUPABASE_SERVICE_ROLE_KEY
Value: <der SERVICE_ROLE Key aus Supabase Dashboard>
```

## 🔑 Service Role Key finden:
1. Supabase Dashboard → Dein Projekt
2. Settings → API
3. Kopiere der **service_role** key (Secret!)
4. NICHT der **anon** key!

## ⚠️ Wichtig:
Der Service Role Key hat **Admin-Zugriff** auf die Datenbank!
Deshalb braucht die FastAPI ihn - sie muss direkt auf die Datenbank zugreifen.

## 📋 Quick Fix in Vercel:
1. Gehe zu Environment Variables
2. Ändere `SUPABASE` zu `SUPABASE_SERVICE_ROLE_KEY`
3. Füge `SUPABASE_URL` hinzu
4. Redeploy

