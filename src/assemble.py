import json
import os
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

# Стандартный размер для Reels / Shorts / TikTok (9:16)
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920

def load_scenario(json_filepath):
    with open(json_filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_audio(text, output_audio_path):
    tts = gTTS(text=text, lang='ru', slow=False)
    tts.save(output_audio_path)
    return output_audio_path

def resize_and_crop_to_vertical(clip, target_w=TARGET_WIDTH, target_h=TARGET_HEIGHT):
    """Принудительно подгоняет любое видео под формат 9:16 (1080x1920) без черных полей."""
    scale = max(target_w / clip.w, target_h / clip.h)
    new_w, new_h = int(clip.w * scale), int(clip.h * scale)
    
    resized = clip.resized((new_w, new_h))
    cropped = resized.cropped(
        x_center=new_w / 2, 
        y_center=new_h / 2, 
        width=target_w, 
        height=target_h
    )
    return cropped

def assemble_reels(scenario_path="data/scenario.json", output_path="final_reels.mp4"):
    """
    Главная функция сборки Reels для бота и консоли.
    Возвращает путь к итоговым видео или None при ошибке.
    """
    if not os.path.exists(scenario_path):
        print(f"Файл {scenario_path} не найден.")
        return None

    scenario = load_scenario(scenario_path)
    clips_dir = "clips"
    processed_clips = []
    created_audio_files = []

    # Собираем список всех доступных клипов
    available_clips = []
    if os.path.exists(clips_dir):
        available_clips = [
            os.path.join(clips_dir, f) for f in os.listdir(clips_dir) 
            if f.endswith(('.mp4', '.mov'))
        ]

    if not available_clips:
        print(" Ошибка: Папка clips/ пуста или видео не найдены.")
        return None

    print("Начинаем сборку видео...")

    for idx, scene in enumerate(scenario.get("scenes", [])):
        scene_num = scene.get("scene_number", idx + 1)
        voice_text = scene.get("voiceover_text", "")
        screen_text = scene.get("screen_text", "")

        print(f"Обработка сцены {scene_num}...")

        # 1. Генерация озвучки
        audio_file = f"temp_audio_{scene_num}.mp3"
        generate_audio(voice_text, audio_file)
        created_audio_files.append(audio_file)
        
        audio_clip = AudioFileClip(audio_file)
        duration = audio_clip.duration

        # 2. Поиск видео по номеру или взятие по кругу из доступных
        specific_video = os.path.join(clips_dir, f"clip_{scene_num}.mp4")
        if os.path.exists(specific_video):
            video_file = specific_video
        else:
            video_file = available_clips[idx % len(available_clips)]
            print(f"Файл clip_{scene_num}.mp4 не найден. Используем {video_file}")

        video_clip = VideoFileClip(video_file)

        # 3. Приведение видео к 9:16 (1080x1920) без черных полей
        video_clip = resize_and_crop_to_vertical(video_clip)

        # 4. Подгонка длительности под речь
        if video_clip.duration < duration:
            video_clip = video_clip.with_duration(duration)
        else:
            video_clip = video_clip.subclipped(0, duration)

        video_clip = video_clip.with_audio(audio_clip)

        # 5. Наложение текста
        if screen_text:
            try:
                txt_clip = TextClip(
                    text=screen_text,
                    font_size=48,
                    color='white',
                    method='caption',
                    size=(int(TARGET_WIDTH * 0.85), None)
                ).with_duration(duration).with_position(('center', 'center'))

                scene_final = CompositeVideoClip([video_clip, txt_clip])
            except Exception as e:
                print(f"Ошибка при наложении текста: {e}")
                scene_final = video_clip
        else:
            scene_final = video_clip

        processed_clips.append(scene_final)

    if not processed_clips:
        print("Ошибка: Не удалось обработать ни одну сцену.")
        return None

    # 6. Экспорт и рендер роликов
    print("Склеиваем сцены в итоговый 9:16 ролик...")
    final_video = concatenate_videoclips(processed_clips, method="compose")
    final_video.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
    
    # 7. Автоматическая очистка временных аудиофайлов
    for a_file in created_audio_files:
        if os.path.exists(a_file):
            try:
                os.remove(a_file)
            except Exception:
                pass

    print(f"УСПЕХ! Итоговый файл сохранен в {output_path}")
    return output_path

if __name__ == "__main__":
    assemble_reels()