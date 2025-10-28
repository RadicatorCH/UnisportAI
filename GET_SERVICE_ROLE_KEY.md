# 🔑 Service Role Key finden

## Wo ist der Service Role Key?

### Option 1: Supabase Dashboard
1. Gehe zu **supabase.com**
2. Wähle dein Projekt: `mcbbjvjezbgekbmcajii`
3. **Settings** (Zahnrad) → **API**
4. Finde **"service_role" key** (Secret!)
5. **Kopiere** diesen Key

### Option 2: Aus .env oder bestehender Config
Der Service Role Key sollte so aussehen:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1jYmJqdmplemJnZWtibWNhamlpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTQ4MTczMSwiZXhwIjoyMDc1MDU3NzMxfQ.xxxxx
```

**WICHTIG**: Der Service Role Key ist **Geheim** und hat Admin-Zugriff!

## 📋 Vercel Environment Variables

### Zu setzen in Vercel:
1. `SUPABASE_URL` = `https://mcbbjvjezbgekbmcajii.supabase.co`
2. `SUPABASE_SERVICE_ROLE_KEY` = `<Service Role Key aus Supabase Dashboard>`

### Beide für alle Environments:
- ✅ Production
- ✅ Preview  
- ✅ Development

## ⚡ Quick Setup

```bash
# Falls du Vercel CLI hast:
vercel env add SUPABASE_URL
# Value: https://mcbbjvjezbgekbmcajii.supabase.co

vercel env add SUPABASE_SERVICE_ROLE_KEY  
# Value: <dein-service-role-key>
```

