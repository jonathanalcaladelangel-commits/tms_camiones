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
                respuesta = supabase.table("viajes").select("*").order("id", desc=True).execute()
                
                if respuesta.data and len(respuesta.data) > 0:
                    df_viajes = pd.DataFrame(respuesta.data)
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

            lista_operadores = []
            lista_unidades = []
            try:
                supabase = obtener_cliente()
                res_ops = supabase.table("operadores").select("nombre").order("nombre").execute()
                if res_ops.data:
                    lista_operadores = [row["nombre"] for row in res_ops.data]
                
                res_unis = supabase.table("unidades").select("numero_economico", "modelo").order("numero_economico").execute()
                if res_unis.data:
                    lista_unidades = [f"{row['numero_economico']} - {row['modelo']}" for row in res_unis.data]
            except Exception as e:
                st.warning(f"⚠️ Nota: No se pudieron precargar choferes/unidades automáticamente.")

            with st.form("formulario_despacho", clear_on_submit=True):
                col_flete1, col_flete2 = st.columns(2)
                
                with col_flete1:
                    cliente = st.text_input("🏢 Nombre del Cliente")
                    origen = st.text_input("📍 Ciudad de Origen")
                    
                    if lista_operadores:
                        operador_manual = st.selectbox("👤 Seleccionar Chofer / Operador", lista_operadores)
                    else:
                        operador_manual = st.text_input("👤 Nombre del Chofer / Operador (Manual)")
                    
                with col_flete2:
                    tarifa = st.number_input("💰 Tarifa del Flete ($)", min_value=0.0, step=500.0)
                    destino = st.text_input("🏁 Ciudad de Destino")
                    
                    if lista_unidades:
                        unidad_manual = st.selectbox("🚛 Seleccionar Camión de la Flota", lista_unidades)
                    else:
                        unidad_manual = st.text_input("🚛 Camión / Placas de la Unidad (Manual)")
                
                boton_despachar = st.form_submit_button("🚀 Registrar y Despachar Viaje", use_container_width=True)
                
                if boton_despachar:
                    if not cliente or not origen or not destino or not operador_manual:
                        st.error("⚠️ Por favor, llena los campos esenciales (Cliente, Origen, Destino y Chofer).")
                    else:
                        try:
                            supabase = obtener_cliente()
                            datos_viaje = {
                                "id_cliente": cliente.strip(),
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

        # =========================================================
        # PESTAÑA 3: OPTIMIZACIÓN DE FLOTA (UNIDADES, CHOFERES E INCIDENCIAS)
        # =========================================================
        with tab3:
            st.header("⚙️ Control Central de Flota")
            
            sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🚛 Camiones", "👤 Choferes", "⚠️ Récord e Incidencias"])
            
            # --- SUB-PESTAÑA 1: CONTROL DE CAMIONES (TERMÓMETRO) ---
            with sub_tab1:
                st.subheader("Estatus Mecánico y de Mantenimiento")
                
                # Mostrar semáforo visual de unidades existentes
                try:
                    supabase = obtener_cliente()
                    res_unidades_ver = supabase.table("unidades").select("*").order("numero_economico").execute()
                    if res_unidades_ver.data:
                        # Generamos métricas en columnas para simular los termómetros de control
                        cols_mecanicas = st.columns(len(res_unidades_ver.data) if len(res_unidades_ver.data) <= 4 else 4)
                        for idx, uni in enumerate(res_unidades_ver.data):
                            col_act = cols_mecanicas[idx % 4]
                            est_icono = "🟢" if uni["estatus"] == "Disponible" else "🟡" if uni["estatus"] == "Mantenimiento Preventivo" else "🔴"
                            col_act.metric(label=f"{est_icono} {uni['numero_economico']}", value=uni["modelo"], delta=uni["estatus"])
                    else:
                        st.info("No hay camiones dados de alta.")
                except Exception as e:
                    st.error(f"Error al leer indicadores: {e}")

                st.divider()
                st.write("➕ **Registrar Nueva Unidad a la Flota**")
                with st.form("alta_unidad", clear_on_submit=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        num_eco = st.text_input("Número Económico (ej: Eco-05)")
                        placas_u = st.text_input("Placas de Circulación")
                    with c2:
                        modelo_u = st.text_input("Marca / Modelo (ej: Kenworth T680)")
                        anio_u = st.number_input("Año de la Unidad", min_value=1990, max_value=2027, value=2020, step=1)
                    with c3:
                        estatus_u = st.selectbox("Termómetro de Mantenimiento", ["Disponible", "Mantenimiento Preventivo", "Taller / Reparación"])
                    
                    if st.form_submit_button("Guardar Camión", use_container_width=True):
                        if not num_eco or not modelo_u:
                            st.error("El número económico y modelo son campos obligatorios.")
                        else:
                            try:
                                supabase.table("unidades").insert({
                                    "numero_economico": num_eco.strip(), "placas": placas_u.strip(),
                                    "modelo": modelo_u.strip(), "anio": int(anio_u), "estatus": estatus_u
                                }).execute()
                                st.success("🚛 Unidad añadida con éxito a la flotilla.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al guardar unidad: {e}")

            # --- SUB-PESTAÑA 2: CONTROL DE OPERADORES ---
            with sub_tab2:
                st.subheader("Gestión de Choferes Registrados")
                
                with st.form("alta_chofer", clear_on_submit=True):
                    ch1, ch2, ch3 = st.columns(3)
                    with ch1:
                        nom_chofer = st.text_input("Nombre Completo del Operador")
                    with ch2:
                        lic_chofer = st.text_input("Número de Licencia Federal")
                    with ch3:
                        tel_chofer = st.text_input("Teléfono de Contacto")
                        
                    if st.form_submit_button("Dar de Alta Chofer", use_container_width=True):
                        if not nom_chofer:
                            st.error("El nombre del operador es obligatorio.")
                        else:
                            try:
                                supabase.table("operadores").insert({
                                    "nombre": nom_chofer.strip(), "licencia": lic_chofer.strip(), "telefono": tel_chofer.strip()
                                }).execute()
                                st.success("👤 Chofer registrado de forma exitosa.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al guardar chofer: {e}")

            # --- SUB-PESTAÑA 3: RÉCORD, DISCREPANCIAS Y SANCIONES ---
            with sub_tab3:
                st.subheader("Récord de Desempeño y Sanciones por Chofer")
                st.write("Registra y audita penalizaciones, daños de carga o incidencias en ruta.")
                
                # Jalar operadores dinámicos para el reporte
                op_opciones = lista_operadores if lista_operadores else ["José Hernández"]
                
                with st.form("alta_incidencia", clear_on_submit=True):
                    col_inc1, col_inc2 = st.columns(2)
                    with col_inc1:
                        op_seleccionado = st.selectbox("Seleccionar Chofer a Reportar", op_opciones)
                        tipo_rep = st.selectbox("Tipo de Incidencia / Reporte", ["Sanción por Retraso", "Discrepancia de Combustible", "Daño a la Unidad / Carga", "Felicitación / Récord Limpio"])
                    with col_inc2:
                        puntos_penalizacion = st.slider("Descuento en Récord (Puntos)", min_value=0, max_value=5, value=1)
                        desc_inc = st.text_area("Detalle de la Discrepancia o Nota descriptiva")
                        
                    if st.form_submit_button("Aplicar Reporte al Historial", use_container_width=True):
                        if not desc_inc:
                            st.error("Por favor ingresa los detalles explicativos del reporte.")
                        else:
                            try:
                                supabase.table("incidencias_operadores").insert({
                                    "operador_nombre": op_seleccionado,
                                    "tipo_reporte": tipo_rep,
                                    "descripcion": desc_inc.strip(),
                                    "puntos_record": -int(puntos_penalizacion) if puntos_penalizacion > 0 else 0
                                }).execute()
                                st.success(f"⚠️ Reporte aplicado exitosamente al expediente de {op_seleccionado}.")
                            except Exception as e:
                                st.error(f"Error al procesar la incidencia: {e}")

                st.divider()
                st.write("📋 **Consulta de Expedientes en Tiempo Real**")
                op_consulta = st.selectbox("Filtrar historial del operador:", op_opciones, key="consulta_historial")
                
                try:
                    res_historial = supabase.table("incidencias_operadores").select("*").eq("operador_nombre", op_consulta).order("fecha", desc=True).execute()
                    if res_historial.data and len(res_historial.data) > 0:
                        df_hist = pd.DataFrame(res_historial.data)
                        st.dataframe(df_hist[["fecha", "tipo_reporte", "descripcion", "puntos_record"]].rename(columns={
                            "fecha": "📅 Fecha", "tipo_reporte": "🚨 Reporte", "descripcion": "🔍 Detalles", "puntos_record": "📉 Impacto Récord"
                        }), use_container_width=True, hide_index=True)
                    else:
                        st.info(f"🟢 El operador {op_consulta} mantiene un récord impecable sin discrepancias registradas.")
                except Exception as e:
                    st.error(f"Error al cargar el expediente: {e}")

    # =========================================================
    # VISTA PARA EL CLIENTE
    # =========================================================
    elif st.session_state.rol == "cliente":
        st.title("Portal de Clientes")
        st.subheader("📦 Estado de mis Embarques")
        st.write(f"Bienvenido. Consultando las cargas asignadas a: **{st.session_state.usuario}**")
        
        try:
            supabase = obtener_cliente()
            respuesta = supabase.table("viajes").select("*").order("id", desc=True).execute()
            
            if respuesta.data and len(respuesta.data) > 0:
                df_completo = pd.DataFrame(respuesta.data)
                col_filtro = "id_cliente" if "id_cliente" in df_completo.columns else "cliente"
                
                df_cliente = df_completo[df_completo[col_filtro].astype(str).str.strip() == st.session_state.usuario.strip()]
                
                if not df_cliente.empty:
                    df_cliente = df_cliente.rename(columns={
                        "origen": "📍 Origen", "destino": "🏁 Destino",
                        "unidad_manual": "🚛 Unidad asignada", "estatus": "🟢 Estatus de Entrega"
                    })
                    columnas_cliente = ["📍 Origen", "🏁 Destino", "🚛 Unidad asignada", "🟢 Estatus de Entrega"]
                    cols_finales = [c for c in columnas_cliente if c in df_cliente.columns]
                    st.dataframe(df_cliente[cols_finales], use_container_width=True, hide_index=True)
                else:
                    st.info("📭 Actualmente no tienes ningún embarque en tránsito con nosotros.")
            else:
                st.info("📭 Actualmente no tienes ningún embarque en tránsito con nosotros.")
        except Exception as e:
            st.error(f"❌ Error al consultar tus datos: {e}")
