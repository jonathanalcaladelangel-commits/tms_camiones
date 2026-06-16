# =========================================================
    # VISTA PARA EL CLIENTE (CORREGIDA Y COMPROBADA)
    # =========================================================
    elif st.session_state.rol == "cliente":
        st.title("Portal de Clientes")
        st.subheader("📦 Estado de mis Embarques")
        st.write(f"Bienvenido. Consultando las cargas asignadas a: **{st.session_state.usuario}**")
        
        try:
            supabase = obtener_cliente()
            
            # 1. Traemos todos los viajes para el cliente actual
            respuesta = supabase.table("viajes").select("*").order("id", desc=True).execute()
            
            if respuesta.data and len(respuesta.data) > 0:
                df_completo = pd.DataFrame(respuesta.data)
                
                # Identificamos qué columna de cliente existe en la base de datos para no adivinar
                col_filtro = "id_cliente" if "id_cliente" in df_completo.columns else "cliente"
                
                # 2. Filtramos en Pandas para asegurar que la estructura no rompa el Schema Cache
                df_cliente = df_completo[df_completo[col_filtro].astype(str).str.strip() == st.session_state.usuario.strip()]
                
                if not df_cliente.empty:
                    # Renombramos solo las columnas de interés para el cliente
                    df_cliente = df_cliente.rename(columns={
                        "origen": "📍 Origen",
                        "destino": "🏁 Destino",
                        "unidad_manual": "🚛 Unidad asignada",
                        "estatus": "🟢 Estatus de Entrega"
                    })
                    
                    columnas_cliente = ["📍 Origen", "🏁 Destino", "🚛 Unidad asignada", "🟢 Estatus de Entrega"]
                    # Mostramos solo las columnas que existan
                    cols_finales = [c for c in columnas_cliente if c in df_cliente.columns]
                    
                    st.dataframe(df_cliente[cols_finales], use_container_width=True, hide_index=True)
                else:
                    st.info("📭 Actualmente no tienes ningún embarque en tránsito con nosotros.")
            else:
                st.info("📭 Actualmente no tienes ningún embarque en tránsito con nosotros.")
                
        except Exception as e:
            st.error(f"❌ Error al consultar tus datos: {e}")
