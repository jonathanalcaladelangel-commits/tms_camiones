# Dao/usuario_dao.py
from database.conexion import obtener_cliente
import streamlit as st

class UsuarioDAO:
    @staticmethod
    def validar_usuario(username, password_ingresada):
        # 1. ACCESO DE EMERGENCIA (Para probar si la interfaz abre)
        # Si pones de usuario 'root' y contraseña 'root', va a entrar directo sin ir a internet
        if username == "root" and password_ingresada == "root":
            return "admin"

        try:
            supabase = obtener_cliente()
            
            # Intentamos buscar en Supabase
            respuesta = supabase.table("usuarios").select("*").eq("username", username).execute()
            
            # Si Supabase responde, mostramos un mensaje temporal en la app para saber qué encontró
            if respuesta.data:
                usuario = respuesta.data[0]
                db_pass = str(usuario.get('password_hash', '')).strip()
                input_pass = str(password_ingresada).strip()
                
                if db_pass == input_pass:
                    return usuario.get('rol', 'admin')
                else:
                    st.warning(f"DEBUG: El usuario existe, pero la clave en DB es '{db_pass}' y pusiste '{input_pass}'")
            else:
                st.warning("DEBUG: Supabase respondió, pero la tabla está vacía o no encontró ese username.")
                
        except Exception as e:
            # Si la conexión a internet falló, nos va a pintar el error exacto en letras rojas
            st.error(f"⚠️ Error de conexión real con Supabase: {e}")
            
        return None
    
    