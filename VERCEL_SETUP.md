# Vercel Setup Instructions

## 🔐 Secrets hinzufügen

Füge zu `.streamlit/secrets.toml` hinzu:

```toml
[vercel]
bypass_secret = "streamli29uz34o7821z34087g342g2t"
```

## 📝 Dann

Die App wird automatisch die Vercel URL mit Bypass nutzen!

## 🔄 Falls Vercel nicht funktioniert

Die App nutzt automatisch Supabase Edge Function als Fallback.
