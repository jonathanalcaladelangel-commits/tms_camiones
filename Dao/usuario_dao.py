# Dao/usuario_dao.py
from database.conexion import obtener_cliente
import streamlit as st

class UsuarioDAO:
    @staticmethod
    def validar_usuario(username, password_ingresada):
        try:
            supabase = obtener_cliente()
            user_limpio = str(username).strip()
            pass_limpia = str(password_ingresada).strip()
            
            # Consultamos en Supabase
            respuesta = supabase.table("usuarios").select("*").eq("username", user_limpio).execute()
            
            # 🔎 REVISIÓN DE DIAGNÓSTICO VISIBLE
            if respuesta.data and len(respuesta.data) > 0:
                usuario_db = respuesta.data[0]
                password_db = str(usuario_db.get('password_hash', '')).strip()
                rol_db = usuario_db.get('rol', '').strip()
                
                # Si coincide, entramos normal
                if password_db == pass_limpia:
                    return rol_db
                else:
                    # Nos confiesa qué clave tiene Supabase guardada en realidad
                    st.warning(f"🔎 DEBUG: El usuario '{user_limpio}' SÍ existe en Supabase, pero su clave guardada es '{password_db}' y tú escribiste '{pass_limpia}'")
            else:
                # Nos avisa si la tabla de plano está vacía o el nombre está mal
                st.warning(f"🔎 DEBUG: Supabase respondió con éxito, pero NO encontró ningún usuario con el nombre '{user_limpio}' en la tabla.")
                    
        except Exception as e:
            st.error(f"⚠️ Error de conexión real con Supabase: {e}")
            
        return None
