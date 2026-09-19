import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

ODIROUTER_API_KEY = os.getenv("ODIROUTER_API_KEY")
ODIROUTER_URL = "[https://api.odirouter.ai/v1/chat/completions](https://api.odirouter.ai/v1/chat/completions)"

SYSTEM_ANALYSIS_PROMPT = """
You are an expert short-form video strategist creating high-converting Reels/Shorts for an English-speaking audience in psychology.
Analyze the transcription of a competitor's vertical video and deconstruct it directly in ENGLISH.

Return ONLY a raw JSON object (no markdown, no ```json formatting):
{
  "deconstruction": {
    "viral_hook_trigger": "What psychological trigger makes the first 3 seconds hook the audience?",
    "core_meaning": "Core underlying narrative/idea of the original video"
  },
  "adapted_concept": {
    "our_angle": "Our unique psychological twist on this concept for English-speaking viewers",
    "target_emotion": "Primary emotion to evoke"
  }
}
"""

def analyze_competitor_text(transcription_text, index=1):
    print(f"Deconstructing video #{index} via OdiRouter...")
    
    headers = {
        "Authorization": f"Bearer {ODIROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    models_to_try = [
        "free-gemini-3.1-flash-lite",
        "free-gpt-5.4-mini",
        "gemini-2.5-flash"
    ]

    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_ANALYSIS_PROMPT},
                {"role": "user", "content": f"Competitor Transcription:\n{transcription_text}"}
            ],
            "temperature": 0.7
        }

        try:
            response = requests.post(ODIROUTER_URL, headers=headers, json=payload, timeout=90)
            
            if response.status_code == 200:
                data = response.json()
                raw_text = data['choices'][0]['message']['content']
                raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                
                analysis_data = json.loads(raw_text)
                
                os.makedirs("data/analyses", exist_ok=True)
                filepath = os.path.join("data/analyses", f"analysis_video_{index}.json")
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(analysis_data, f, ensure_ascii=False, indent=2)
                    
                print(f" Разбор #{index} успешно завершен через: {model_name}")
                return analysis_data
            else:
                print(f" Модель {model_name} вернула {response.status_code}: {response.text}")

        except Exception as e:
            print(f" Ошибка сети/таймаут для {model_name}: {e}")

    return {
        "deconstruction": {"viral_hook_trigger": "Error", "core_meaning": "Error"},
        "adapted_concept": {"our_angle": "Error", "target_emotion": "Error"}
    }