# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
        
        # Reducción estratégica a solo 3 pestañas principales
        tab1, tab2, tab3 = st.tabs(["📊 Monitoreo y Utilidades", "📝 Operación de Fletes", "⚙️ Control de Flota"])
        supabase = obtener_cliente()

        # ---------------------------------------------------------
        # PESTAÑA 1: MAESTRA DE MONITOREO Y RENTABILIDAD EN VIVO
        # ---------------------------------------------------------
        with tab1:
            st.subheader("📊 Centro de Mando Financiero")
            st.write("Haz doble clic en cualquier celda para corregir datos del viaje (Tarifa, Cliente, Origen, Destino). Las columnas grises se calculan automáticamente.")
            
            try:
                res_v = supabase.table("viajes").select("id", "id_cliente", "origen", "destino", "tarifa", "operador_manual", "unidad_manual", "estatus").order("id", desc=True).execute()
                res_g = supabase.table("gastos").select("id", "id_viaje", "tipo_gasto", "monto", "descripcion").order("id", desc=True).execute()
                
                if res_v.data:
                    df_v = pd.DataFrame(res_v.data)
                    df_g = pd.DataFrame(res_g.data) if res_g.data else pd.DataFrame(columns=["id", "id_viaje", "tipo_gasto", "monto", "descripcion"])
                    
                    if not df_g.empty:
                        df_g_sum = df_g.groupby("id_viaje")["monto"].sum().reset_index()
                        df_g_sum = df_g_sum.rename(columns={"monto": "Gastos Totales"})
                        df_merged = pd.merge(df_v, df_g_sum, left_on="id", right_on="id_viaje", how="left")
                        df_merged["Gastos Totales"] = df_merged["Gastos Totales"].fillna(0)
                    else:
                        df_merged = df_v.copy()
                        df_merged["Gastos Totales"] = 0
                        
                    df_merged["Utilidad Neta"] = df_merged["tarifa"] - df_merged["Gastos Totales"]
                    
                    # Tabla Maestra Interactiva de Viajes
                    df_viajes_edicion = df_merged[["id", "id_cliente", "origen", "destino", "tarifa", "Gastos Totales", "Utilidad Neta"]]
                    cambios_viajes = st.data_editor(
                        df_viajes_edicion,
                        key="editor_viajes_maestro",
                        use_container_width=True,
                        hide_index=True,
                        disabled=["id", "Gastos Totales", "Utilidad Neta"],
                        column_config={
                            "id": "ID Viaje", "id_cliente": "🏢 Cliente", "origen": "📍 Origen", "destino": "🏁 Destino",
                            "tarifa": st.column_config.NumberColumn("💰 Tarifa ($)", min_value=0.0, step=500.0),
                            "Gastos Totales": "🛑 Total Gastos ($)", "Utilidad Neta": "💵 Utilidad Neta ($)"
                        }
                    )
                    
                    if st.button("💾 Guardar Correcciones de Viajes", use_container_width=True):
                        for i, fila in cambios_viajes.iterrows():
                            original = df_viajes_edicion.iloc[i]
                            if not fila.equals(original):
                                supabase.table("viajes").update({
                                    "id_cliente": fila["id_cliente"], "origen": fila["origen"],
                                    "destino": fila["destino"], "tarifa": float(fila["tarifa"])
                                }).eq("id", int(fila["id"])).execute()
                        st.success("🎉 ¡Cambios guardados con éxito!")
                        st.rerun()
                        
                    # Tabla Secundaria de Desglose de Gastos
                    st.divider()
                    st.subheader("🔍 Desglose Individual de Tickets de Gasto")
                    if not df_g.empty:
                        df_g_edit = df_g[["id", "id_viaje", "tipo_gasto", "monto", "descripcion"]]
                        cambios_gastos = st.data_editor(
                            df_g_edit,
                            key="editor_costos_maestro",
                            use_container_width=True,
                            hide_index=True,
                            disabled=["id", "id_viaje", "tipo_gasto"],
                            column_config={
                                "id_viaje": "ID Viaje", "tipo_gasto": "Concepto",
                                "monto": st.column_config.NumberColumn("Monto ($)", min_value=0.0, step=50.0), "descripcion": "Nota / Detalle"
                            }
                        )
                        if st.button("💾 Guardar Correcciones de Tickets", use_container_width=True):
                            for i, fila in cambios_gastos.iterrows():
                                original = df_g_edit.iloc[i]
                                if not fila.equals(original):
                                    supabase.table("gastos").update({
                                        "monto": float(fila["monto"]), "descripcion": fila["descripcion"].strip()
                                    }).eq("id", int(fila["id"])).execute()
                            st.success("🎉 ¡Tickets actualizados!")
                            st.rerun()
                    else:
                        st.info("No hay tickets de gastos registrados en el sistema.")
                else:
                    st.info("📭 No hay fletes registrados aún.")
            except Exception as e:
                st.error(f"Error en panel de control: {e}")

        # ---------------------------------------------------------
        # PESTAÑA 2: OPERACIÓN DE FLETES (DESPACHO + LIQUIDACIÓN UNIFICADOS)
        # ---------------------------------------------------------
        with tab2:
            st.header("📝 Gestión de Operación Diaria")
            
            # Sub-sección A: Crear Viajes
            st.subheader("➕ Despachar Nuevo Viaje")
            lista_operadores = []
            lista_unidades = []
            try:
                res_ops = supabase.table("operadores").select("nombre").order("nombre").execute()
                if res_ops.data:
                    lista_operadores = [row["nombre"] for row in res_ops.data]
                res_unis = supabase.table("unidades").select("numero_economico", "modelo").order("numero_economico").execute()
                if res_unis.data:
                    lista_unidades = [f"{row['numero_economico']} - {row['modelo']}" for row in res_unis.data]
            except Exception as e:
                st.warning(f"⚠️ Nota: Error al precargar listas dinámicas.")

            with st.form("formulario_despacho_maestro", clear_on_submit=True):
                col_flete1, col_flete2 = st.columns(2)
                with col_flete1:
                    cliente = st.text_input("🏢 Nombre del Cliente")
                    origen = st.text_input("📍 Ciudad de Origen")
                    operador_manual = st.selectbox("👤 Seleccionar Chofer", lista_operadores) if lista_operadores else st.text_input("👤 Chofer (Manual)")
                with col_flete2:
                    tarifa = st.number_input("💰 Tarifa del Flete ($)", min_value=0.0, step=500.0)
                    destino = st.text_input("🏁 Ciudad de Destino")
                    unidad_manual = st.selectbox("Compañía / Camión", lista_unidades) if lista_unidades else st.text_input("🚛 Camión (Manual)")
                
                if st.form_submit_button("🚀 Registrar y Despachar Viaje", use_container_width=True):
                    if cliente and origen and destino:
                        supabase.table("viajes").insert({
                            "id_cliente": cliente.strip(), "origen": origen.strip(), "destino": destino.strip(),
                            "operador_manual": operador_manual.strip(), "unidad_manual": unidad_manual.strip(), "tarifa": tarifa, "estatus": "En Tránsito"
                        }).execute()
                        st.success("✅ ¡Viaje lanzado con éxito hacia la ruta!")
                        st.rerun()
                    else:
                        st.error("Por favor completa los campos obligatorios.")

            # Sub-sección B: Liquidación Inmediata de Gastos (Unificado abajo)
            st.divider()
            st.subheader("💵 Liquidación de Gastos en Ruta")
            st.write("Registra los comprobantes y viáticos de combustible o casetas acumulados por el chofer.")
            
            opciones_viajes = {}
            try:
                res_viajes_gastos = supabase.table("viajes").select("id", "id_cliente", "destino").order("id", desc=True).execute()
                if res_viajes_gastos.data:
                    for v in res_viajes_gastos.data:
                        opciones_viajes[v["id"]] = f"ID: {v['id']} | {v['id_cliente']} -> {v['destino']}"
            except:
                pass
                
            if opciones_viajes:
                with st.form("registro_gasto_unificado_form", clear_on_submit=True):
                    viaje_seleccionado_id = st.selectbox("Asociar Liquidación al Viaje ID:", list(opciones_viajes.keys()), format_func=lambda x: opciones_viajes[x])
                    st.write("Introduce los montos correspondientes:")
                    
                    col_g1, col_g2 = st.columns(2)
                    with col_g1:
                        monto_diesel = st.number_input("⛽ Diésel ($)", min_value=0.0, step=500.0, value=0.0)
                        monto_casetas = st.number_input("🛣️ Casetas ($)", min_value=0.0, step=100.0, value=0.0)
                        monto_maniobras = st.number_input("🏗️ Maniobras / Descargas ($)", min_value=0.0, step=100.0, value=0.0)
                    with col_g2:
                        monto_sueldo = st.number_input("👤 Sueldo Operador ($)", min_value=0.0, step=500.0, value=0.0)
                        monto_taller = st.number_input("🔧 Reparación en Ruta ($)", min_value=0.0, step=200.0, value=0.0)
                        monto_otros = st.number_input("📦 Otros Gastos ($)", min_value=0.0, step=100.0, value=0.0)
                    
                    nota_liquidacion = st.text_input("📝 Nota descriptiva de la liquidación")
                    
                    if st.form_submit_button("💾 Guardar Gastos de Liquidación", use_container_width=True):
                        gastos_a_insertar = [
                            ("Diésel", monto_diesel), ("Casetas", monto_casetas),
                            ("Maniobras", monto_maniobras), ("Sueldo Operador", monto_sueldo),
                            ("Taller", monto_taller), ("Otros", monto_otros)
                        ]
                        for tipo_concepto, monto_valor in gastos_a_insertar:
                            if monto_valor > 0:
                                supabase.table("gastos").insert({
                                    "id_viaje": viaje_seleccionado_id, "tipo_gasto": tipo_concepto,
                                    "monto": monto_valor, "descripcion": nota_liquidacion.strip() if nota_liquidacion else f"Registro de {tipo_concepto}"
                                }).execute()
                        st.success("✅ ¡Liquidación guardada exitosamente!")
                        st.rerun()
            else:
                st.info("No hay viajes disponibles para liquidar costos.")

        # ---------------------------------------------------------
        # PESTAÑA 3: CONTROL CENTRAL DE FLOTA
        # ---------------------------------------------------------
        with tab3:
            st.header("⚙️ Control Central de Flota")
            sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs(["🚛 Camiones", "👤 Choferes", "⚠️ Reportar Incidencia", "📋 Reporte Semanal"])
            
            with sub_tab1:
                st.subheader("Estatus Mecánico y Modificaciones")
                try:
                    res_unidades_ver = supabase.table("unidades").select("*").order("numero_economico").execute()
                    if res_unidades_ver.data:
                        df_unis = pd.DataFrame(res_unidades_ver.data)
                        m1, m2, m3 = st.columns(3)
                        m1.metric("🟢 Disponibles", len(df_unis[df_unis['estatus'] == 'Disponible']))
                        m2.metric("🟡 En Preventivo", len(df_unis[df_unis['estatus'] == 'Mantenimiento Preventivo']))
                        m3.metric("🔴 En Taller", len(df_unis[df_unis['estatus'] == 'Taller / Reparación']))
                        
                        df_unis_edit = df_unis[["id", "numero_economico", "placas", "modelo", "anio", "estatus"]]
                        cambios_unis = st.data_editor(
                            df_unis_edit, key="editor_unidades", use_container_width=True, hide_index=True, disabled=["id"],
                            column_config={
                                "numero_economico": "Económico", "placas": "Placas", "modelo": "Marca/Modelo", "anio": "Año",
                                "estatus": st.column_config.SelectboxColumn("Termómetro", options=["Disponible", "Mantenimiento Preventivo", "Taller / Reparación"], required=True)
                            }
                        )
                        if st.button("💾 Guardar Cambios en Camiones", use_container_width=True):
                            for i, fila in cambios_unis.iterrows():
                                original = df_unis_edit.iloc[i]
                                if not fila.equals(original):
                                    supabase.table("unidades").update({
                                        "numero_economico": fila["numero_economico"], "placas": fila["placas"],
                                        "modelo": fila["modelo"], "anio": int(fila["anio"]), "estatus": fila["estatus"]
                                    }).eq("id", int(fila["id"])).execute()
                            st.success("¡Flotilla actualizada!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

                st.divider()
                st.write("➕ **Añadir Camión Nuevo**")
                with st.form("alta_unidad", clear_on_submit=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        num_eco = st.text_input("Número Económico")
                        placas_u = st.text_input("Placas")
                    with c2:
                        modelo_u = st.text_input("Marca / Modelo")
                        anio_u = st.number_input("Año", min_value=1990, max_value=2027, value=2020)
                    with c3:
                        estatus_u = st.selectbox("Termómetro Inicial", ["Disponible", "Mantenimiento Preventivo", "Taller / Reparación"])
                    if st.form_submit_button("Guardar Camión Nuevo"):
                        if num_eco and modelo_u:
                            supabase.table("unidades").insert({
                                "numero_economico": num_eco.strip(), "placas": placas_u.strip(),
                                "modelo": modelo_u.strip(), "anio": int(anio_u), "estatus": estatus_u
                            }).execute()
                            st.success("🚛 Camión añadido.")
                            st.rerun()

            with sub_tab2:
                st.subheader("Gestión y Corrección de Operadores")
                try:
                    res_ops_ver = supabase.table("operadores").select("*").order("nombre").execute()
                    if res_ops_ver.data:
                        df_ops = pd.DataFrame(res_ops_ver.data)
                        df_ops_edit = df_ops[["id", "nombre", "licencia", "telefono"]]
                        cambios_ops = st.data_editor(
                            df_ops_edit, key="editor_operadores", use_container_width=True, hide_index=True, disabled=["id"],
                            column_config={"nombre": "Nombre Completo", "licencia": "Licencia Federal", "telefono": "Teléfono Contacto"}
                        )
                        if st.button("💾 Guardar Cambios en Choferes", use_container_width=True):
                            for i, fila in cambios_ops.iterrows():
                                original = df_ops_edit.iloc[i]
                                if not fila.equals(original):
                                    supabase.table("operadores").update({
                                        "nombre": fila["nombre"], "licencia": fila["licencia"], "telefono": fila["telefono"]
                                    }).eq("id", int(fila["id"])).execute()
                            st.success("¡Padrón actualizado!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

                st.divider()
                st.write("➕ **Dar de Alta Nuevo Chofer**")
                with st.form("alta_chofer", clear_on_submit=True):
                    ch1, ch2, ch3 = st.columns(3)
                    with ch1:
                        nom_chofer = st.text_input("Nombre Operador")
                    with ch2:
                        lic_chofer = st.text_input("Licencia")
                    with ch3:
                        tel_chofer = st.text_input("Teléfono")
                    if st.form_submit_button("Guardar Chofer"):
                        if nom_chofer:
                            supabase.table("operadores").insert({
                                "nombre": nom_chofer.strip(), "licencia": lic_chofer.strip(), "telefono": tel_chofer.strip()
                            }).execute()
                            st.success("👤 Chofer guardado.")
                            st.rerun()

            with sub_tab3:
                st.subheader("Levantar Reporte o Penalización")
                op_opciones = lista_operadores if lista_operadores else ["José Hernández"]
                with st.form("alta_incidencia", clear_on_submit=True):
                    col_inc1, col_inc2 = st.columns(2)
                    with col_inc1:
                        op_seleccionado = st.selectbox("Chofer Involucrado", op_opciones)
                        tipo_rep = st.selectbox("Gravedad / Tipo de Reporte", ["Sanción por Retraso", "Discrepancia de Combustible", "Daño a la Unidad / Carga", "Infracción de Tránsito", "Felicitación"])
                    with col_inc2:
                        puntos_penalizacion = st.slider("Puntos a Descontar de su Récord", min_value=0, max_value=5, value=1)
                        desc_inc = st.text_area("Explicación de la discrepancia detectada")
                    if st.form_submit_button("Aplicar Reporte al Expediente"):
                        if desc_inc:
                            supabase.table("incidencias_operadores").insert({
                                "operador_nombre": op_seleccionado, "tipo_reporte": tipo_rep,
                                "descripcion": desc_inc.strip(), "puntos_record": -int(puntos_penalizacion) if puntos_penalizacion > 0 else 0
                            }).execute()
                            st.success(f"Reporte aplicado.")
                            st.rerun()

            with sub_tab4:
                st.subheader("📋 Boletín Semanal de Rendimiento y Desempeño")
                try:
                    hoy = datetime.now()
                    inicio_semana = hoy - timedelta(days=hoy.weekday())
                    fecha_lunes = inicio_semana.strftime("%Y-%m-%d")
                    st.info(f"📅 **Período Evaluado:** Del lunes {fecha_lunes} al día de hoy.")
                    res_todas = supabase.table("incidencias_operadores").select("*").execute()
                    if res_todas.data:
                        df_todas = pd.DataFrame(res_todas.data)
                        df_todas['fecha'] = pd.to_datetime(df_todas['fecha'])
                        df_semana = df_todas[df_todas['fecha'] >= pd.to_datetime(fecha_lunes)]
                        if not df_semana.empty:
                            st.warning(f"🚨 **Alertas de la Semana:** Se han levantado {len(df_semana)} reportes.")
                            for _, r in df_semana.iterrows():
                                st.chat_message("assistant", avatar="⚠️").write(f"**{r['operador_nombre']}** - *{r['tipo_reporte']}* ({r['puntos_record']} pts). \n\n*Detalles: {r['descripcion']}*")
                        else:
                            st.success("✨ **Boletín Semanal:** Operación limpia.")
                        st.divider()
                        df_record = df_todas.groupby("operador_nombre")["puntos_record"].sum().reset_index()
                        df_record = df_record.rename(columns={"operador_nombre": "👤 Chofer", "puntos_record": "📉 Puntos Acumulados"})
                        st.dataframe(df_record.sort_values(by="📉 Puntos Acumulados"), use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Error: {e}")

    # =========================================================
    # VISTA PARA EL CLIENTE
    # =========================================================
    elif st.session_state.rol == "cliente":
        st.title("Portal de Clientes")
        st.subheader("📦 Estado de mis Embarques")
        st.write(f"Bienvenido. Consultando las cargas asignadas a: **{st.session_state.usuario}**")
        try:
            respuesta = supabase.table("viajes").select("*").order("id", desc=True).execute()
            if respuesta.data and len(respuesta.data) > 0:
                df_completo = pd.DataFrame(respuesta.data)
                col_filtro = "id_cliente" if "id_cliente" in df_completo.columns else "cliente"
                df_cliente = df_completo[df_completo[col_filtro].astype(str).str.strip() == st.session_state.usuario.strip()]
                if not df_cliente.empty:
                    df_cliente = df_cliente.rename(columns={"origen": "📍 Origen", "destino": "🏁 Destino", "unidad_manual": "🚛 Unidad asignada", "estatus": "🟢 Estatus de Entrega"})
                    st.dataframe(df_cliente[["📍 Origen", "🏁 Destino", "🚛 Unidad asignada", "🟢 Estatus de Entrega"]], use_container_width=True, hide_index=True)
                else:
                    st.info("📭 Actualmente no tienes ningún embarque.")
            else:
                st.info("📭 Actualmente no tienes ningún embarque.")
        except Exception as e:
            st.error(f"❌ Error: {e}")
