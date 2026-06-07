# database/conexion.py
from supabase import create_client, Client

# Tu URL única de proyecto basada en tu ID de Supabase
SUPABASE_URL = "https://uctwcciuvgonajsvfhkc.supabase.co"

# ⚠️ PEGA AQUÍ TU LLAVE ANON COMPLETA (La que copiaste de la captura)
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVjdHdjY2l1dmdvbmFqc3ZmaGtjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA3NzgwNDcsImV4cCI6MjA5NjM1NDA0N30.400nmXLmve88nf_P0BiR9aTrtoREMWjgftgzi4sfFR8" 

def obtener_cliente() -> Client:
    """Retorna la instancia del cliente para interactuar con Supabase"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)