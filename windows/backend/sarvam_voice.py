"""
Sarvam AI Voice Pipeline for Track 1 - G2 (Voice-First AI Interaction).
Integrates:
- Saaras v4 (`saaras:v4`) Speech-to-Text with codemix / translate modes and domain keyterm prompting
- Bulbul v4 Flash (`bulbul:v4-flash`) Text-to-Speech for low-latency natural voice responses
"""
import base64
import os
import requests
from typing import Dict, Any, Optional


class SarvamVoicePipeline:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SARVAM_API_KEY", "")
        self.base_url = "https://api.sarvam.ai"

    def transcribe_speech(
        self,
        audio_bytes: bytes,
        filename: str = "command.wav",
        mode: str = "codemix",
        language_code: str = "en-IN",
        keyterms: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Calls Sarvam AI /speech-to-text using `saaras:v4`.
        Supports `transcribe`, `codemix` (Hinglish/Kanglish), and `translate`.
        """
        if not self.api_key:
            return {
                "transcript": "",
                "error": "SARVAM_API_KEY is not configured. WebSpeech API active fallback.",
                "model": "client_fallback",
                "mode": mode,
            }

        headers = {"api-subscription-key": self.api_key}
        files = {"file": (filename, audio_bytes, "audio/wav")}
        data: Dict[str, Any] = {
            "model": "saaras:v4",
            "mode": mode,
            "language_code": language_code,
        }
        if keyterms:
            data["prompt"] = ", ".join(keyterms)

        resp = requests.post(
            f"{self.base_url}/speech-to-text",
            headers=headers,
            files=files,
            data=data,
            timeout=20,
        )
        resp.raise_for_status()
        payload = resp.json()
        return {
            "transcript": payload.get("transcript", ""),
            "language_code": payload.get("language_code", language_code),
            "model": "saaras:v4",
            "mode": mode,
        }

    def synthesize_speech(
        self,
        text: str,
        language_code: str = "en-IN",
        speaker: str = "shubh_enhi_ads",
        pace: float = 1.08,
        sample_rate: int = 24000,
    ) -> Dict[str, Any]:
        """
        Calls Sarvam AI /text-to-speech using `bulbul:v4-flash` for low-latency J.A.R.V.I.S. responses.
        """
        if not self.api_key:
            return {
                "audio_base64": "",
                "error": "SARVAM_API_KEY is not configured. Browser SpeechSynthesis active fallback.",
                "model": "client_fallback"
            }

        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        body = {
            "inputs": [text[:2500]],
            "target_language_code": language_code,
            "speaker": speaker,
            "pace": pace,
            "speech_sample_rate": sample_rate,
            "enable_preprocessing": True,
            "model": "bulbul:v4-flash",
        }
        resp = requests.post(
            f"{self.base_url}/text-to-speech",
            headers=headers,
            json=body,
            timeout=20,
        )
        resp.raise_for_status()
        payload = resp.json()
        audios = payload.get("audios", [])
        return {
            "audio_base64": audios[0] if audios else "",
            "model": "bulbul:v4-flash",
            "speaker": speaker,
            "sample_rate": sample_rate,
        }
