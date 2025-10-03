import streamlit as st
from typing import Any, Dict, List, Optional

# Wir nutzen die offizielle Streamlit-Connection für Supabase.
# Stelle sicher, dass "st-supabase-connection" in requirements.txt installiert ist.


def get_supabase_conn() -> Any:
    """
    Baut eine Streamlit-Connection zu Supabase auf.

    Erwartete Keys in `.streamlit/secrets.toml` unter [connections.supabase]:
    - Bevorzugt: url, key
    - Alternativ: SUPABASE_URL, SUPABASE_KEY
    Die Connection liest automatisch aus secrets; wir übergeben ggf. Fallbacks.
    """
    secrets = st.secrets.get("connections", {}).get("supabase", {})
    # Mapping unterstützen, falls SUPABASE_URL/KEY genutzt werden
    url = secrets.get("url") or secrets.get("SUPABASE_URL")
    key = secrets.get("key") or secrets.get("SUPABASE_KEY")

    # Wenn url/key fehlen, trotzdem versuchen, da die Connection sie ggf. selbst liest
    if url and key:
        return st.connection("supabase", type="st_supabase_connection.SupabaseConnection", url=url, key=key)
    return st.connection("supabase", type="st_supabase_connection.SupabaseConnection")


def safe_query(conn: Any, table: str, select: str = "*") -> List[Dict[str, Any]]:
    try:
        client = getattr(conn, "client", None)
        if client is None:
            raise RuntimeError("Supabase-Client nicht verfügbar (conn.client ist None)")
        resp = client.table(table).select(select).execute()
        return resp.data or []
    except Exception as e:
        st.warning(f"Fehler beim Laden aus {table}: {e}")
        return []


def main() -> None:
    st.set_page_config(page_title="UnisportAI", layout="wide")
    st.title("UnisportAI – Datenansicht")
    st.caption("Streamlit + Supabase via st.connection")

    with st.sidebar:
        st.header("Verbindung")
        st.write("Credentials werden aus `.streamlit/secrets.toml` geladen.")
        st.code("""
[connections.supabase]
url = "https://PROJECT_REF.supabase.co"
key = "<ANON ODER SERVICE KEY>"
# Alternativ:
SUPABASE_URL = "https://PROJECT_REF.supabase.co"
SUPABASE_KEY = "<ANON ODER SERVICE KEY>"
""".strip())

    conn = get_supabase_conn()

    st.subheader("Tabellen")
    tabs = st.tabs(["sportangebote", "sportkurse", "kurs_termine"])  # legacy: kurs_termine

    with tabs[0]:
        st.write("Alle Sportangebote")
        data = safe_query(conn, "sportangebote", "name, href")
        search = st.text_input("Filter nach Name…", key="f1")
        if search:
            data = [r for r in data if search.lower() in (r.get("name") or "").lower()]
        st.dataframe(data, use_container_width=True)

    with tabs[1]:
        st.write("Alle Kurse")
        data = safe_query(conn, "sportkurse", "kursnr, offer_name, tag, zeit, zeitraum_href, buchung, buchung_href")
        col1, col2 = st.columns(2)
        with col1:
            f_offer = st.text_input("Filter Angebot…", key="f2")
        with col2:
            f_kurs = st.text_input("Filter Kursnr…", key="f3")
        if f_offer:
            data = [r for r in data if f_offer.lower() in (r.get("offer_name") or "").lower()]
        if f_kurs:
            data = [r for r in data if f_kurs.lower() in (r.get("kursnr") or "").lower()]
        st.dataframe(data, use_container_width=True)

    with tabs[2]:
        st.write("Kurs-Termine (legacy: kurs_termine)")
        data = safe_query(conn, "kurs_termine", "kursnr, datum, wochentag, zeit, location_name, canceled")
        col1, col2, col3 = st.columns(3)
        with col1:
            f_kurs = st.text_input("Filter Kursnr…", key="f4")
        with col2:
            f_date = st.text_input("Filter Datum (YYYY-MM-DD)…", key="f5")
        with col3:
            canceled_only = st.checkbox("Nur canceled=true", value=False)
        if f_kurs:
            data = [r for r in data if f_kurs.lower() in (r.get("kursnr") or "").lower()]
        if f_date:
            data = [r for r in data if (r.get("datum") or "").startswith(f_date)]
        if canceled_only:
            data = [r for r in data if bool(r.get("canceled"))]
        st.dataframe(data, use_container_width=True)


if __name__ == "__main__":
    main()


