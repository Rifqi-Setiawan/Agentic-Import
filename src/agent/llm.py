"""The only network adapter allowed to invoke the configured 9Router model."""
import time
from typing import Any

import httpx

from src.core.config import settings


class LLMInvocationError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, raw_response=None):
        super().__init__(message)
        self.status_code = status_code
        self.raw_response = raw_response


class TokenBudgetManager:
    def __init__(self, max_run_tokens=60000, current_run_tokens=0):
        self.max_run_tokens = max_run_tokens
        self.current_run_tokens = current_run_tokens

    def can_proceed(self, estimated_tokens=0):
        return self.current_run_tokens + estimated_tokens <= self.max_run_tokens

    def record_usage(self, prompt_tokens: int, completion_tokens: int):
        self.current_run_tokens += prompt_tokens + completion_tokens

    def get_stop_reason(self):
        return "QUOTA_EXCEEDED" if self.current_run_tokens > self.max_run_tokens else None


def get_llm_client() -> httpx.Client:
    headers = {"Content-Type": "application/json"}
    if settings.LLM_GATEWAY_KEY:
        headers["Authorization"] = f"Bearer {settings.LLM_GATEWAY_KEY}"
    return httpx.Client(base_url=settings.LLM_GATEWAY_URL.rstrip("/") + "/", headers=headers,
                        timeout=httpx.Timeout(60, connect=10))


def call_llm(messages: list[dict], model: str | None = None, stream=False, temperature=None, **kwargs: Any):
    if stream:
        raise ValueError("The structured model adapter requires stream=False.")
    if not (model or settings.LLM_MODEL):
        raise LLMInvocationError("LLM_MODEL belum dikonfigurasi.")
    payload = {"model": model or settings.LLM_MODEL, "messages": messages,
               "temperature": settings.LLM_TEMPERATURE if temperature is None else temperature,
               "max_tokens": 4000, **kwargs, "stream": False}
    primary = payload["model"]
    fallback = settings.LLM_MODEL_FALLBACK
    for attempt in range(3):
        try:
            with get_llm_client() as client:
                response = client.post("chat/completions", json=payload)
                response.raise_for_status()
                body = response.json()
            choices = body.get("choices") or []
            if not choices:
                raise LLMInvocationError("9Router tidak mengembalikan pilihan jawaban.")
            message = choices[0].get("message", {})
            if not message.get("content") and not message.get("tool_calls"):
                raise LLMInvocationError("9Router mengembalikan jawaban kosong.")
            usage = body.get("usage") or {}
            return {"content": message.get("content") or "", "message": message,
                    "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"), "model": body.get("model", payload["model"]),
                    "raw": body, "attempts": attempt + 1, "used_fallback": payload["model"] != primary}
        except httpx.HTTPStatusError as error:
            status = error.response.status_code
            if status not in (429, 500, 502, 503, 504) or attempt == 2:
                raise LLMInvocationError(f"9Router gagal (HTTP {status}). Coba ulang setelah layanan pulih.", status) from error
            if status == 429 and fallback and fallback != payload["model"]:
                payload["model"] = fallback
                continue
        except (httpx.RequestError, ValueError) as error:
            if attempt == 2:
                raise LLMInvocationError("Koneksi atau format respons 9Router gagal setelah percobaan ulang.") from error
        except LLMInvocationError:
            if attempt == 2:
                raise
        if attempt == 1 and fallback:
            payload["model"] = fallback
        if attempt < 2:
            time.sleep(2 ** attempt)
    raise LLMInvocationError("9Router belum tersedia.")


def invoke_llm(messages, model=None, stream=False, **kwargs):
    return call_llm(messages, model=model, stream=stream, **kwargs)
