# Dao/usuario_dao.py
from database.conexion import obtener_cliente
import streamlit as st

class UsuarioDAO:
    @staticmethod
    def validar_usuario(username, password_ingresada):
        try:
            supabase = obtener_cliente()
            user_limpio = str(username).strip().lower()
            pass_limpia = str(password_ingresada).strip()
            
            # Consultamos los usuarios existentes
            respuesta = supabase.table("usuarios").select("*").execute()
            
            # 🚀 SI LA TABLA ESTÁ VACÍA, INSERTAMOS LOS ACCESOS AUTOMÁTICAMENTE
            if not respuesta.data or len(respuesta.data) == 0:
                st.info("Configurando accesos iniciales en la base de datos conectada...")
                
                # Insertamos el administrador
                supabase.table("usuarios").insert({"username": "admin", "password_hash": "1234", "rol": "admin"}).execute()
                # Insertamos el cliente
                supabase.table("usuarios").insert({"username": "cliente", "password_hash": "1234", "rol": "cliente"}).execute()
                
                # Volvemos a consultar para actualizar los datos en memoria
                respuesta = supabase.table("usuarios").select("*").execute()
            
            # Buscamos las credenciales válidas
            if respuesta.data:
                for usuario in respuesta.data:
                    db_user = str(usuario.get('username', '')).strip().lower()
                    db_pass = str(usuario.get('password_hash', '')).strip()
                    
                    if db_user == user_limpio and db_pass == pass_limpia:
                        return usuario.get('rol', 'admin')
                        
                st.warning("🔎 DEBUG: Usuario encontrado, pero la contraseña no coincide.")
                
        except Exception as e:
            st.error(f"⚠️ Error de conexión real con Supabase: {e}")
            
        return None
