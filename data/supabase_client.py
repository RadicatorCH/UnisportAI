from st_supabase_connection import SupabaseConnection

def supaconn():
    conn = st.connection("supabase",type=SupabaseConnection)
    return conn()

def kurse():
    conn = supaconn()
    rows = conn.query("*", table="kurse", ttl="10m").execute()
    return rows