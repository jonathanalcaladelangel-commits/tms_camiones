# app.py
import streamlit as st
from Dao.usuario_dao import UsuarioDAO  
# Configuración de página limpia y centrada (se adapta a pantallas móviles)
st.set_page_config(page_title="TMS Camiones", page_icon="🚛", layout="centered")

# Inicializar las variables de estado de sesión si no existen
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.rol = None
    st.session_state.usuario = ""

# --- FORMULARIO DE LOGIN ---
if not st.session_state.autenticado:
    st.title("🚛 TMS Control")
    st.subheader("Iniciar Sesión")
    
    usuario_input = st.text_input("Usuario")
    contrasena_input = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar", use_container_width=True):
        # Llamamos al DAO para validar contra Supabase
        rol_detectado = UsuarioDAO.validar_usuario(usuario_input, contrasena_input)
        
        if rol_detectado:
            st.session_state.autenticado = True
            st.session_state.rol = rol_detectado
            st.session_state.usuario = usuario_input
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

# --- PANEL PRINCIPAL (USUARIO LOGUEADO) ---
else:
    # Encabezado móvil con datos del usuario y botón de salida
    col_user, col_logout = st.columns([2, 1])
    col_user.write(f"👤 **{st.session_state.usuario}** ({st.session_state.rol.upper()})")
    if col_logout.button("Salir", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.rol = None
        st.session_state.usuario = ""
        st.rerun()
        
    st.divider()

    # VISTA 1: PANEL DEL DUEÑO (ADMINISTRADOR)
    if st.session_state.rol == "admin":
        st.title("Panel de Administración")
        
        # Pestañas de navegación superiores ideales para el celular
        tab1, tab2, tab3 = st.tabs(["📊 Viajes", "➕ Despacho", "⚙️ Flota"])
        
        with tab1:
            st.subheader("Monitoreo de Unidades")
            st.info("Visualización del estatus actual de los fletes en tránsito.")
            
        with tab2:
            st.subheader("Registrar Nuevo Viaje")
            st.text_input("Origen del flete")
            st.text_input("Destino del flete")
            if st.button("Crear Viaje", type="primary", use_container_width=True):
                st.success("Viaje registrado en el sistema correctamente.")
                
        with tab3:
            st.subheader("Control de Flota")
            st.write("Catálogo rápido de camiones y operadores.")

    # VISTA 2: PORTAL PARA EL CLIENTE
    elif st.session_state.rol == "cliente":
        st.title("Portal de Clientes")
        st.subheader("📍 Rastreo de Cargas")
        st.write("Bienvenido. Aquí puedes consultar el estado logístico de tus fletes contratados:")
        
        # Tarjeta visual simulada de viaje
        st.success("📦 **Viaje #1024** | Origen: Monterrey ➡️ Destino: Reynosa | **Estatus: En Ruta**")