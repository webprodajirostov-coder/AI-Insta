import os
import subprocess
from faster_whisper import WhisperModel

# Переменная для кэширования модели в памяти
_whisper_model = None

def get_whisper_model():
    """Загружает модель Faster-Whisper только при первом вызове."""
    global _whisper_model
    if _whisper_model is None:
        print("Загрузка модели Faster-Whisper в память...")
        _whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
    return _whisper_model

def download_and_transcribe(url):
    temp_audio = "temp_competitor.mp3"
    if os.path.exists(temp_audio):
        try:
            os.remove(temp_audio)
        except Exception:
            pass
        
    print(f"Скачиваем аудио по ссылке: {url}...")
    cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", temp_audio, "--no-playlist", url]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Ошибка скачивания: {result.stderr}")
        return None

    print("Распознаем речь через faster-whisper...")
    # Получаем модель без задержек при запуске всего скрипта
    model = get_whisper_model()
    
    # Автоопределение языка (убрали жесткий language="ru" для корректной работы с английским)
    segments, info = model.transcribe(temp_audio)
    text = " ".join([segment.text for segment in segments]).strip()
    
    if os.path.exists(temp_audio):
        try:
            os.remove(temp_audio)
        except Exception:
            pass
        
    return text