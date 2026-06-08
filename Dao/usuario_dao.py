# Dao/usuario_dao.py
from database.conexion import obtener_cliente
import streamlit as st

class UsuarioDAO:
    @staticmethod
    def validar_usuario(username, password_ingresada):
        try:
            supabase = obtener_cliente()
            
            # Pasamos todo a minúsculas y limpiamos espacios de lo que escribe el usuario
            user_limpio = str(username).strip().lower()
            pass_limpia = str(password_ingresada).strip()
            
            # Traemos todos los usuarios para buscarlo de forma segura en Python
            respuesta = supabase.table("usuarios").select("*").execute()
            
            if respuesta.data:
                for usuario in respuesta.data:
                    # Comparamos ignorando mayúsculas/minúsculas en el username
                    db_user = str(usuario.get('username', '')).strip().lower()
                    db_pass = str(usuario.get('password_hash', '')).strip()
                    
                    if db_user == user_limpio and db_pass == pass_limpia:
                        return usuario.get('rol', 'admin')
                
                # Si recorrió la tabla y no coincidió la clave
                st.warning(f"🔎 DEBUG: El usuario '{username}' existe, pero la contraseña no coincide.")
            else:
                st.warning("🔎 DEBUG: La tabla 'usuarios' en Supabase está completamente vacía.")
                
        except Exception as e:
            st.error(f"⚠️ Error de conexión real con Supabase: {e}")
            
        return None
