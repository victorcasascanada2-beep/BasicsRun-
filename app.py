import streamlit as st
from PIL import Image
from streamlit_js_eval import get_geolocation
import ia_engine
import html_generator
import google_drive_manager
import location_manager
import os
import datetime

# -------------------------------------------------
# 1. CONFIGURACIÓN
# -------------------------------------------------
st.set_page_config(page_title="Tasador Agrícola", page_icon="🚜", layout="centered")

# -------------------------------------------------
# 2. CONTROL DE ACCESO
# -------------------------------------------------
def login():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.title("🔐 Acceso Tasador")
        user_id = st.text_input("ID John Deere")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Entrar", use_container_width=True):
            if "usuarios" in st.secrets and user_id in st.secrets["usuarios"]:
                if password == st.secrets["usuarios"][user_id]:
                    st.session_state.autenticado = True
                    st.session_state.vendedor_id = user_id
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")
            else:
                st.error("❌ ID de usuario no autorizado")
        return False
    return True

# -------------------------------------------------
# EJECUCIÓN DE LA APP
# -------------------------------------------------
if login():
    # 3. CSS "MODO APP NATIVA" (Ajustado para subir el form)
    st.markdown("""
    <style>
        header[data-testid="stHeader"] { display: none !important; }
        [data-testid="stToolbar"] { display: none !important; }
        footer { display: none !important; }
        .block-container { 
            margin-top: -5rem !important; /* Subimos el contenido al máximo */
            padding-top: 0.5rem !important;
            padding-bottom: 2rem !important;
        }
        [data-testid="stImage"] { display: flex; justify-content: center; }
        button[kind="secondaryFormSubmit"] {
            border: 2px solid #2e7d32 !important;
            color: #2e7d32 !important;
            font-weight: bold !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 4. UBICACIÓN
    loc = get_geolocation(component_key="gps_tasacion_final")
    texto_ubicacion = "PENDIENTE"

    if loc and isinstance(loc, dict) and 'coords' in loc:
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        texto_ubicacion = location_manager.codificar_coordenadas(lat, lon)

    # 5. CONEXIÓN GOOGLE (VERTEX AI)
    if "vertex_client" not in st.session_state:
        try:
            creds = dict(st.secrets["google"])
            if "private_key" in creds:
                creds["private_key"] = creds["private_key"].replace("\\n", "\n")
            st.session_state.vertex_client = ia_engine.conectar_vertex(creds)
        except Exception as e:
            st.error(f"Error credenciales Google: {e}")

    # 6. INTERFAZ
    if os.path.exists("agricolanoroestelogo.jpg"):
        st.image("agricolanoroestelogo.jpg", width=250)
    
    st.caption(f"Sesión activa: {st.session_state.vendedor_id}")

    # 7. RESULTADOS (Se muestran primero si existen)
    if "informe_final" in st.session_state:
        if "drive_status" in st.session_state:
            st.success(st.session_state.drive_status)

        st.markdown(st.session_state.informe_final)
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "📥 DESCARGAR", 
                data=st.session_state.html, 
                file_name=f"Tasacion_{st.session_state.vendedor_id}_{st.session_state.marca}.html",
                mime="text/html",
                use_container_width=True
            )
        with c2:
            if st.button("🔄 NUEVA", use_container_width=True):
                keys_to_keep = ["autenticado", "vendedor_id", "vertex_client"]
                for key in list(st.session_state.keys()):
                    if key not in keys_to_keep:
                        del st.session_state[key]
                st.rerun()

    # 8. FORMULARIO (Uso de placeholder para limpieza visual)
    placeholder = st.empty()

    if "informe_final" not in st.session_state:
        with placeholder.container():
            with st.form("form_tasacion"):
                st.title("Tasación Experta")
                fotos = st.file_uploader("📸 Sube las imágenes", accept_multiple_files=True, type=['jpg','png'])
                
                c1, c2 = st.columns(2)
                with c1:
                    marca = st.text_input("Marca", value="John Deere")
                modelo = st.text_input("Modelo", value="6175M")
                with c2:
                    anio = st.text_input("Año", value="2015")
                    horas = st.text_input("Horas", value="9800")
                
                obs = st.text_area("Extras y Observaciones", value="Ruedas al 80%, Soportes de pala...")
                
                submit = st.form_submit_button("🚀 TASAR AHORA", use_container_width=True)

        if submit:
            if marca and modelo and fotos:
                # Al pulsar, borramos el form y mostramos el progreso arriba
                placeholder.empty() 
                
                with st.spinner("🤖 Analizando tractor... Esto tardará unos segundos."):
                    try:
                        # IA
                        notas_ia = f"Vendedor: {st.session_state.vendedor_id}\n{obs}\n\n[ID: {texto_ubicacion}]"
                        inf = ia_engine.realizar_peritaje(st.session_state.vertex_client, marca, modelo, int(anio), int(horas), notas_ia, fotos)
                        
                        # Guardado inmediato
                        st.session_state.informe_final = inf
                        st.session_state.marca = marca
                        st.session_state.modelo = modelo
                        
                        # Generación de HTML
                        fotos_pil = [Image.open(f) for f in fotos]
                        st.session_state.html = html_generator.generar_informe_html(marca, modelo, inf, fotos_pil, texto_ubicacion)

                        # Drive
                        try:
                            ahora = datetime.datetime.now().strftime("%d%H%M")
                            creds_drive = dict(st.secrets["google"])
                            if "private_key" in creds_drive:
                                creds_drive["private_key"] = creds_drive["private_key"].replace("\\n", "\n")
                            
                            google_drive_manager.subir_informe(creds_drive, f"{marca}_{modelo}_{ahora}.html", st.session_state.html, folder_name=st.session_state.vendedor_id)
                            st.session_state.drive_status = f"✅ Guardado en carpeta: {st.session_state.vendedor_id}"
                        except:
                            st.session_state.drive_status = "⚠️ Tasación lista, pero no se pudo subir a Drive."
                        
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error en el proceso: {e}")
            else:
                st.warning("⚠️ Rellena todos los campos y sube fotos.")
