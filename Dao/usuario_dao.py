# Dao/usuario_dao.py
from database.conexion import obtener_cliente
import streamlit as st

class UsuarioDAO:
    @staticmethod
    def validar_usuario(username, password_ingresada):
        try:
            supabase = obtener_cliente()
            
            # Limpiamos espacios del usuario que ingresó el teclado
            user_limpio = str(username).strip()
            pass_limpia = str(password_ingresada).strip()
            
            # Consultamos en Supabase filtrando por el nombre de usuario
            respuesta = supabase.table("usuarios").select("*").eq("username", user_limpio).execute()
            
            # Si Supabase encontró al usuario
            if respuesta.data and len(respuesta.data) > 0:
                usuario_db = respuesta.data[0]
                
                # Sacamos la contraseña y el rol de la base de datos
                password_db = str(usuario_db.get('password_hash', '')).strip()
                rol_db = usuario_db.get('rol', '').strip()
                
                # Comparación final de seguridad
                if password_db == pass_limpia:
                    return rol_db
                    
        except Exception as e:
            # Si la URL o la Key están mal, o no hay internet, saltará este aviso en rojo
            st.error(f"⚠️ Error de conexión real con Supabase: {e}")
            
        return None
    