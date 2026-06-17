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
        
        tab1, tab2, tab3 = st.tabs(["📊 Monitoreo y Utilidades", "📝 Operación de Fletes", "⚙️ Control de Flota"])
        supabase = obtener_cliente()

        # ---------------------------------------------------------
        # PESTAÑA 1: MAESTRA DE MONITOREO Y RENTABILIDAD EN VIVO (SINCRONIZACIÓN REAL-TIME)
        # ---------------------------------------------------------
        with tab1:
            st.subheader("📊 Monitoreo General")
            st.write("Estado operativo de los fletes activos en el sistema.")
            
            try:
                res_v = supabase.table("viajes").select("id", "id_cliente", "origen", "destino", "tarifa", "operador_manual", "unidad_manual", "estatus").order("id", desc=True).execute()
                res_g = supabase.table("gastos").select("id", "id_viaje", "tipo_gasto", "monto", "descripcion").order("id", desc=True).execute()
                
                if res_v.data:
                    df_v = pd.DataFrame(res_v.data)
                    df_g = pd.DataFrame(res_g.data) if res_g.data else pd.DataFrame(columns=["id", "id_viaje", "tipo_gasto", "monto", "descripcion"])
                    
                    df_v["tarifa"] = df_v["tarifa"].astype(float)
                    
                    # --- PREPARACIÓN DE LA MATRIZ DE GASTOS EN MEMORIA ---
                    if not df_g.empty:
                        df_pivot = df_g.pivot_table(index='id_viaje', columns='tipo_gasto', values='monto', aggfunc='sum').reset_index().fillna(0.0)
                    else:
                        df_pivot = pd.DataFrame(columns=['id_viaje'])
                        
                    for col_concepto in ['Diésel', 'Casetas', 'Maniobras', 'Sueldo Operador', 'Taller', 'Otros']:
                        if col_concepto not in df_pivot.columns:
                            df_pivot[col_concepto] = 0.0
                            
                    df_pivot = df_pivot[['id_viaje', 'Diésel', 'Casetas', 'Maniobras', 'Sueldo Operador', 'Taller', 'Otros']]
                    df_pivot['id_viaje'] = df_pivot['id_viaje'].astype(int)
                    
                    # --- VISTA OPERATIVA ESCENCIAL AL ENTRAR (DISCRETA) ---
                    df_publico = df_v[["id", "id_cliente", "origen", "destino", "operador_manual", "unidad_manual", "estatus"]].rename(columns={
                        "id": "ID Viaje", "id_cliente": "🏢 Cliente", "origen": "📍 Origen", "destino": "🏁 Destino",
                        "operador_manual": "👤 Chofer", "unidad_manual": "🚛 Unidad", "estatus": "🟢 Estatus"
                    })
                    st.dataframe(df_publico, use_container_width=True, hide_index=True)
                    
                    # --- CAJA FUERTE EXPANDIBLE FINANCIERA ---
                    st.write("")
                    with st.expander("🔓 Acceder a Balance Financiero y Corrección de Datos"):
                        st.subheader("💰 Auditoría de Cuentas en Ruta")
                        st.write("Modifica los montos de los fletes o desglosa los gastos abajo. Las tablas se recalculan en caliente.")
                        
                        st.divider()
                        st.write("🔍 **1. Desglose de Gastos por Categoría (Modificación Real-Time)**")
                        
                        cambios_matriz_gastos = st.data_editor(
                            df_pivot,
                            key="editor_matriz_gastos_vivos",
                            use_container_width=True,
                            hide_index=True,
                            disabled=["id_viaje"],
                            column_config={
                                "id_viaje": "ID Viaje",
                                "Diésel": st.column_config.NumberColumn("⛽ Diésel", format="$%.2f"),
                                "Casetas": st.column_config.NumberColumn("🛣️ Casetas", format="$%.2f"),
                                "Maniobras": st.column_config.NumberColumn("🏗️ Maniobras", format="$%.2f"),
                                "Sueldo Operador": st.column_config.NumberColumn("👤 Sueldo", format="$%.2f"),
                                "Taller": st.column_config.NumberColumn("🔧 Taller", format="$%.2f"),
                                "Otros": st.column_config.NumberColumn("📦 Otros", format="$%.2f")
                            }
                        )
                        
                        # --- CÁLCULO EN CALIENTE DE TOTALES ---
                        df_gastos_calculados = cambios_matriz_gastos.copy()
                        df_gastos_calculados["Gastos Totales"] = df_gastos_calculados[['Diésel', 'Casetas', 'Maniobras', 'Sueldo Operador', 'Taller', 'Otros']].sum(axis=1)
                        
                        df_merged_live = pd.merge(df_v, df_gastos_calculados[["id_viaje", "Gastos Totales"]], left_on="id", right_on="id_viaje", how="left")
                        df_merged_live["Gastos Totales"] = df_merged_live["Gastos Totales"].fillna(0.0)
                        df_merged_live["Utilidad Neta"] = df_merged_live["tarifa"] - df_merged_live["Gastos Totales"]
                        
                        st.divider()
                        st.write("📈 **2. Resumen de Rentabilidad y Datos Base del Flete**")
                        
                        df_viajes_edicion = df_merged_live[["id", "id_cliente", "origen", "destino", "tarifa", "Gastos Totales", "Utilidad Neta"]]
                        
                        cambios_viajes = st.data_editor(
                            df_viajes_edicion,
                            key="editor_viajes_live_recalc",
                            use_container_width=True,
                            hide_index=True,
                            disabled=["id", "Gastos Totales", "Utilidad Neta"],
                            column_config={
                                "id": "ID Viaje", "id_cliente": "🏢 Cliente", "origen": "📍 Origen", "destino": "🏁 Destino",
                                "tarifa": st.column_config.NumberColumn("💰 Tarifa", format="$%,.2f"),
                                "Gastos Totales": st.column_config.NumberColumn("🛑 Total Gastos", format="$%,.2f"),
                                "Utilidad Neta": st.column_config.NumberColumn("💵 Utilidad Neta", format="$%,.2f")
                            }
                        )
                        
                        if st.button("💾 Guardar Toda la Información en la Base de Datos", use_container_width=True):
                            # A. Guardar Viajes
                            for i, fila in cambios_viajes.iterrows():
                                original = df_viajes_edicion.iloc[i]
                                if not fila.equals(original):
                                    supabase.table("viajes").update({
                                        "id_cliente": fila["id_cliente"], "origen": fila["origen"],
                                        "destino": fila["destino"], "tarifa": float(fila["tarifa"])
                                    }).eq("id", int(fila["id"])).execute()
                                    
                            # B. Guardar Gastos Matrix
                            for i, fila in cambios_matriz_gastos.iterrows():
                                id_v_act = int(fila["id_viaje"])
                                conceptos_actualizar = {
                                    "Diésel": float(fila["Diésel"]), "Casetas": float(fila["Casetas"]),
                                    "Maniobras": float(fila["Maniobras"]), "Sueldo Operador": float(fila["Sueldo Operador"]),
                                    "Taller": float(fila["Taller"]), "Otros": float(fila["Otros"])
                                }
                                for tipo_c, monto_c in conceptos_actualizar.items():
                                    registro_existente = df_g[(df_g['id_viaje'] == id_v_act) & (df_g['tipo_gasto'] == tipo_c)]
                                    if not registro_existente.empty
