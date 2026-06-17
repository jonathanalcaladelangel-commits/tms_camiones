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
        # PESTAÑA 1: MAESTRA DE MONITOREO Y RENTABILIDAD EN VIVO
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
                    
                    # --- VISTA OPERATIVA ESENCIAL AL ENTRAR (DISCRETA) ---
                    df_publico = df_v[["id", "id_cliente", "origen", "destino", "operador_manual", "unidad_manual", "estatus"]].rename(columns={
                        "id": "ID Viaje", "id_cliente": "🏢 Cliente", "origen": "📍 Origen", "destino": "🏁 Destino",
                        "operador_manual": "👤 Chofer", "unidad_manual": "🚛 Unidad", "estatus": "🟢 Estatus"
                    })
