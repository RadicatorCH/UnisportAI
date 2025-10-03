import os
import runpy
import sys


# Kompatibilitäts-Starter für Streamlit Cloud:
# Lädt die eigentliche App aus .streamlit/streamlit_app.py,
# damit der erwartete Hauptpfad im Repo-Root wieder vorhanden ist.

BASE_DIR = os.path.dirname(__file__)
TARGET = os.path.join(BASE_DIR, ".streamlit", "streamlit_app.py")

if not os.path.exists(TARGET):
    raise SystemExit(f"Main module not found at {TARGET}")

# Ausführen, als wäre es das Hauptmodul
runpy.run_path(TARGET, run_name="__main__")


