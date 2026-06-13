# app.py
import streamlit as st
import pandas as pd
from Dao.usuario_dao import UsuarioDAO
from database.conexion import obtener_cliente

# Configuración de página limpia y centrada
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
        
        tab1, tab2, tab3 = st.tabs(["📊 Viajes", "➕ Despacho", "⚙️ Flota"])

        # PESTAÑA 1: VISUALIZACIÓN DE VIAJES EN TIEMPO REAL
        with tab1:
            st.subheader("📊 Monitoreo de Unidades")
            st.write("Estatus actual de los fletes registrados en el sistema.")
            
            try:
                supabase = obtener_cliente()
                # CORREGIDO: Tu columna de ordenamiento real es 'id'
                respuesta = supabase.table("viajes").select("*").order("id", desc=True).execute()
                
                if respuesta.data and len(respuesta.data) > 0:
                    df_viajes = pd.DataFrame(respuesta.data)
                    
                    # Identificamos dinámicamente si la columna es 'id_cliente' o 'cliente'
                    col_cliente_db = "id_cliente" if "id_cliente" in df_viajes.columns else "cliente"
                    
                    columnas_mapeo = {
                        col_cliente_db: "🏢 Cliente",
                        "origen": "📍 Origen",
                        "destino": "🏁 Destino",
                        "operador_manual": "👤 Chofer",
                        "unidad_manual": "🚛 Unidad",
                        "tarifa": "💰 Tarifa ($)",
                        "estatus": "🟢 Estatus"
                    }
                    
                    df_viajes = df_viajes.rename(columns=columnas_mapeo)
                    columnas_visibles = ["🏢 Cliente", "📍 Origen", "🏁 Destino", "👤 Chofer", "🚛 Unidad", "💰 Tarifa ($)", "🟢 Estatus"]
                    
                    # Filtrar solo las que existan para no romper la app
                    cols_finales = [c for c in columnas_visibles if c in df_viajes.columns]
                    st.dataframe(df_viajes[cols_finales], use_container_width=True, hide_index=True)
                else:
                    st.info("📭 No hay viajes registrados en este momento.")
            except Exception as e:
                st.error(f"❌ Error al cargar el monitoreo desde Supabase: {e}")

        # PESTAÑA 2: REGISTRO DE NUEVOS VIAJES
        with tab2:
            st.subheader("➕ Registrar Nuevo Viaje")
            st.write("Ingresa los datos del flete para asignarlo al operador.")
            
            try:
                supabase = obtener_cliente()
                # Traemos las columnas reales de la tabla viajes en caliente para saber cómo se llama la columna de cliente
                test_cols = supabase.table("viajes").select("*").limit(1).execute()
                lista_columnas = test_cols.data[0].keys() if test_cols.data else []
                col_destino_cliente = "id_cliente" if "id_cliente" in lista_columnas else "cliente"
            except:
                col_destino_cliente = "id_cliente"

            with st.form("formulario_despacho", clear_on_submit=True):
                col_flete1, col_flete2 = st.columns(2)
                
                with col_flete1:
                    cliente = st.text_input("🏢 Nombre del Cliente")
                    origen = st.text_input("📍 Ciudad de Origen")
                    operador_manual = st.text_input("👤 Nombre del Chofer / Operador")
                    
                with col_flete2:
                    tarifa = st.number_input("💰 Tarifa del Flete ($)", min_value=0.0, step=500.0)
                    destino = st.text_input("🏁 Ciudad de Destino")
                    unidad_manual = st.text_input("🚛 Camión / Placas de la Unidad")
                
                boton_despachar = st.form_submit_button("🚀 Registrar y Despachar Viaje", use_container_width=True)
                
                if boton_despachar:
                    if not cliente or not origen or not destino or not operador_manual:
                        st.error("⚠️ Por favor, llena los campos esenciales (Cliente, Origen, Destino y Chofer).")
                    else:
                        try:
                            datos_viaje = {
                                col_destino_cliente: cliente.strip(),
                                "origen": origen.strip(),
                                "destino": destino.strip(),
                                "operador_manual": operador_manual.strip(),
                                "unidad_manual": unidad_manual.strip(),
                                "tarifa": tarifa,
                                "estatus": "En Tránsito"
                            }
                            
                            supabase.table("viajes").insert(datos_viaje).execute()
                            st.session_state["mensaje_exito"] = f"✅ ¡Viaje registrado con éxito! Operador **{operador_manual}** va en tránsito hacia **{destino}**."
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error al guardar el viaje en Supabase: {e}")
            
            if "mensaje_exito" in st.session_state:
                st.success(st.session_state["mensaje_exito"])
                st.balloons()
                del st.session_state["mensaje_exito"]

        # PESTAÑA 3: CONFIGURACIÓN DE FLOTA
        with tab3:
            st.subheader("⚙️ Control de Flota")
            st.write("Apartado para gestionar camiones y operadores reales (Próximamente).")

    # =========================================================
    # VISTA PARA EL CLIENTE (OPCIÓN 4 COMPLETADA)
    # =========================================================
    elif st.session_state.rol == "cliente":
        st.title("Portal de Clientes")
        st.subheader("📦 Estado de mis Embarques")
        st.write(f"Bienvenido. Consultando las cargas asignadas a: **{st.session_state.usuario}**")
        
        try:
            supabase = obtener_cliente()
            test_cols = supabase.table("viajes").select("*").limit(1).execute()
            lista_columnas = test_cols.data[0].keys() if test_cols.data else []
            col_destino_cliente = "id_cliente" if "id_cliente" in lista_columnas else "cliente"

            respuesta = supabase.table("viajes").select("*").eq(col_destino_cliente, st.session_state.usuario).order("id", desc=True).execute()
            
            if respuesta.data and len(respuesta.data) > 0:
                df_cliente = pd.DataFrame(respuesta.data)
                df_cliente = df_cliente.rename(columns={"origen": "📍 Origen", "destino": "🏁 Destino", "unidad_manual": "🚛 Unidad asignada", "estatus": "🟢 Estatus de Entrega"})
                columnas_cliente = ["📍 Origen", "🏁 Destino", "🚛 Unidad asignada", "🟢 Estatus de Entrega"]
                st.dataframe(df_cliente[columnas_cliente], use_container_width=True, hide_index=True)
            else:
                st.info("📭 Actualmente no tienes ningún embarque en tránsito con nosotros.")
        except Exception as e:
            st.error(f"❌ Error al consultar tus datos: {e}")
