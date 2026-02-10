import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account

# Tu carpeta raíz donde se organizará todo
ID_CARPETA_RAIZ = "0AEU0RHjR-mDOUk9PVA" 
SCOPES = ["https://www.googleapis.com/auth/drive"]

def subir_informe(creds_dict, nombre_archivo, contenido_html, folder_name="General"):
    try:
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        # 1. BUSCAR SI YA EXISTE LA CARPETA DEL VENDEDOR DENTRO DE LA RAÍZ
        query = (f"name = '{folder_name}' and "
                 f"'{ID_CARPETA_RAIZ}' in parents and "
                 f"mimeType = 'application/vnd.google-apps.folder' and "
                 f"trashed = false")
        
        response = service.files().list(q=query, spaces='drive', supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        folders = response.get('files', [])

        if not folders:
            # Si no existe, creamos la subcarpeta del vendedor
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [ID_CARPETA_RAIZ]
            }
            folder = service.files().create(
                body=folder_metadata, 
                fields='id',
                supportsAllDrives=True
            ).execute()
            folder_id = folder.get('id')
        else:
            # Si ya existe, tomamos su ID
            folder_id = folders[0].get('id')

        # 2. PREPARAR EL CONTENIDO
        if isinstance(contenido_html, str):
            datos_a_subir = contenido_html.encode('utf-8')
        else:
            datos_a_subir = contenido_html 

        # 3. SUBIR EL ARCHIVO A LA CARPETA DEL VENDEDOR
        file_metadata = {
            'name': nombre_archivo,
            'parents': [folder_id],
            'mimeType': 'text/html'
        }
        
        fh = io.BytesIO(datos_a_subir)
        media = MediaIoBaseUpload(fh, mimetype='text/html', resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True 
        ).execute()

        return file.get('id')

    except Exception as e:
        print(f"Error crítico en Drive: {str(e)}")
        return None
