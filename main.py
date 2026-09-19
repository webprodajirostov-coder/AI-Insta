import sys
import os
import json
import subprocess
from datetime import datetime
from src.transcribe import download_and_transcribe
from src.analyzer import analyze_competitor_text


def run_batch_analysis():
    print("\n--- ПАКЕТНЫЙ АНАЛИЗ КОНКУРЕНТОВ ---")
    print("Вставьте ссылки на Reels/Shorts (по одной на строке или через пробел).")
    print("Когда закончите ввод, нажмите Enter дважды:")
    
    lines = []
    while True:
        line = input()
        if not line.strip():
            break
        lines.append(line.strip())
        
    urls = []
    for line in lines:
        for item in line.split():
            if item.startswith("http"):
                urls.append(item)
                
    if not urls:
        print("Ссылки не найдены.")
        return
        
    print(f"\n Найдено ссылок для обработки: {len(urls)}")
    
    # 1. Загружаем уже существующий итоговый JSON, если он есть
    summary_dir = os.path.join("data", "analyses")
    os.makedirs(summary_dir, exist_ok=True)
    summary_path = os.path.join(summary_dir, "latest_batch_summary.json")
    
    existing_data = []
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = []
            print(f" Найдена существующая база: в ней уже {len(existing_data)} разобранных роликов.")
        except Exception as e:
            print(f" Не удалось прочитать старый summary-файл, создаем новый список: {e}")
            existing_data = []

    # 2. Обрабатываем новые ссылки
    new_results_count = 0
    for idx, url in enumerate(urls, 1):
        print(f"\n========================================")
        print(f"Обработка [{idx}/{len(urls)}]: {url}")
        print(f"========================================")
        
        text = download_and_transcribe(url)
        if text:
            print(f"\nРасшифровка получена ({len(text)} символов).")
            analysis = analyze_competitor_text(text, index=idx)
            if analysis:
                # Добавляем новую запись в общий массив
                existing_data.append({
                    "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "url": url,
                    "transcription": text,
                    "analysis": analysis
                })
                new_results_count += 1
        else:
            print(f"Пропуск ролика из-за ошибки скачивания/транскрибации.")

    # 3. Перезаписываем итоговый файл уже ПОПОЛНЕННЫМ массивом
    if new_results_count > 0:
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n ПАКЕТНАЯ ОБРАБОТКА ЗАВЕРШЕНА!")
        print(f"Добавлено новых роликов: {new_results_count}")
        print(f"Всего роликов в базе `latest_batch_summary.json`: {len(existing_data)}")
        print(f"Файл обновлен: {summary_path}")

def run_bot():
    print("\nЗапуск Telegram-бота...")
    subprocess.run(["python", "src/bot.py"])
    
def main():
    while True:
        print("\n=== AI REELS ENGINE ===")
        print("1. Разобрать пачку Reels (через консоль)")
        print("2. Запустить Telegram-бота")
        print("3. Выход")
        
        choice = input("Выберите действие (1-3): ").strip()
        
        if choice == "1":
            from src.analyzer import run_batch_analysis # или вызов функции пакетного анализа
            pass
        elif choice == "2":
            run_bot()
        elif choice == "3":
            break

if __name__ == "__main__":
    main()