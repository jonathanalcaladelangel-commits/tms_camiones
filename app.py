# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from Dao.usuario_dao import UsuarioDAO
from database.conexion import obtener_cliente

# Zona horaria local (Frontera)
LOCAL_TZ = pytz.timezone("America/Monterrey")

st.set_page_config(page_title="BorderTransfer Pro", page_icon="🚛", layout="centered")

# Inicialización segura de estados de sesión
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.rol = None
    st.session_state.usuario = ""

# --- FORMULARIO DE ACCESO ACCESIBLE ---
if not st.session_state.autenticado:
    st.title("🚛 BorderTransfer Pro")
    st.caption("Sistema de Control de Cruces Fronterizos y Telemetría")
    
    usuario_input = st.text_input("Usuario")
    contrasena_input = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar al Sistema", use_container_width=True):
        # NOTA: Asegúrate de que en tu BD existan usuarios con roles 'admin', 'chofer' o 'cliente'
        rol_detectado = UsuarioDAO.validar_usuario(usuario_input, contrasena_input)
        if rol_detectado:
            st.session_state.autenticado = True
            st.session_state.rol = rol_detectado
            st.session_state.usuario = usuario_input
            st.rerun()
        else:
            st.error("Credenciales inválidas para el cruce.")

else:
    # Header minimalista de sesión
    col_u, col_l = st.columns([3, 1])
    col_u.write(f"👤 **{st.session_state.usuario.upper()}** | Rol: `{st.session_state.rol.upper()}`")
    if col_l.button("Salir", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.rol = None
        st.session_state.usuario = ""
        st.rerun()
    st.divider()

    supabase = obtener_cliente()

    # =========================================================================
    # 👑 1. EXPERIENCIA DEL CEO / ADMINISTRADOR (Panel Ejecutivo)
    # =========================================================================
    if st.session_state.rol == "admin":
        st.title("Centro de Control de Transfers")
        
        tab_monitoreo, tab_despacho, tab_analitica = st.tabs(["🚦 Tráfico e Inspección", "📝 Despacho Aduanal", "📋 Resumen Semanal"])
        
        with tab_monitoreo:
            st.subheader("👀 Estado de la Flota en el Puente")
            st.write("Triangulación de estatus operativos en tiempo real para evitar Reward Hacking.")
            
            try:
                # Jalar los viajes activos de la frontera
                res_v = supabase.table("viajes").select("*").order("id", desc=True).execute()
                if res_v.data:
                    df_viajes = pd.DataFrame(res_v.data)
                    
                    # Filtrar los que están activamente en el puente o fila
                    df_activos = df_viajes[df_viajes["estatus"].isin(["En Tránsito", "En Fila del Puente", "Módulo de Aduana", "En Inspección", "Retrasado por Tráfico"])]
                    
                    if not df_activos.empty:
                        for _, flete in df_activos.iterrows():
                            # Generar tarjeta de alerta contextual tipo Semáforo Inteligente
                            motivo = flete.get("motivo_demora", "Ninguna")
                            estatus_actual = flete["estatus"]
                            
                            if estatus_actual == "Retrasado por Tráfico" or motivo != "Ninguna":
                                color_alerta = "🔴 ALERTA DE DEMORA EXTERNA"
                                ayuda_contexto = f"El operador reportó una anomalía: **{motivo}**."
                            elif estatus_actual in ["Módulo de Aduana", "En Inspección"]:
                                color_alerta = "🟡 PROCESO ADUANAL ACTIVO"
                                ayuda_contexto = "Unidad cruzando el recinto fiscal."
                            else:
                                color_alerta = "🟢 EN TIEMPO PROMEDIO"
                                ayuda_contexto = "Flujo normal en fila."
                                
                            with st.container(border=True):
                                c1, c2 = st.columns([3, 1])
                                c1.markdown(f"### Viaje ID #{flete['id']} - {flete['id_cliente']}")
                                c1.markdown(f"**Ruta:** {flete['origen']} ➡️ {flete['destino']} | **Caja:** `{flete.get('tipo_movimiento', 'Cargado')}` ({flete.get('tipo_operacion', 'Exportación')})")
                                c1.markdown(f"📌 **Ubicación Reportada:** `{estatus_actual}`")
                                c2.markdown(f"<p style='text-align:center;'><b>{color_alerta}</b></p>", unsafe_allow_html=True)
                                st.caption(ayuda_contexto)
                    else:
                        st.success("✨ Todas las unidades han completado sus cruces. Patio limpio.")
                else:
                    st.info("No hay fletes registrados en el sistema.")
            except Exception as e:
                st.error(f"Error de lectura real-time: {e}")
                
        with tab_despacho:
            st.subheader("➕ Despachar Transfer (Cruces Rápidos)")
            
            # Cargar dinámicamente camiones y choferes para evitar errores tipográficos
            lista_ops, lista_unis = [], []
            try:
                r_op = supabase.table("operadores").select("nombre").execute()
                r_un = supabase.table("unidades").select("numero_economico").execute()
                lista_ops = [x["nombre"] for x in r_op.data] if r_op.data else []
                lista_unis = [x["numero_economico"] for x in r_un.data] if r_un.data else []
            except:
                pass

            with st.form("form_despacho_frontier", clear_on_submit=True):
                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    cl_t = st.text_input("🏢 Agencia Aduanal / Cliente")
                    orig_t = st.text_input("📍 Origen (ej. Patio Reynosa)", value="Reynosa, TAM")
                    op_t = st.selectbox("👤 Operador Asignado", lista_ops) if lista_ops else st.text_input("👤 Operador")
                    tipo_mov = st.selectbox("📦 Estado de la Caja", ["Cargado", "Vacío (Empty)"])
                with c_d2:
                    pedimento = st.text_input("📄 Número de Pedimento / Folio")
                    dest_t = st.text_input("🏁 Destino (ej. Bodega McAllen)", value="McAllen, TX")
                    uni_t = st.selectbox("🚛 Camión Corto (Transfer)", lista_unis) if lista_unis else st.text_input("🚛 Unidad")
                    tipo_op = st.selectbox("🌐 Régimen", ["Exportación", "Importación"])
                    
                tarifa_t = st.number_input("💰 Tarifa Pactada ($)", min_value=0.0, step=100.0)
                
                if st.form_submit_button("🚀 Autorizar e Iniciar Cruce Fronterizo", use_container_width=True):
                    if cl_t and pedimento:
                        ahora_local = datetime.now(LOCAL_TZ).isoformat()
                        supabase.table("viajes").insert({
                            "id_cliente": cl_t.strip(), "origen": orig_t.strip(), "destino": dest_t.strip(),
                            "operador_manual": op_t, "unidad_manual": str(uni_t), "tarifa": tarifa_t,
                            "numero_pedimento": pedimento.strip(), "tipo_movimiento": tipo_mov,
                            "tipo_operacion": tipo_op, "estatus": "En Tránsito", "hora_despacho": ahora_local
                        }).execute()
                        st.success(f"✅ Flete autorizado. Pedimento {pedimento} enviado al teléfono del operador.")
                        st.rerun()
                    else:
                        st.error("El número de pedimento y el cliente son obligatorios para la aduana.")

        with tab_analitica:
            st.subheader("📋 Dashboard Semanal de Cruces y Rendimientos")
            st.write("Estadísticas consolidadas basadas en marcas de tiempo automatizadas.")
            try:
                res_all = supabase.table("viajes").select("*").execute()
                if res_all.data:
                    df_all = pd.DataFrame(res_all.data)
                    df_fin = df_all[df_all["estatus"] == "Finalizado"].copy()
                    
                    if not df_fin.empty:
                        col_m1, col_m2 = st.columns(2)
                        col_m1.metric("📊 Total Cruces Concluidos", len(df_fin))
                        
                        # Simulación de volumen operativo
                        tipo_semana = "🔥 SEMANA ALTA" if len(df_fin) >= 5 else "🧊 SEMANA BAJA"
                        col_m2.metric("📈 Evaluación de Demanda", tipo_semana)
                        
                        st.write("### Historial de Rendimientos Recientes")
                        df_vista_analitica = df_fin[["id", "id_cliente", "numero_pedimento", "tipo_movimiento", "rendimiento_calculado"]].rename(columns={
                            "id": "ID", "id_cliente": "Cliente", "numero_pedimento": "Pedimento", "tipo_movimiento": "Caja", "rendimiento_calculado": "Rendimiento (km/L)"
                        })
                        st.dataframe(df_vista_analitica, use_container_width=True, hide_index=True)
                    else:
                        st.info("Aún no hay transfers finalizados este ciclo para promediar.")
            except Exception as e:
                st.error(f"Error analítico: {e}")

    # =========================================================================
    # 📱 2. EXPERIENCIA DEL CHOFER / OPERADOR (Botonera Gigante Móvil)
    # =========================================================================
    elif st.session_state.rol == "chofer":
        st.title("📱 Panel del Operador")
        st.write("Presiona el botón correspondiente a tu estado actual en el puente internacional.")
        
        try:
            # Buscar el viaje asignado a este operador que esté en tránsito
            res_c = supabase.table("viajes").select("*").eq("operador_manual", st.session_state.usuario).neq("estatus", "Finalizado").order("id", desc=True).limit(1).execute()
            
            if res_c.data:
                viaje_actual = res_c.data[0]
                st.info(f"📋 **Viaje Activo ID #{viaje_actual['id']}**\n\n**Cliente:** {viaje_actual['id_cliente']} | **Pedimento:** {viaje_actual['numero_pedimento']}\n\n**Estatus Actual:** `{viaje_actual['estatus']}`")
                
                # --- BOTONERA DE UN SOLO CLIC (CHECKPOINTS) ---
                st.write("---")
                
                if st.button("🚛 1. Salí de Patio / En Fila de Puente", use_container_width=True, type="secondary"):
                    supabase.table("viajes").update({"estatus": "En Fila del Puente", "motivo_demora": "Ninguna"}).eq("id", viaje_actual["id"]).execute()
                    st.success("Estatus actualizado: En Fila del Puente")
                    st.rerun()
                    
                if st.button("🛂 2. Entré a Módulo de Aduana", use_container_width=True, type="secondary"):
                    supabase.table("viajes").update({"estatus": "Módulo de Aduana", "motivo_demora": "Ninguna"}).eq("id", viaje_actual["id"]).execute()
                    st.success("Estatus actualizado: Módulo de Aduana")
                    st.rerun()

                if st.button("🔎 3. Me mandaron a Inspección / Gamma", use_container_width=True, type="secondary"):
                    supabase.table("viajes").update({"estatus": "En Inspección"}).eq("id", viaje_actual["id"]).execute()
                    st.warning("Estatus actualizado: En Inspección / Rayos Gamma")
                    st.rerun()

                # --- ESCUDO REWARD HACKING: JUSTIFICACIÓN DE DEMORAS ---
                st.write("---")
                st.markdown("##### ⚠️ ¿El puente no avanza? Reporta Demora Externa")
                
                col_b1, col_b2 = st.columns(2)
                if col_b1.button("🛑 Fila Parada / Tráfico", use_container_width=True):
                    supabase.table("viajes").update({"estatus": "Retrasado por Tráfico", "motivo_demora": "Fila Pesada en Puente"}).eq("id", viaje_actual["id"]).execute()
                    st.error("Demora por Tráfico Reportada.")
                    st.rerun()
                if col_b2.button("💻 Caída de Sistema", use_container_width=True):
                    supabase.table("viajes").update({"estatus": "Retrasado por Tráfico", "motivo_demora": "Caída de Sistema en Aduana"}).eq("id", viaje_actual["id"]).execute()
                    st.error("Demora por Sistema Reportada.")
                    st.rerun()

                # --- CIERRE DE VIAJE Y LIQUIDACIÓN ---
                st.write("---")
                with st.expander("🏁 Concluir Cruce (Llegué a Bodega USA)"):
                    litros = st.number_input("Litros de diésel cargados en el circuito", min_value=0.0, step=5.0, value=0.0)
                    km_concluidos = st.number_input("Odómetro / Kilómetros Finales", min_value=0.0, step=10.0, value=100.0)
                    
                    if st.button("💾 Finalizar Cruce y Enviar Telemetría", use_container_width=True, type="primary"):
                        ahora_fin = datetime.now(LOCAL_TZ).isoformat()
                        
                        # Cálculo matemático de respaldo para el rendimiento
                        distancia = km_concluidos - float(viaje_actual.get("km_iniciales", 0))
                        rendimiento_final = (distancia / litros) if litros > 0 and distancia > 0 else 2.5
                        
                        supabase.table("viajes").update({
                            "estatus": "Finalizado",
                            "km_finales": km_concluidos,
                            "litros_combustible": litros,
                            "rendimiento_calculado": rendimiento_final,
                            "hora_finalizacion": ahora_fin
                        }).eq("id", viaje_actual["id"]).execute()
                        
                        st.success("🏁 ¡Cruce finalizado! Información de telemetría resguardada con éxito.")
                        st.rerun()
            else:
                st.success("🎉 No tienes transfers asignados por el momento. Espera instrucciones de Despacho.")
        except Exception as e:
            st.error(f"Falla de sincronización local temporal: {e}")

    # =========================================================================
    # 🏢 3. EXPERIENCIA DEL CLIENTE (Portal de Visibilidad Express)
    # =========================================================================
    elif st.session_state.rol == "cliente":
        st.title("🤝 Portal de Clientes - Seguimiento Aduanal")
        st.write(f"Monitoreo de transfers asignados a: **{st.session_state.usuario.upper()}**")
        
        try:
            res_cl = supabase.table("viajes").select("*").order("id", desc=True).execute()
            if res_cl.data:
                df_c = pd.DataFrame(res_cl.data)
                # Filtrado por cliente
                df_filtrado = df_c[df_c["id_cliente"].astype(str).str.strip().str.lower() == st.session_state.usuario.strip().lower()]
                
                if not df_filtrado.empty:
                    for _, flete in df_filtrado.iterrows():
                        estatus = flete["estatus"]
                        
                        # Suavizado estético para el cliente (No le mostramos alertas de estrés interno)
                        if estatus in ["En Tránsito", "En Fila del Puente"]:
                            linea_tiempo = "🟢 [Despachado] ➡️ 🟡 [En Fila de Puente] ➡️ ⚪ [Módulo] ➡️ ⚪ [Entregado]"
                        elif estatus == "Módulo de Aduana":
                            linea_tiempo = "🟢 [Despachado] ➡️ 🟢 [En Fila de Puente] ➡️ 🟡 [Módulo Recinto Fiscal] ➡️ ⚪ [Entregado]"
                        elif estatus == "En Inspección":
                            linea_tiempo = "🟢 [Despachado] ➡️ 🟢 [En Fila de Puente] ➡️ 🔴 [Inspección / Rayos Gamma] ➡️ ⚪ [Entregado]"
                        elif estatus == "Retrasado por Tráfico":
                            linea_tiempo = "🟢 [Despachado] ➡️ ⏳ [Demora por Tráfico Externo en Puente] ➡️ ⚪ [Módulo] ➡️ ⚪ [Entregado]"
                        else:
                            linea_tiempo = "🟢 [Despachado] ➡️ 🟢 [En Fila de Puente] ➡️ 🟢 [Módulo] ➡️ 🎉 [CRUZADO / ENTREGADO]"
                            
                        with st.container(border=True):
                            st.markdown(f"### 📄 Pedimento / Folio: **{flete['numero_pedimento']}**")
                            st.write(f"**Destino:** {flete['destino']} | **Caja:** {flete['tipo_movimiento']}")
                            st.markdown(f"**Avance de la Carga:**")
                            st.markdown(f"#### {linea_tiempo}")
                            st.caption(f"Estatus reportado: *{estatus}*")
                else:
                    st.info("📭 Actualmente no hay cruces en tránsito asignados a tu cuenta.")
            else:
                st.info("📭 No hay registros en el sistema.")
        except Exception as e:
            st.error(f"Error al consultar estatus: {e}")
