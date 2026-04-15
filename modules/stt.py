"""語音轉文字模組 - 使用 OpenAI Whisper API"""

from openai import OpenAI


def transcribe(audio_bytes: bytes, api_key: str, filename: str = "audio.wav") -> str:
    """將音檔位元組轉為逐字稿文字。"""
    client = OpenAI(api_key=api_key)
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=(filename, audio_bytes),
        language="zh",
        response_format="text",
    )
    return response.strip()
