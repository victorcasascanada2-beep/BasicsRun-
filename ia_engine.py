#HE subido la temperatura a tope a ver como flipa
import streamlit as st
from google import genai
from google.oauth2 import service_account
from PIL import Image
import io
import time
import config_prompt

def conectar_vertex(creds_dict):
    raw_key = str(creds_dict.get("private_key", ""))
    clean_key = raw_key.strip().strip('"').strip("'").replace("\\n", "\n")
    creds_dict["private_key"] = clean_key
    google_creds = service_account.Credentials.from_service_account_info(
        creds_dict, 
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return genai.Client(vertexai=True, project=creds_dict.get("project_id"), 
                        location="us-central1", credentials=google_creds)

def realizar_peritaje(client, marca, modelo, anio, horas, observaciones, lista_fotos):
    # --- 1. OPTIMIZACIÓN DE FOTOS ---
    fotos_ia = []
    for foto in lista_fotos:
        img = Image.open(foto).convert("RGB")
        img.thumbnail((800, 800)) 
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75) 
        buf.seek(0)
        fotos_ia.append(Image.open(buf))

    # --- 2. BÚSQUEDA SECUENCIAL POR ETAPAS ---
    portales = ["Agriaffaires", "Tractorpool", "Truck1", "E-farm"]
    memoria_busqueda = ""
    
    # Contenedor visual para el progreso de etapas
    status_container = st.empty()
    
    for i, portal in enumerate(portales):
        with status_container:
            st.info(f"🔍 Etapa {i+1}/4: Escaneando {portal}...")
        
        prompt_etapa = config_prompt.obtener_prompt_etapa(portal, marca, modelo, anio, horas)
        
        try:
            # Llamada de búsqueda individual
            res_etapa = client.models.generate_content(
                model="gemini-2.5-pro", 
                contents=[prompt_etapa],
                config={"tools": [{"google_search": {}}], "temperature": 0.2}
            )
            memoria_busqueda += f"\n--- HALLAZGOS EN {portal} ---\n{res_etapa.text}\n"
            
            # Espera para no agobiar y simular proceso humano
            time.sleep(2) 
        except Exception as e:
            memoria_busqueda += f"\n⚠️ Error en {portal}: {str(e)}\n"

    status_container.success("✅ Escaneo de portales finalizado. Generando informe...")

    # --- 3. SÍNTESIS FINAL ---
    prompt_final = config_prompt.obtener_prompt_sintesis_final(
        marca, modelo, memoria_busqueda, observaciones
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro", 
            contents=[prompt_final] + fotos_ia,
            config={
                "temperature": 0.1,
                "max_output_tokens": 8192
            }
        )
        return response.text
    except Exception as e:
        return f"Error en la síntesis final: {str(e)}"
