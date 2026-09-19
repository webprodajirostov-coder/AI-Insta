import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

ODIROUTER_API_KEY = os.getenv("ODIROUTER_API_KEY")
ODIROUTER_URL = "https://api.odirouter.ai/v1/chat/completions"

SYSTEM_SCENARIO_PROMPT = """
You are a lead video strategist for short-form video (Reels/Shorts) in sales psychology and personal transformation for an English audience.
Turn the user's concept into a scene-by-scene script.

Return ONLY a raw JSON object (no markdown, no ```json formatting):
{
  "content_type": "engagement",
  "title": "Short catchy title in English",
  "viral_hook_reason": "Why the first 3 seconds pull the viewer in",
  "scenes": [
    {
      "scene_number": 1,
      "duration_seconds": 4,
      "voiceover_text": "Voiceover script text in English for TTS",
      "visual_prompt_en": "Cinematic vertical 9:16 background video prompt",
      "screen_text": "Short screen caption (max 4 words)"
    }
  ]
}
"""

def generate_scenario_from_idea(idea_text):
    print("Generating English scene-by-scene script via OdiRouter...")
    
    headers = {
        "Authorization": f"Bearer {ODIROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # Актуальные варианты названий для роутера
    models_to_try = [
        "free-gemini-3.1-flash-lite",
        "free-gpt-5.4-mini",
        "gemini-2.5-flash"
    ]

    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_SCENARIO_PROMPT},
                {"role": "user", "content": f"Idea/Concept:\n{idea_text}"}
            ],
            "temperature": 0.7
        }

        try:
            # Увеличен timeout до 90 секунд для исключения Read timed out
            response = requests.post(ODIROUTER_URL, headers=headers, json=payload, timeout=90)
            
            if response.status_code == 200:
                data = response.json()
                raw_text = data['choices'][0]['message']['content']
                raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                
                scenario_data = json.loads(raw_text)
                
                os.makedirs("data", exist_ok=True)
                scenario_path = os.path.join("data", "scenario.json")
                with open(scenario_path, "w", encoding="utf-8") as f:
                    json.dump(scenario_data, f, ensure_ascii=False, indent=2)
                    
                print(f" Сценарий успешно сгенерирован через: {model_name}")
                return scenario_data
            else:
                print(f" Модель {model_name} вернула {response.status_code}: {response.text}")

        except Exception as e:
            print(f" Ошибка сети/таймаут для {model_name}: {e}")

    return None