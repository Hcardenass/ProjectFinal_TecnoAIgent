#!pip install google-cloud-storage
#pip install --upgrade --quiet  twilio
#pip install gspread oauth2client

from langchain_community.utilities.twilio import TwilioAPIWrapper
import os
import uuid
from datetime import datetime
from typing import Optional
from google.cloud import storage
from langchain.tools import tool

from dotenv import load_dotenv
load_dotenv()

def make_tool_audio_whatsapp(
    client_openai,
    twilio_from_number='whatsapp:+1',
    bucket_name="gc-"
):
    """
    Genera un audio desde texto, lo sube a GCS y lo envía por WhatsApp usando Twilio.
    """
    # ---- 1. Speech ----
    def generate_speech_from_text(text: str, file_name: Optional[str] = None, folder_path: str = "audios", voice: str = "nova") -> str:
        os.makedirs(folder_path, exist_ok=True)
        if file_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_name = f"speech_{timestamp}_{unique_id}.mp3"
        output_path = os.path.join(folder_path, file_name)
        response = client_openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        with open(output_path, "wb") as f:
            f.write(response.content)
        return output_path

    # ---- 2. Google Cloud Storage ----
    def upload_mp3_to_gcs(local_file_path: str, bucket_name: str, destination_blob_name: Optional[str] = None) -> str:
        """
        Sube un archivo .mp3 a un bucket de Google Cloud Storage en la carpeta 'audios/' y lo hace público.
        Retorna la URL pública del archivo.
        """
        try:
            if not os.path.exists(local_file_path):
                raise FileNotFoundError(f"El archivo '{local_file_path}' no existe.")
            if destination_blob_name is None:
                destination_blob_name = f"audios/{os.path.basename(local_file_path)}"
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(local_file_path)
            blob.make_public()
            print(f"Archivo subido y hecho público: {blob.public_url}")
            return blob.public_url
        except Exception as e:
            print(f"[ERROR al subir a GCS]: {e}")
            raise

    # ---- 3. Twilio WhatsApp ----

    # Configura Twilio
    twilio = TwilioAPIWrapper(
        account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
        from_number="whatsapp:+14",  # Este es el número de sandbox de WhatsApp (generalmente)
    )

    @tool
    def send_audio_message_to_whatsapp(to_number: str, audio_url: str) -> str:
        """
        Envía un mensaje de audio (voz) a WhatsApp usando Twilio y una URL pública (audio_url debe ser .mp3 o .ogg).
        """
        from twilio.rest import Client
        # Normaliza el número de destino
        print(to_number)
        client = Client(twilio.account_sid, twilio.auth_token)
        message = client.messages.create(
            body="🎧 Aquí tienes tu audio generado:",
            from_=twilio.from_number,
            to=f"whatsapp:+{to_number}",
            media_url=[audio_url]
        )
        return f"✅ Mensaje enviado a {to_number}. SID: {message.sid}"


    @tool
    def generar_y_enviar_audio(texto: str, numero_destino: str) -> str:
        """
        Genera un audio desde texto, lo sube a GCS y lo envía por WhatsApp usando Twilio.
        """
        local_path = generate_speech_from_text(texto)
        public_url = upload_mp3_to_gcs(local_path, bucket_name)
        # Direct call, NOT .invoke, porque ahora es función normal
        resultado_envio = send_audio_message_to_whatsapp.invoke({
            "to_number": numero_destino,
            "audio_url": public_url
        })
        return f"{resultado_envio}\n🔗 URL del audio: {public_url}"

    return [generar_y_enviar_audio]
