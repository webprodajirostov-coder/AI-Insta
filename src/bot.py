import os
import asyncio
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

from transcribe import download_and_transcribe
from analyzer import analyze_competitor_text
from get_scenario import generate_scenario_from_idea
from assemble import assemble_reels

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = os.getenv("TELEGRAM_USER_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class BotStates(StatesGroup):
    waiting_for_idea = State()
    waiting_for_urls = State()

def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" Анализ конкурентов (Ссылки)", callback_data="mode_urls")],
        [InlineKeyboardButton(text=" Создать сценарий из идеи", callback_data="mode_idea")],
        [InlineKeyboardButton(text=" Смонтировать Reels (MP4)", callback_data="mode_assemble")]
    ])

def is_authorized(user_id: int) -> bool:
    return str(user_id) == str(ALLOWED_USER_ID)

async def safe_callback_answer(callback: types.CallbackQuery):
    """Безопасный ответ на callback во избежание таймаутов Telegram."""
    try:
        await callback.answer()
    except Exception:
        pass

# --- КОМАНДЫ И МЕНЮ ---

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    if not is_authorized(message.from_user.id):
        await message.answer("Доступ ограничен.")
        return
    await state.clear()
    await message.answer("Привет! Выбери действие в меню:", reply_markup=main_keyboard())

@dp.callback_query(F.data == "mode_urls")
async def set_urls_mode(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_urls)
    await callback.message.answer("Пришли одну или несколько ссылок на Reels/Shorts:")
    await safe_callback_answer(callback)

@dp.callback_query(F.data == "mode_idea")
async def set_idea_mode(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_idea)
    await callback.message.answer("Вставь идею/концепт из чата-стратега (или JSON):")
    await safe_callback_answer(callback)

# --- МОНТАЖ ВИДЕО ---

@dp.callback_query(F.data == "mode_assemble")
async def process_assembly(callback: types.CallbackQuery):
    scenario_path = os.path.join("data", "scenario.json")
    if not os.path.exists(scenario_path):
        await callback.message.answer("Файл `data/scenario.json` не найден! Сначала сгенерируйте сценарий из идеи.")
        await safe_callback_answer(callback)
        return

    status_msg = await callback.message.answer(" Запущена сборка ролика (озвучка + нарезка + субтитры)... Это займет ~30-60 сек.")
    await safe_callback_answer(callback)

    output_video = await asyncio.to_thread(assemble_reels)

    if output_video and os.path.exists(output_video):
        await status_msg.edit_text(" Монтаж завершен! Отправляю видео...")
        video_file = FSInputFile(output_video)
        await callback.message.answer_video(video_file, caption="Ваш готовый Reels!")
    else:
        await status_msg.edit_text(" Ошибка при монтаже видео. Проверьте логи в консоли.")

# --- ОБРАБОТКА ИДЕИ -> СЦЕНАРИЙ ---

@dp.message(BotStates.waiting_for_idea)
async def handle_idea(message: types.Message, state: FSMContext):
    if not is_authorized(message.from_user.id): 
        return
    
    idea_text = message.text.strip()
    if not idea_text:
        await message.answer("Пожалуйста, отправьте текстовую идею.")
        return

    os.makedirs("data", exist_ok=True)
    with open(os.path.join("data", "ideas.json"), "w", encoding="utf-8") as f:
        json.dump({"raw_idea": idea_text}, f, ensure_ascii=False, indent=2)

    status_msg = await message.answer("⏳ Генерирую сценарий...")
    scenario = await asyncio.to_thread(generate_scenario_from_idea, idea_text)

    if scenario:
        await status_msg.edit_text(
            f" **Сценарий готов и сохранен!**\n\n"
            f"**Заголовок:** {scenario.get('title', 'Без названия')}\n"
            f"**Кадров:** {len(scenario.get('scenes', []))}\n\n"
            f"Теперь выберите в меню **'Смонтировать Reels'**.",
            reply_markup=main_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await status_msg.edit_text(" Не удалось сгенерировать сценарий. Проверьте консоль.")
    
    await state.clear()

# --- ОБРАБОТКА ССЫЛОК -> РАЗБОР ---

@dp.message(BotStates.waiting_for_urls)
async def handle_urls(message: types.Message, state: FSMContext):
    if not is_authorized(message.from_user.id): 
        return
    
    urls = [item for item in message.text.split() if item.startswith("http")]
    if not urls:
        await message.answer("Ссылки не найдены. Отправьте ссылки через пробел.")
        return

    status_msg = await message.answer(f"⏳ Принято ссылок: {len(urls)}. Начинаем обработку...")

    summary_path = os.path.join("data", "analyses", "latest_batch_summary.json")
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    
    batch_data = []

    for idx, url in enumerate(urls, 1):
        try:
            await status_msg.edit_text(f" Обработка [{idx}/{len(urls)}]: Скачивание и Whisper...")
            transcription = await asyncio.to_thread(download_and_transcribe, url)
            
            if not transcription:
                continue

            await status_msg.edit_text(f" Обработка [{idx}/{len(urls)}]: Англоязычный анализ смыслов...")
            analysis = await asyncio.to_thread(analyze_competitor_text, transcription, idx)

            batch_data.append({
                "video_id": idx,
                "url": url,
                "transcription_en": transcription,
                "analysis_en": analysis
            })

        except Exception as e:
            print(f"Ошибка на ролик {idx}: {e}")

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(batch_data, f, ensure_ascii=False, indent=2)

    await status_msg.delete()

    if batch_data:
        summary_file = FSInputFile(summary_path)
        await message.answer_document(
            document=summary_file,
            caption=(
                f" **Обработка завершена!**\n\n"
                f" Успешно обработано: `{len(batch_data)}` из `{len(urls)}` ссылок.\n"
                f" Все смыслы и транскрипции сохранены на **английском языке** в прикрепленном `.json` файле."
            ),
            parse_mode="Markdown"
        )
    else:
        await message.answer("Не удалось обработать отправленные ссылки.")

    await state.clear()
    await message.answer("Выберите следующее действие:", reply_markup=main_keyboard())

# --- ЗАПУСК БОТА ---

async def main():
    print("ТГ-Бот успешно запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())