# config_prompt.py

def obtener_prompt_etapa(portal, marca, modelo, anio, horas):
    """Prompt específico para buscar en un solo portal."""
    return f"""
    Busca únicamente en el portal {portal} anuncios actuales de: {marca} {modelo}.
    Céntrate en unidades del año {anio} con aproximadamente {horas} horas.
    
    TAREAS:
    1. Encuentra al menos 3-5 resultados reales en {portal}.
    2. Extrae: Precio, Año, Horas y Ubicación.
    3. Si no encuentras el modelo exacto, busca el más cercano (ej. misma serie).
    
    Responde de forma esquemática solo con los datos encontrados en {portal}.
    """

def obtener_prompt_sintesis_final(marca, modelo, datos_acumulados, observaciones):
    """Prompt para que la IA una todos los hallazgos y analice las fotos."""
    return f"""
    Actúa como experto tasador de Agrícola Noroeste. 
    Tienes ante ti los datos recolectados de 4 portales líderes sobre el {marca} {modelo}.
    
    DATOS RECOLECTADOS:
    {datos_acumulados}
    
    TAREAS FINALES:
    1. Analiza el estado visual a través de las fotos adjuntas (máximo 30 palabras por foto).
    2. Genera una TABLA COMPARATIVA unificada con lo mejor de los 4 portales.
    3. Calcula basándote en los datos:
       - Precio Venta sugerido (Aterrizaje).
       - Precio Compra recomendado para Agrícola Noroeste.
    
    Notas adicionales del perito: {observaciones}
    
    Usa un tono profesional, negritas y tablas Markdown.
    """
