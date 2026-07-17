"""
LLM client abstraction.
Supports multiple providers. Configure via environment variables.
"""

from __future__ import annotations
import os
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class LLMClient:
    """
    Thin multi-provider client.
    Set one of:
      OPENAI_API_KEY
      ANTHROPIC_API_KEY
      XAI_API_KEY (Grok)
    """

    def __init__(self, provider: str = "auto", model: Optional[str] = None):
        self.provider = provider
        self.model = model
        self._detect_provider()

    def _detect_provider(self):
        if self.provider != "auto":
            return
        if os.getenv("ANTHROPIC_API_KEY"):
            self.provider = "anthropic"
            self.model = self.model or "claude-sonnet-4-20250514"
        elif os.getenv("XAI_API_KEY"):
            self.provider = "xai"
            self.model = self.model or "grok-4"
        elif os.getenv("OPENAI_API_KEY"):
            self.provider = "openai"
            self.model = self.model or "gpt-4.1"
        else:
            self.provider = "mock"
            self.model = "mock"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def chat(
        self,
        system: str,
        user: str,
        images: Optional[List[str]] = None,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ) -> str:
        if self.provider == "mock":
            return self._mock_response(system, user)

        if self.provider == "anthropic":
            return self._anthropic(system, user, images, temperature, max_tokens)
        if self.provider == "openai":
            return self._openai(system, user, images, temperature, max_tokens)
        if self.provider == "xai":
            return self._xai(system, user, images, temperature, max_tokens)

        raise ValueError(f"Unsupported provider: {self.provider}")

    def _anthropic(self, system, user, images, temperature, max_tokens) -> str:
        import anthropic
        client = anthropic.Anthropic()
        content = [{"type": "text", "text": user}]
        message = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": content}],
        )
        return message.content[0].text

    def _openai(self, system, user, images, temperature, max_tokens) -> str:
        from openai import OpenAI
        client = OpenAI()
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content

    def _xai(self, system, user, images, temperature, max_tokens) -> str:
        api_key = os.getenv("XAI_API_KEY")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        with httpx.Client(timeout=120) as client:
            r = client.post("https://api.x.ai/v1/chat/completions", headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    def _mock_response(self, system: str, user: str) -> str:
        return json.dumps({
            "status": "mock",
            "message": "LLM not configured. Set ANTHROPIC_API_KEY, OPENAI_API_KEY or XAI_API_KEY.",
            "system_preview": system[:200],
            "user_preview": user[:300],
        }, indent=2)


def load_prompt(name: str) -> str:
    """Load a prompt markdown file from the prompts/ directory."""
    prompt_path = Path(__file__).parent.parent / "prompts" / f"{name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")
