from flask import Flask, request, send_file
import os
from google.cloud import speech
from fpdf import FPDF
from dotenv import load_dotenv
import uvicorn

app = Flask(__name__)

load_dotenv()

# Configurez votre clé d'API Google Cloud
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    # Vérifiez si un fichier a été envoyé
    if 'audio' not in request.files:
        return {"error": "Aucun fichier audio fourni."}, 400

    audio_file = request.files['audio']
    audio_path = f"temp_{audio_file.filename}"
    audio_file.save(audio_path)

    try:
        # Initialisez le client Google Speech-to-Text
        client = speech.SpeechClient()

        # Chargez le fichier audio
        with open(audio_path, "rb") as audio:
            audio_content = audio.read()

        audio_config = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="fr-FR"
        )

        # Transcription
        response = client.recognize(config=config, audio=audio_config)
        transcription = "\n".join([result.alternatives[0].transcript for result in response.results])

        # Génération du PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, transcription)

        pdf_path = f"transcription_{audio_file.filename}.pdf"
        pdf.output(pdf_path)

        # Retourner le PDF
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        # Nettoyez les fichiers temporaires
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Railway définit dynamiquement le port
    uvicorn.run(app, host="", port=port)