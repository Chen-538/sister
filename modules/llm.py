"""LLM 呼叫模組 - 使用 OpenAI GPT-4o"""

import json
from pathlib import Path
from openai import OpenAI

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _call_gpt(api_key: str, system: str, user: str) -> str:
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content


def structure_transcript(transcript: str, api_key: str) -> dict:
    """將逐字稿整理為結構化 JSON。"""
    prompt = _load_prompt("structuring.txt")
    filled = prompt.replace("{transcript}", transcript)
    result = _call_gpt(api_key, "你是幼兒園教學紀錄助手，請回傳 JSON。", filled)
    return json.loads(result)


def generate_newsletter(structured_data: dict, api_key: str) -> dict:
    """根據結構化資料生成班刊內容。"""
    prompt = _load_prompt("newsletter.txt")
    filled = prompt.replace("{structured_data}", json.dumps(structured_data, ensure_ascii=False, indent=2))
    result = _call_gpt(api_key, "你是幼兒園班刊撰寫助手，請回傳 JSON。", filled)
    return json.loads(result)


def generate_weekly_log(structured_data: dict, api_key: str) -> dict:
    """根據結構化資料生成週誌內容。"""
    prompt = _load_prompt("weekly_log.txt")
    filled = prompt.replace("{structured_data}", json.dumps(structured_data, ensure_ascii=False, indent=2))
    result = _call_gpt(api_key, "你是幼兒園教學週誌撰寫助手，請回傳 JSON。", filled)
    return json.loads(result)
