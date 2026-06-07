# Dao/usuario_dao.py
from database.conexion import obtener_cliente

class UsuarioDAO:
    @staticmethod
    def validar_usuario(username, password_ingresada):
        """
        Verifica si el usuario existe en Supabase y coincide la contraseña.
        Retorna el rol ('admin' o 'cliente') si es correcto, o None si falla.
        """
        try:
            supabase = obtener_cliente()
            
            # Consultamos la tabla 'usuarios' filtrando por el username
            respuesta = supabase.table("usuarios").select("*").eq("username", username).execute()
            
            # Si encontró al menos un registro
            if respuesta.data:
                usuario = respuesta.data[0]
                # Validación básica de texto plano para el MVP
                if usuario['password_hash'] == password_ingresada:
                    return usuario['rol']
        except Exception as e:
            # En caso de un error de red o conexión, lo captura aquí
            print(f"Error de conexión en UsuarioDAO: {e}")
            
        return None