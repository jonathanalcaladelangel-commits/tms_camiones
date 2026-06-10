# app.py
import streamlit as st
import pandas as pd
from Dao.usuario_dao import UsuarioDAO
from database.conexion import obtener_cliente

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

    # =========================================================
    # VISTA PARA EL DUEÑO / ADMINISTRADOR
    # =========================================================
    if st.session_state.rol == "admin":
        st.title("Panel de Administración")
        
        # Creamos las 3 pestañas principales de tu negocio
        tab1, tab2, tab3 = st.tabs(["📊 Viajes", "➕ Despacho", "⚙️ Flota"])

        # PESTAÑA 1: VISUALIZACIÓN DE VIAJES EN TIEMPO REAL
        with tab1:
            st.subheader("📊 Monitoreo de Unidades")
            st.write("Estatus actual de los fletes registrados en el sistema.")
            
            try:
                supabase = obtener_cliente()
                respuesta = supabase.table("viajes").select("*").order("id", desc=True).execute()
                
                if respuesta.data and len(respuesta.data) > 0:
                    df_viajes = pd.DataFrame(respuesta.data)
                    
                    df_viajes = df_viajes.rename(columns={
                        "cliente": "🏢 Cliente",
                        "origen": "📍 Origen",
                        "destino": "🏁 Destino",
                        "operador_manual": "👤 Chofer",
                        "unidad_manual": "🚛 Unidad",
                        "tarifa": "💰 Tarifa ($)",
                        "estatus": "🟢 Estatus"
                    })
                    
                    columnas_visibles = ["🏢 Cliente", "📍 Origen", "🏁 Destino", "👤 Chofer", "🚛 Unidad", "💰 Tarifa ($)", "🟢 Estatus"]
                    st.dataframe(df_viajes[columnas_visibles], use_container_width=True, hide_index=True)
                else:
                    st.info("📭 No hay viajes registrados en este momento.")
            except Exception as e:
                st.error(f"❌ Error al cargar el monitoreo desde Supabase: {e}")

        # PESTAÑA 2: REGISTRO DE NUEVOS VIAJES (CORREGIDO SIN DOBLE ENVÍO)
        with tab2:
            st.subheader("➕ Registrar Nuevo Viaje")
            st.write("Ingresa los datos del flete para asignarlo al operador.")
            
            col_flete1, col_flete2 = st.columns(2)
            
            with col_flete1:
                cliente = st.text_input("🏢 Nombre del Cliente", key="input_cliente")
                origen = st.text_input("📍 Ciudad de Origen", key="input_origen")
                operador_manual = st.text_input("👤 Nombre del Chofer / Operador", key="input_operador")
                
            with col_flete2:
                tarifa = st.number_input("💰 Tarifa del Flete ($)", min_value=0.0, step=500.0, key="input_tarifa")
                destino = st.text_input("🏁 Ciudad de Destino", key="input_destino")
                unidad_manual = st.text_input("🚛 Camión / Placas de la Unidad", key="input_unidad")
            
            # Botón directo sin st.form para evitar ejec
