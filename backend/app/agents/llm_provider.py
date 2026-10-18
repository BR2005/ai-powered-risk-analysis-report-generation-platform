import json
import logging
from typing import Any
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

class LLMProvider:
    """Dedicated LLM Provider configured for Google DeepMind's Gemma 4 model family."""

    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self.gemma_model = settings.gemma_model

    async def generate_completion(self, system_prompt: str, user_prompt: str) -> str | None:
        """
        Invokes Gemma 4 model via configured endpoint (Google AI Studio, Ollama, or OpenAI-compatible server).
        Safely falls back to deterministic analysis if the model server is offline or keys are absent.
        """
        # 1. Gemma 4 via Google AI Studio API
        if self.provider in ("gemma-4", "gemma", "google-ai-studio"):
            api_key = settings.gemma_api_key
            if api_key:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemma_model}:generateContent?key={api_key}"
                    payload = {
                        "contents": [
                            {
                                "role": "user",
                                "parts": [{"text": f"{system_prompt}\n\nTask: {user_prompt}"}]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.2,
                            "maxOutputTokens": 2048,
                        }
                    }
                    timeout = httpx.Timeout(20.0, connect=2.5)
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                text_parts = candidates[0].get("content", {}).get("parts", [])
                                if text_parts:
                                    return text_parts[0].get("text", "").strip()
                        else:
                            logger.warning(f"Gemma 4 API responded with status {resp.status_code}: {resp.text}")
                except Exception as e:
                    logger.warning(f"Gemma 4 API request error: {e}. Using deterministic engine.")

            # If Ollama is running Gemma 4 locally as secondary check
            return await self._call_ollama(system_prompt, user_prompt)

        # 2. Gemma 4 via Local Ollama
        if self.provider == "ollama":
            return await self._call_ollama(system_prompt, user_prompt)

        # 3. Gemma 4 via OpenAI-compatible endpoint (vLLM, LM Studio, OpenRouter)
        if self.provider == "openai-compatible" and settings.openai_api_key:
            try:
                url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": settings.openai_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.2
                }
                timeout = httpx.Timeout(20.0, connect=2.5)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.warning(f"OpenAI endpoint request for Gemma 4 failed: {e}.")

        return None

    async def _call_ollama(self, system_prompt: str, user_prompt: str) -> str | None:
        """Calls local Ollama daemon hosting Gemma 4."""
        try:
            url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
            payload = {
                "model": settings.ollama_model, # e.g. "gemma-4"
                "prompt": f"{system_prompt}\n\nTask: {user_prompt}",
                "stream": False,
            }
            timeout = httpx.Timeout(20.0, connect=1.5)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
        except Exception as e:
            logger.debug(f"Ollama local Gemma 4 check: {e}")
        return None

llm_provider = LLMProvider()
