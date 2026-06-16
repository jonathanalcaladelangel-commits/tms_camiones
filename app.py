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
        
        # Pestañas principales
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Viajes", "➕ Despacho", "💰 Gastos", "⚙️ Flota"])
        supabase = obtener_cliente()

        # PESTAÑA 1: VISUALIZACIÓN DE VIAJES EN TIEMPO REAL
        with tab1:
            st.subheader("📊 Monitoreo de Unidades")
            st.write("Estatus actual de los fletes registrados en el sistema.")
            
            try:
                respuesta = supabase.table("viajes").select("*").order("id", desc=True).execute()
                
                if respuesta.data and len(respuesta.data) > 0:
                    df_viajes = pd.DataFrame(respuesta.data)
                    col_cliente_db = "id_cliente" if "id_cliente" in df_viajes.columns else "cliente"
                    
                    columnas_mapeo = {
                        "id": "ID Viaje",
                        col_cliente_db: "🏢 Cliente",
                        "origen": "📍 Origen",
                        "destino": "🏁 Destino",
                        "operador_manual": "👤 Chofer",
                        "unidad_manual": "🚛 Unidad",
                        "tarifa": "💰 Tarifa ($)",
                        "estatus": "🟢 Estatus"
                    }
                    
                    df_mostrar = df_viajes[list(columnas_mapeo.keys())].rename(columns=columnas_mapeo)
                    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
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
        # PESTAÑA 3: GASTOS, LIQUIDACIONES Y MODIFICACIONES EN VIVO
        # =========================================================
        with tab3:
            st.header("💰 Liquidación de Gastos y Utilidades")
            
            sub_g1, sub_g2 = st.tabs(["💵 Liquidación Múltiple", "📈 Reporte y Edición de Costos"])
            
            # Obtener viajes para el selector dinámico
            opciones_viajes = {}
            try:
                res_viajes_gastos = supabase.table("viajes").select("id", "id_cliente", "destino").order("id", desc=True).execute()
                if res_viajes_gastos.data:
                    for v in res_viajes_gastos.data:
                        opciones_viajes[v["id"]] = f"ID: {v['id']} | Cliente: {v['id_cliente']} -> Destino: {v['destino']}"
            except Exception as e:
                st.error(f"Error al cargar fletes para gastos: {e}")
                
            # SUB-PESTAÑA 1: FORMULARIO DINÁMICO DE LIQUIDACIÓN COMPLETA
            with sub_g1:
                st.subheader("Registrar Liquidación Completa")
                st.write("Introduce los montos de los conceptos que apliquen para este flete. Puedes llenar varios a la vez.")
                
                if opciones_viajes:
                    with st.form("registro_gasto_multiple", clear_on_submit=True):
                        viaje_seleccionado_id = st.selectbox("Selecciona el Viaje Asociado", list(opciones_viajes.keys()), format_func=lambda x: opciones_viajes[x])
                        st.divider()
                        
                        col_g1, col_g2 = st.columns(2)
                        
                        with col_g1:
                            monto_diesel = st.number_input("⛽ Diésel ($)", min_value=0.0, step=500.0, value=0.0)
                            monto_casetas = st.number_input("🛣️ Casetas ($)", min_value=0.0, step=100.0, value=0.0)
                            monto_maniobras = st.number_input("🏗️ Maniobras / Descargas ($)", min_value=0.0, step=100.0, value=0.0)
                            
                        with col_g2:
                            monto_sueldo = st.number_input("👤 Sueldo / Comisión Operador ($)", min_value=0.0, step=500.0, value=0.0)
                            monto_taller = st.number_input("🔧 Taller / Reparación en Ruta ($)", min_value=0.0, step=200.0, value=0.0)
                            monto_otros = st.number_input("📦 Otros Gastos ($)", min_value=0.0, step=100.0, value=0.0)
                        
                        st.divider()
                        nota_liquidacion = st.text_input("📝 Nota global de la liquidación (ej: Tickets operador)")
                        
                        if st.form_submit_button("🚀 Guardar Liquidación Completa", use_container_width=True):
                            gastos_a_insertar = [
                                ("Diésel", monto_diesel), ("Casetas", monto_casetas),
                                ("Maniobras", monto_maniobras), ("Sueldo Operador", monto_sueldo),
                                ("Taller", monto_taller), ("Otros", monto_otros)
                            ]
                            
                            contador_inserciones = 0
                            errores = []
                            
                            for tipo_concepto, monto_valor in gastos_a_insertar:
                                if monto_valor > 0:
                                    try:
                                        supabase.table("gastos").insert({
                                            "id_viaje": viaje_seleccionado_id, "tipo_gasto": tipo_concepto,
                                            "monto": monto_valor, "descripcion": nota_liquidacion.strip() if nota_liquidacion else f"Registro de {tipo_concepto}"
                                        }).execute()
                                        contador_inserciones += 1
                                    except Exception as err:
                                        errores.append(f"{tipo_concepto}: {err}")
                            
                            if errores:
                                st.error(f"❌ Hubo problemas con algunos conceptos: {errores}")
                            if contador_inserciones > 0:
                                st.success(f"✅ ¡Liquidación procesada! Se guardaron {contador_inserciones} conceptos.")
                                st.rerun()
                else:
                    st.info("No hay viajes registrados a los cuales asignarles gastos.")
                    
            # SUB-PESTAÑA 2: REPORTE Y EDITOR DE COSTOS EN VIVO
            with sub_g2:
                st.subheader("Rentabilidad Real por Flete")
                st.write("Cálculo dinámico de utilidades.")
                
                try:
                    res_v = supabase.table("viajes").select("id", "id_cliente", "destino", "tarifa").order("id", desc=True).execute()
                    res_g = supabase.table("gastos").select("id", "id_viaje", "tipo_gasto", "monto", "descripcion").order("id", desc=True).execute()
                    
                    if res_v.data:
                        df_v = pd.DataFrame(res_v.data)
                        df_g = pd.DataFrame(res_g.data) if res_g.data else pd.DataFrame(columns=["id", "id_viaje", "tipo_gasto", "monto", "descripcion"])
                        
                        # Pintar reporte global arriba
                        if not df_g.empty:
                            df_g_sum = df_g.groupby("id_viaje")["monto"].sum().reset_index()
                            df_g_sum = df_g_sum.rename(columns={"monto": "Gastos Totales"})
                            df_merged = pd.merge(df_v, df_g_sum, left_on="id", right_on="id_viaje", how="left")
                            df_merged["Gastos Totales"] = df_merged["Gastos Totales"].fillna(0)
                        else:
                            df_merged = df_v.copy()
                            df_merged["Gastos Totales"] = 0
                            
                        df_merged["Utilidad Neta"] = df_merged["tarifa"] - df_merged["Gastos Totales"]
                        
                        df_merged_rep = df_merged.rename(columns={
                            "id": "ID Viaje", "id_cliente": "🏢 Cliente", "destino": "🏁 Destino",
                            "tarifa": "💰 Tarifa ($)", "Gastos Totales": "🛑 Total Gastos ($)", "Utilidad Neta": "💵 Utilidad Neta ($)"
                        })
                        st.dataframe(df_merged_rep[["ID Viaje", "🏢 Cliente", "🏁 Destino", "💰 Tarifa ($)", "🛑 Total Gastos ($)", "💵 Utilidad Neta ($)"]], use_container_width=True, hide_index=True)
                        
                        # --- SECCIÓN EXCLUSIVA DE EDICIÓN Y CORRECCIÓN DE GASTOS ---
                        st.divider()
                        st.subheader("📝 Corregir o Modificar Costos Inyectados")
                        st.write("Haz doble clic sobre cualquier monto o nota para cambiar el dato, luego presiona el botón de guardar.")
                        
                        if not df_g.empty:
                            # Mapeamos para que sea fácil de entender para el usuario qué viaje se está editando
                            df_g_edit = df_g[["id", "id_viaje", "tipo_gasto", "monto", "descripcion"]]
                            
                            cambios_gastos = st.data_editor(
                                df_g_edit,
                                key="editor_costos_vivos",
                                use_container_width=True,
                                hide_index=True,
                                disabled=["id", "id_viaje", "tipo_gasto"], # Protegemos para que solo edites el dinero y notas
                                column_config={
                                    "id_viaje": "ID Viaje",
                                    "tipo_gasto": "Concepto",
                                    "monto": st.column_config.NumberColumn("Monto Corregido ($)", min_value=0.0, step=50.0),
                                    "descripcion": "Nota / Descripción"
                                }
                            )
                            
                            if st.button("💾 Guardar Cambios en Gastos", use_container_width=True):
                                for i, fila in cambios_gastos.iterrows():
                                    original = df_g_edit.iloc[i]
                                    # Si el registro cambió, se actualiza en Supabase
                                    if not fila.equals(original):
                                        supabase.table("gastos").update({
                                            "monto": float(fila["monto"]),
                                            "descripcion": fila["descripcion"].strip()
                                        }).eq("id", int(fila["id"])).execute()
                                st.success("🎉 ¡Historial de costos corregido y utilidad actualizada!")
                                st.rerun()
                        else:
                            st.info("No hay gastos registrados individuales todavía para modificar.")
                            
                except Exception as e:
                    st.error(f"Error al cargar panel de control de utilidades: {e}")

        # =========================================================
        # PESTAÑA 4: CONTROL CENTRAL DE FLOTA
        # =========================================================
        with tab4:
            st.header("⚙️ Control Central de Flota")
            
            sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs(["🚛 Camiones", "👤 Choferes", "⚠️ Reportar Incidencia", "📋 Reporte Semanal"])
            
            # --- SUB-PESTAÑA 1: CONTROL Y EDICIÓN DE CAMIONES ---
            with sub_tab1:
                st.subheader("Estatus Mecánico y Modificaciones")
                
                try:
                    res_unidades_ver = supabase.table("unidades").select("*").order("numero_economico").execute()
                    if res_unidades_ver.data:
                        df_unis = pd.DataFrame(res_unidades_ver.data)
                        
                        disponibles = len(df_unis[df_unis['estatus'] == 'Disponible'])
                        preventivos = len(df_unis[df_unis['estatus'] == 'Mantenimiento Preventivo'])
                        taller = len(df_unis[df_unis['estatus'] == 'Taller / Reparación'])
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("🟢 Unidades Disponibles", disponibles)
                        m2.metric("🟡 En Preventivo", preventivos)
                        m3.metric("🔴 En Taller / Parados", taller)
                        
                        st.write("📝 **Editor de Camiones en Vivo:**")
                        df_unis_edit = df_unis[["id", "numero_economico", "placas", "modelo", "anio", "estatus"]]
                        
                        cambios_unis = st.data_editor(
                            df_unis_edit, 
                            key="editor_unidades", 
                            use_container_width=True, 
                            hide_index=True,
                            disabled=["id"],
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
                            st.success("¡Flotilla de camiones actualizada con éxito!")
                            st.rerun()
                    else:
                        st.info("No hay camiones registrados.")
                except Exception as e:
                    st.error(f"Error en módulo de camiones: {e}")

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

            # --- SUB-PESTAÑA 2: CONTROL Y EDICIÓN DE CHOFERES ---
            with sub_tab2:
                st.subheader("Gestión y Corrección de Operadores")
                
                try:
                    res_ops_ver = supabase.table("operadores").select("*").order("nombre").execute()
                    if res_ops_ver.data:
                        df_ops = pd.DataFrame(res_ops_ver.data)
                        
                        st.write("📝 **Editor de Choferes en Vivo:**")
                        df_ops_edit = df_ops[["id", "nombre", "licencia", "telefono"]]
                        
                        cambios_ops = st.data_editor(
                            df_ops_edit, 
                            key="editor_operadores", 
                            use_container_width=True, 
                            hide_index=True,
                            disabled=["id"],
                            column_config={"nombre": "Nombre Completo", "licencia": "Licencia Federal", "telefono": "Teléfono Contacto"}
                        )
                        
                        if st.button("💾 Guardar Cambios en Choferes", use_container_width=True):
                            for i, fila in cambios_ops.iterrows():
                                original = df_ops_edit.iloc[i]
                                if not fila.equals(original):
                                    supabase.table("operadores").update({
                                        "nombre": fila["nombre"], "licencia": fila["licencia"], "telefono": fila["telefono"]
                                    }).eq("id", int(fila["id"])).execute()
                            st.success("¡Padrón de choferes actualizado!")
                            st.rerun()
                    else:
                        st.info("No hay operadores registrados.")
                except Exception as e:
                    st.error(f"Error en módulo de choferes: {e}")

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

            # --- SUB-PESTAÑA 3: LEVANTAR INCIDENCIAS ---
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
                            st.success(f"Reporte aplicado al expediente de {op_seleccionado}.")
                            st.rerun()

            # --- SUB-PESTAÑA 4: REPORTE SEMANAL ---
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
                                st.chat_message("assistant", avatar="⚠️").write(
                                    f"**{r['operador_nombre']}** recibió un reporte de tipo *{r['tipo_reporte']}* con un impacto de **{r['puntos_record']} pts**. \n\n*Detalles: {r['descripcion']}*"
                                )
                        else:
                            st.success("✨ **Boletín Semanal:** Operación limpia. No hay sanciones registradas esta semana.")
                        
                        st.divider()
                        st.write("📊 **Récord Acumulado General de Choferes:**")
                        df_record = df_todas.groupby("operador_nombre")["puntos_record"].sum().reset_index()
                        df_record = df_record.rename(columns={"operador_nombre": "👤 Chofer", "puntos_record": "📉 Puntos Acumulados"})
                        st.dataframe(df_record.sort_values(by="📉 Puntos Acumulados"), use_container_width=True, hide_index=True)
                    else:
                        st.info("No hay historial de incidencias registrado aún.")
                except Exception as e:
                    st.error(f"Error al generar reporte semanal: {e}")

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
