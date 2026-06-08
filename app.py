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
            
       # Buscaremos la sección de las pestañas en tu app.py y nos paramos en Despacho:
    with tab2: # Asegúrate de que corresponda a tu pestaña de Despacho
        st.subheader("➕ Registrar Nuevo Viaje")
        st.write("Ingresa los datos del flete para asignarlo al operador correspondiente.")
        
        # Conexión directa a Supabase para guardar los datos
        from database.conexion import obtener_cliente
        
        # Creamos el formulario de captura
        with st.form("form_nuevo_viaje", clear_on_submit=True):
            col_flete1, col_flete2 = st.columns(2)
            
            with col_flete1:
                cliente = st.text_input("🏢 Nombre del Cliente")
                origen = st.text_input("📍 Ciudad de Origen")
                operador_manual = st.text_input("👤 Nombre del Chofer / Operador")
                
            with col_flete2:
                tarifa = st.number_input("💰 Tarifa del Flete ($)", min_value=0.0, step=500.0)
                destino = st.text_input("🏁 Ciudad de Destino")
                unidad_manual = st.text_input("🚛 Camión / Placas de la Unidad")
            
            # Botón de envío dentro del formulario
            boton_despachar = st.form_submit_code = st.form_submit_button("🚀 Registrar y Despachar Viaje", use_container_width=True)
            
            if boton_despachar:
                # Validamos que los campos obligatorios no estén vacíos
                if not cliente or not origen or not destino or not operador_manual:
                    st.error("⚠️ Por favor, llena los campos esenciales (Cliente, Origen, Destino y Chofer).")
                else:
                    try:
                        supabase = obtener_cliente()
                        
                        # Armamos el diccionario con los nombres de tus columnas en Supabase
                        datos_viaje = {
                            "cliente": cliente.strip(),
                            "origen": origen.strip(),
                            "destino": destino.strip(),
                            "operador_manual": operador_manual.strip(),
                            "unidad_manual": unidad_manual.strip(),
                            "tarifa": tarifa,
                            "estatus": "En Tránsito" # Se registra activo por defecto
                        }
                        
                        # Insertamos directo en la tabla 'viajes'
                        supabase.table("viajes").insert(datos_viaje).execute()
                        st.success(f"✅ ¡Viaje registrado con éxito! Operador **{operador_manual}** va en tránsito hacia **{destino}**.")
                        
                    except Exception as e:
                        st.error(f"❌ Error al guardar el viaje en Supabase: {e}")
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
