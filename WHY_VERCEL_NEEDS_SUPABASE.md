# Warum die FastAPI Supabase braucht

## 🎯 Architektur-Erklärung

### Was die FastAPI macht:

Die `api/main.py` (FastAPI auf Vercel) ist ein **Python Wrapper** um deine Supabase Datenbank:

```python
# Zeilen 36-48 in api/main.py
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Hole User aus Supabase
user_result = supabase.table('users')
    .select('id, email, name, ical_feed_token')
    .eq('ical_feed_token', token)
    .single()
    .execute()

# 2. Hole Events aus Supabase
notifications = supabase.table('friend_course_notifications')
    .select('event_id, created_at')
    .eq('user_id', user_id)
    .execute()

# 3. Join mit anderen Supabase Tables
result = supabase.table('kurs_termine')
result = supabase.table('unisport_locations')
result = supabase.table('sportkurse')
```

## 🤔 Warum dann Vercel?

### Option 1: **KEIN Vercel** (Aktuell ✅)
- Nutze **Supabase Edge Function** (TypeScript)
- Funktioniert perfekt
- Alles in einem Stack

### Option 2: **Mit Vercel** (Optional)
- Python Syntax (statt TypeScript)
- Zugriff auf `icalendar` Library
- Separation of Concerns

## 💡 Du musst Vercel NICHT verwenden!

Die **Supabase Edge Function** macht das Gleiche:

```typescript:supabase/functions/ical-feed/index.ts
// Supabase Edge Function
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

// 1. Hole User
const { data: tokenUserData } = await supabase
  .from('users')
  .select('id, email, name')
  .eq('ical_feed_token', token)
  .single()

// 2. Hole Events
const { data: notifications } = await supabase
  .from('friend_course_notifications')
  .select('event_id, created_at')
  .eq('user_id', userData.id)
```

## ✅ Empfehlung

**Nutze die Supabase Edge Function** - die läuft bereits perfekt!
- ✅ Keine Environment Variables nötig
- ✅ Läuft bereits live
- ✅ Einfacher Setup
- ✅ Gleiche Funktionalität

**Vercel FastAPI ist optional** - nur wenn du Python statt TypeScript willst.

